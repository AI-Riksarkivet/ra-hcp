"""S3Ops — presigned-first, multipart for large files."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

import httpx

if TYPE_CHECKING:
    from rahcp_client.client import HCPClient

log = logging.getLogger(__name__)


class S3Ops:
    """S3 data-plane operations — presigned-first, multipart for large files.

    All data transfer prefers presigned URLs. Files above
    ``client.multipart_threshold`` automatically use multipart upload.

    Path mapping to the backend API (all under /api/v1):
        GET  /buckets                              — list buckets
        GET  /buckets/{b}/objects                  — list objects
        POST /presign                              — single presigned URL
        POST /buckets/{b}/objects/presign          — bulk presigned URLs
        POST /buckets/{b}/multipart/{key}          — initiate multipart
        POST /buckets/{b}/multipart/{key}/presign  — presign parts
        POST /buckets/{b}/multipart/{key}/complete — complete multipart
        DELETE /buckets/{b}/objects/{key}           — delete object
        POST /buckets/{b}/objects/delete            — bulk delete
        POST /buckets/{b}/objects/{key}/copy       — copy object
        HEAD /buckets/{b}/objects/{key}             — head object
    """

    def __init__(self, client: HCPClient) -> None:
        self._client = client

    def _http(self) -> httpx.AsyncClient:
        """Create an httpx client for presigned URL operations."""
        return httpx.AsyncClient(verify=self._client.verify_ssl)

    # ── Presigned URL operations (preferred path) ───────────────────

    async def presign_get(self, bucket: str, key: str, *, expires: int = 3600) -> str:
        """Get a presigned download URL."""
        resp = await self._client.request(
            "POST",
            "/presign",
            json={
                "bucket": bucket,
                "key": key,
                "method": "get_object",
                "expires_in": expires,
            },
        )
        return resp.json()["url"]

    async def presign_put(self, bucket: str, key: str, *, expires: int = 3600) -> str:
        """Get a presigned upload URL."""
        resp = await self._client.request(
            "POST",
            "/presign",
            json={
                "bucket": bucket,
                "key": key,
                "method": "put_object",
                "expires_in": expires,
            },
        )
        return resp.json()["url"]

    async def presign_bulk(
        self,
        bucket: str,
        keys: list[str],
        *,
        expires: int = 3600,
    ) -> list[dict[str, Any]]:
        """Get presigned download URLs for multiple keys."""
        resp = await self._client.request(
            "POST",
            f"/buckets/{bucket}/objects/presign",
            json={
                "keys": keys,
                "expires_in": expires,
            },
        )
        return resp.json()["urls"]

    # ── Convenience wrappers (use presigned internally) ─────────────

    async def upload(self, bucket: str, key: str, data: bytes | Path) -> str:
        """Upload data — auto-selects presigned PUT or multipart based on size.

        Returns the ETag of the uploaded object.
        """
        if isinstance(data, Path):
            size = await asyncio.to_thread(lambda: data.stat().st_size)
            if size >= self._client.multipart_threshold:
                return await self.upload_multipart(bucket, key, data)
            content = await asyncio.to_thread(data.read_bytes)
        else:
            content = data

        url = await self.presign_put(bucket, key)
        async with self._http() as http:
            resp = await http.put(url, content=content)
            resp.raise_for_status()
        return resp.headers.get("etag", "")

    async def download(self, bucket: str, key: str, dest: Path) -> int:
        """Download an object via presigned GET. Returns byte count."""
        url = await self.presign_get(bucket, key)
        async with self._http() as http:
            async with http.stream("GET", url) as resp:
                resp.raise_for_status()
                total = 0
                f = await asyncio.to_thread(dest.open, "wb")
                try:
                    async for chunk in resp.aiter_bytes(chunk_size=8192):
                        await asyncio.to_thread(f.write, chunk)
                        total += len(chunk)
                finally:
                    await asyncio.to_thread(f.close)
        return total

    async def download_bytes(self, bucket: str, key: str) -> bytes:
        """Download an object as bytes via presigned GET."""
        url = await self.presign_get(bucket, key)
        async with self._http() as http:
            resp = await http.get(url)
            resp.raise_for_status()
        return resp.content

    # ── Multipart (presigned, parallel) ─────────────────────────────

    async def upload_multipart(
        self,
        bucket: str,
        key: str,
        path: Path,
        *,
        concurrency: int = 6,
    ) -> str:
        """Presigned multipart upload for large files.

        1. Initiate multipart → upload_id
        2. Presign each part
        3. Upload parts in parallel (bounded semaphore)
        4. Complete multipart (or abort on failure)
        """
        file_size = await asyncio.to_thread(lambda: path.stat().st_size)
        chunk = self._client.multipart_chunk

        # Initiate
        resp = await self._client.request(
            "POST",
            f"/buckets/{bucket}/multipart/{key}",
        )
        upload_id = resp.json()["upload_id"]

        try:
            # Presign all parts
            resp = await self._client.request(
                "POST",
                f"/buckets/{bucket}/multipart/{key}/presign",
                json={
                    "upload_id": upload_id,
                    "file_size": file_size,
                    "part_size": chunk,
                },
            )
            data = resp.json()
            part_urls = [p["url"] for p in data["urls"]]
            part_size = data.get("part_size", chunk)

            # Upload parts in parallel — each returns its part info
            sem = asyncio.Semaphore(concurrency)

            async def _upload_part(part_num: int, url: str) -> dict[str, Any]:
                offset = part_num * part_size
                read_size = min(part_size, file_size - offset)

                def _read_chunk() -> bytes:
                    with path.open("rb") as f:
                        f.seek(offset)
                        return f.read(read_size)

                part_data = await asyncio.to_thread(_read_chunk)
                async with sem:
                    async with self._http() as http:
                        r = await http.put(url, content=part_data)
                        r.raise_for_status()
                        return {"part_number": part_num + 1, "etag": r.headers["etag"]}

            parts = await asyncio.gather(
                *[_upload_part(i, url) for i, url in enumerate(part_urls)]
            )

            # Complete
            parts_sorted = sorted(parts, key=lambda p: p["part_number"])
            resp = await self._client.request(
                "POST",
                f"/buckets/{bucket}/multipart/{key}/complete",
                json={
                    "upload_id": upload_id,
                    "parts": [
                        {"ETag": p["etag"], "PartNumber": p["part_number"]}
                        for p in parts_sorted
                    ],
                },
            )
            log.info(
                "Multipart upload complete: %s/%s (%d parts)",
                bucket,
                key,
                len(parts_sorted),
            )
            return resp.json().get("etag", "")

        except Exception:
            # Abort the multipart upload to avoid dangling uploads
            log.warning("Multipart upload failed, aborting: %s/%s", bucket, key)
            try:
                await self._client.request(
                    "POST",
                    f"/buckets/{bucket}/multipart/{key}/abort",
                    json={"upload_id": upload_id},
                )
            except Exception:
                log.warning("Failed to abort multipart upload: %s", upload_id)
            raise

    # ── Bulk operations ─────────────────────────────────────────────

    async def list_buckets(self) -> dict[str, Any]:
        """List all S3 buckets."""
        resp = await self._client.request("GET", "/buckets")
        return resp.json()

    async def list_objects(
        self,
        bucket: str,
        prefix: str = "",
        *,
        max_keys: int = 1000,
        continuation_token: str | None = None,
        delimiter: str | None = None,
    ) -> dict[str, Any]:
        """List objects in a bucket with optional prefix and pagination.

        Returns the full response with 'objects', 'common_prefixes',
        'is_truncated', 'next_continuation_token', 'key_count'.
        """
        params: dict[str, Any] = {"prefix": prefix, "max_keys": max_keys}
        if continuation_token:
            params["continuation_token"] = continuation_token
        if delimiter:
            params["delimiter"] = delimiter
        resp = await self._client.request(
            "GET",
            f"/buckets/{bucket}/objects",
            params=params,
        )
        return resp.json()

    async def delete(self, bucket: str, key: str) -> None:
        """Delete a single object."""
        await self._client.request("DELETE", f"/buckets/{bucket}/objects/{key}")

    async def delete_bulk(self, bucket: str, keys: list[str]) -> dict[str, Any]:
        """Delete multiple objects."""
        resp = await self._client.request(
            "POST",
            f"/buckets/{bucket}/objects/delete",
            json={"keys": keys},
        )
        return resp.json()

    async def copy(
        self,
        bucket: str,
        key: str,
        source_bucket: str,
        source_key: str,
    ) -> None:
        """Copy an object."""
        await self._client.request(
            "POST",
            f"/buckets/{bucket}/objects/{key}/copy",
            json={
                "source_bucket": source_bucket,
                "source_key": source_key,
            },
        )

    async def head(self, bucket: str, key: str) -> dict[str, Any]:
        """Get object metadata."""
        resp = await self._client.request("HEAD", f"/buckets/{bucket}/objects/{key}")
        return dict(resp.headers)

    # ── Staging pattern ─────────────────────────────────────────────

    async def commit_staging(
        self, bucket: str, staging_prefix: str, dest_prefix: str
    ) -> int:
        """Move objects from staging prefix to destination. Returns count."""
        data = await self.list_objects(bucket, staging_prefix)
        objects = data.get("objects", [])
        count = 0
        for obj in objects:
            src_key = obj["Key"]
            dest_key = src_key.replace(staging_prefix, dest_prefix, 1)
            await self.copy(bucket, dest_key, bucket, src_key)
            await self.delete(bucket, src_key)
            count += 1
        return count

    async def cleanup_staging(self, bucket: str, staging_prefix: str) -> int:
        """Delete all objects under a staging prefix. Paginates. Returns count."""
        total = 0
        token: str | None = None
        while True:
            data = await self.list_objects(
                bucket, staging_prefix, continuation_token=token
            )
            objects = data.get("objects", [])
            if not objects:
                break
            keys = [obj["Key"] for obj in objects]
            await self.delete_bulk(bucket, keys)
            total += len(keys)
            if not data.get("is_truncated"):
                break
            token = data.get("next_continuation_token")
        return total
