"""S3 object CRUD endpoints."""

from __future__ import annotations

import asyncio
import logging
import tempfile
import uuid
import zipfile
from pathlib import Path
from typing import Optional

from botocore.exceptions import BotoCoreError, ClientError
from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from fastapi.responses import FileResponse, StreamingResponse
from starlette.background import BackgroundTask as StarletteBackgroundTask

from app.api.dependencies import get_cache_service, get_s3_service
from app.api.errors import run_s3
from app.schemas.s3 import (
    AclPolicy,
    AclResponse,
    BulkDownloadRequest,
    BulkPresignRequest,
    BulkPresignResponse,
    CopyObjectRequest,
    DeleteObjectsRequest,
    DeleteObjectsResponse,
    HeadObjectResponse,
    ListObjectsResponse,
    ObjectInfo,
    ObjectMutationResponse,
    UploadObjectResponse,
    ZipTaskResponse,
)
from app.schemas.common import StatusResponse
from app.services.cache_service import CacheService
from app.services.storage.adapters.hcp import HcpStorage

logger = logging.getLogger(__name__)

# ── In-memory fallback for ZIP task state (no Redis) ──────────────────
_zip_tasks: dict[str, dict] = {}

ZIP_TEMP_DIR = Path(tempfile.gettempdir()) / "zip_tasks"
ZIP_TEMP_DIR.mkdir(exist_ok=True)
MAX_ZIP_OBJECTS = 50_000
BATCH_SIZE = 20

router = APIRouter(prefix="/buckets/{bucket}/objects", tags=["S3 Objects"])


@router.get("", response_model=ListObjectsResponse)
async def list_objects(
    bucket: str,
    prefix: Optional[str] = Query(None),
    max_keys: int = Query(1000, le=1000),
    continuation_token: Optional[str] = Query(None),
    delimiter: Optional[str] = Query(None),
    s3: HcpStorage = Depends(get_s3_service),
):
    result = await run_s3(
        s3.list_objects,
        f"bucket '{bucket}'",
        bucket,
        prefix,
        max_keys,
        continuation_token,
        delimiter,
    )
    objects = [ObjectInfo.model_validate(o) for o in result.get("Contents", [])]
    common_prefixes = [
        cp["Prefix"] for cp in result.get("CommonPrefixes", []) if "Prefix" in cp
    ]
    return ListObjectsResponse(
        objects=objects,
        common_prefixes=common_prefixes,
        is_truncated=result.get("IsTruncated", False),
        next_continuation_token=result.get("NextContinuationToken"),
        key_count=result.get("KeyCount", 0),
    )


# ── Bulk delete (must be before {key:path} catch-all) ────────────────


@router.post("/delete", response_model=DeleteObjectsResponse)
async def delete_objects(
    bucket: str,
    body: DeleteObjectsRequest,
    s3: HcpStorage = Depends(get_s3_service),
):
    result = await run_s3(s3.delete_objects, f"bucket '{bucket}'", bucket, body.keys)
    return {
        "status": "deleted",
        "deleted": len(body.keys),
        "errors": result.get("Errors", []),
    }


# ── ZIP task helpers ──────────────────────────────────────────────────


async def _get_task_state(task_id: str, cache: CacheService | None) -> dict | None:
    """Read task state from Redis (preferred) or in-memory fallback."""
    if cache and cache.enabled:
        state = await cache.get(f"zip_task:{task_id}")
        if state:
            return state
    return _zip_tasks.get(task_id)


async def _set_task_state(
    task_id: str, state: dict, cache: CacheService | None
) -> None:
    """Write task state to Redis with TTL, or in-memory fallback."""
    if cache and cache.enabled:
        await cache.set(f"zip_task:{task_id}", state, ttl=600)
    _zip_tasks[task_id] = state


async def _list_all_keys(s3: HcpStorage, bucket: str, prefix: str) -> list[str]:
    """List all object keys under a prefix, handling S3 pagination."""
    keys: list[str] = []
    token: str | None = None
    while True:
        result = await asyncio.to_thread(s3.list_objects, bucket, prefix, 1000, token)
        for obj in result.get("Contents", []):
            keys.append(obj["Key"])
            if len(keys) > MAX_ZIP_OBJECTS:
                return keys
        if not result.get("IsTruncated", False):
            break
        token = result.get("NextContinuationToken")
    return keys


async def _build_zip(
    task_id: str,
    s3: HcpStorage,
    bucket: str,
    keys: list[str],
    cache: CacheService | None,
) -> None:
    """Background coroutine: build ZIP on disk in batches."""
    zip_path = ZIP_TEMP_DIR / f"{task_id}.zip"
    state: dict = {
        "status": "processing",
        "total": len(keys),
        "completed": 0,
        "failed": 0,
        "failed_keys": [],
        "path": str(zip_path),
    }
    await _set_task_state(task_id, state, cache)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for batch_start in range(0, len(keys), BATCH_SIZE):
                batch = keys[batch_start : batch_start + BATCH_SIZE]

                async def _fetch(key: str) -> tuple[str, bytes | None]:
                    try:
                        result = await asyncio.to_thread(s3.get_object, bucket, key)
                        return key, result["Body"].read()
                    except (ClientError, BotoCoreError):
                        return key, None

                results = await asyncio.gather(*[_fetch(k) for k in batch])
                for key, data in results:
                    if data is not None:
                        zf.writestr(key, data)
                        state["completed"] += 1
                    else:
                        state["failed"] += 1
                        state["failed_keys"].append(key)

                await _set_task_state(task_id, state, cache)

        state["status"] = "ready"
        await _set_task_state(task_id, state, cache)
    except Exception as exc:
        logger.exception("ZIP task %s failed", task_id)
        state["status"] = "failed"
        state["error"] = str(exc)
        await _set_task_state(task_id, state, cache)


# ── Bulk download (must be before {key:path} catch-all) ──────────────


@router.post("/download", response_model=ZipTaskResponse, status_code=202)
async def start_zip_download(
    request: Request,
    bucket: str,
    body: BulkDownloadRequest,
    s3: HcpStorage = Depends(get_s3_service),
    cache: CacheService | None = Depends(get_cache_service),
):
    """Start a background ZIP download task.

    Accepts either explicit keys or a prefix to list all objects under.
    Returns 202 with task_id for polling.
    """
    if body.prefix is not None:
        keys = await _list_all_keys(s3, bucket, body.prefix)
    elif body.keys:
        keys = body.keys
    else:
        from fastapi import HTTPException

        raise HTTPException(400, "Provide either 'prefix' or 'keys'")

    if len(keys) > MAX_ZIP_OBJECTS:
        from fastapi import HTTPException

        raise HTTPException(
            400,
            f"Too many objects ({len(keys)}). Maximum is {MAX_ZIP_OBJECTS}.",
        )

    if len(keys) == 0:
        from fastapi import HTTPException

        raise HTTPException(400, "No objects found under the given prefix")

    task_id = str(uuid.uuid4())

    # Schedule the ZIP build as a background task
    asyncio.ensure_future(_build_zip(task_id, s3, bucket, keys, cache))

    return ZipTaskResponse(
        task_id=task_id,
        status="processing",
        total=len(keys),
    )


@router.get("/download/{task_id}")
async def get_zip_download(
    bucket: str,
    task_id: str,
    cache: CacheService | None = Depends(get_cache_service),
):
    """Poll ZIP task status or download the completed ZIP."""
    from fastapi import HTTPException

    state = await _get_task_state(task_id, cache)
    if not state:
        raise HTTPException(404, "Task not found")

    if state["status"] == "processing":
        return ZipTaskResponse(
            task_id=task_id,
            status="processing",
            total=state.get("total", 0),
            completed=state.get("completed", 0),
            failed=state.get("failed", 0),
        )

    if state["status"] == "failed":
        raise HTTPException(
            500,
            detail={
                "status": "failed",
                "error": state.get("error", "Unknown error"),
                "failed_keys": state.get("failed_keys", []),
            },
        )

    # status == "ready" — stream the file
    zip_path = state.get("path", "")
    if not zip_path or not Path(zip_path).exists():
        raise HTTPException(500, "ZIP file not found on disk")

    async def _cleanup() -> None:
        try:
            Path(zip_path).unlink(missing_ok=True)
        except OSError:
            pass
        _zip_tasks.pop(task_id, None)
        if cache and cache.enabled:
            await cache.delete(f"zip_task:{task_id}")

    return FileResponse(
        path=zip_path,
        media_type="application/zip",
        filename=f"{bucket}-objects.zip",
        background=StarletteBackgroundTask(_cleanup),
        headers={
            "X-Zip-Failed": str(state.get("failed", 0)),
            "X-Zip-Failed-Keys": ",".join(state.get("failed_keys", [])[:50]),
        },
    )


# ── Bulk presign (must be before {key:path} catch-all) ───────────────


@router.post("/presign", response_model=BulkPresignResponse)
async def bulk_presign(
    bucket: str,
    body: BulkPresignRequest,
    s3: HcpStorage = Depends(get_s3_service),
):
    urls = []
    for key in body.keys:
        try:
            url = await asyncio.to_thread(
                s3.generate_presigned_url, bucket, key, body.expires_in
            )
            urls.append({"key": key, "url": url})
        except (ClientError, BotoCoreError):
            continue
    return BulkPresignResponse(urls=urls, expires_in=body.expires_in)


# ── Routes with /acl suffix (must be before {key:path} catch-all) ───


@router.get("/{key:path}/acl", response_model=AclResponse)
async def get_object_acl(
    bucket: str,
    key: str,
    s3: HcpStorage = Depends(get_s3_service),
):
    result = await run_s3(s3.get_object_acl, f"object '{key}'", bucket, key)
    return {
        "owner": result.get("Owner", {}),
        "grants": result.get("Grants", []),
    }


@router.put("/{key:path}/acl", response_model=StatusResponse)
async def put_object_acl(
    bucket: str,
    key: str,
    body: AclPolicy,
    s3: HcpStorage = Depends(get_s3_service),
):
    await run_s3(
        s3.put_object_acl,
        f"object '{key}'",
        bucket,
        key,
        body.model_dump(exclude_none=True),
    )
    return {"status": "updated"}


# ── Copy route (must be before {key:path} catch-all) ─────────────────


@router.post("/{key:path}/copy", response_model=ObjectMutationResponse)
async def copy_object(
    bucket: str,
    key: str,
    body: CopyObjectRequest,
    s3: HcpStorage = Depends(get_s3_service),
):
    await run_s3(
        s3.copy_object,
        f"object '{key}'",
        body.source_bucket,
        body.source_key,
        bucket,
        key,
    )
    return ObjectMutationResponse(status="copied", bucket=bucket, key=key)


# ── Single-object CRUD ({key:path} catch-all routes last) ────────────


@router.post("/{key:path}", response_model=UploadObjectResponse, status_code=201)
async def upload_object(
    bucket: str,
    key: str,
    file: UploadFile = File(...),
    s3: HcpStorage = Depends(get_s3_service),
):
    await run_s3(s3.put_object, f"object '{key}'", bucket, key, file.file)
    return UploadObjectResponse(bucket=bucket, key=key)


@router.get("/{key:path}")
async def download_object(
    bucket: str,
    key: str,
    s3: HcpStorage = Depends(get_s3_service),
):
    result = await run_s3(s3.get_object, f"object '{key}'", bucket, key)
    body = result["Body"]
    return StreamingResponse(
        content=body.iter_chunks(),
        media_type=result.get("ContentType", "application/octet-stream"),
        headers={
            "Content-Length": str(result.get("ContentLength", "")),
            "ETag": result.get("ETag", ""),
        },
    )


@router.head("/{key:path}", response_model=HeadObjectResponse)
async def head_object(
    bucket: str,
    key: str,
    s3: HcpStorage = Depends(get_s3_service),
):
    result = await run_s3(s3.head_object, f"object '{key}'", bucket, key)
    return HeadObjectResponse(
        content_length=result.get("ContentLength"),
        content_type=result.get("ContentType"),
        etag=result.get("ETag"),
        last_modified=str(result.get("LastModified", "")),
    )


@router.delete("/{key:path}", response_model=ObjectMutationResponse)
async def delete_object(
    bucket: str,
    key: str,
    s3: HcpStorage = Depends(get_s3_service),
):
    await run_s3(s3.delete_object, f"object '{key}'", bucket, key)
    return ObjectMutationResponse(status="deleted", bucket=bucket, key=key)
