"""Stream IIIF images straight to HCP S3 — no local disk.

Builds ``(s3_key, image_url)`` items from each batch's IIIF manifest, then pushes
them through the bulk streaming engine: skip-existing, byte validation, verify,
and resumable tracking. This is the programmatic form of ``rahcp iiif upload`` —
it ingests N batches on the fly without staging anything to disk.

Run:
    uv run python examples/iiif_stream_to_s3.py
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import httpx

from rahcp_client import BulkStreamConfig, HCPClient, bulk_stream_upload
from rahcp_iiif.manifest import (
    build_image_url,
    fetch_with_retry,
    file_extension,
    get_image_ids,
)
from rahcp_tracker import SqliteTracker
from rahcp_validate import validate_bytes_by_extension

IIIF_BASE = "https://lbiiif.riksarkivet.se"
BUCKET = "images-batch"
BATCHES = ["A0038595", "A0038596", "A0038597"]  # N batches, ingested on the fly
QUERY_PARAMS = "full/max/0/default.jpg"


async def main() -> None:
    tracker = SqliteTracker(Path(".rahcp/iiif-stream.db"))
    ext = file_extension(QUERY_PARAMS)

    async with (
        HCPClient.from_env() as client,
        httpx.AsyncClient(timeout=60) as iiif,
    ):
        # 1. Enumerate manifests -> (s3_key, image_url) items (cheap: just strings).
        items: list[tuple[str, str]] = []
        for batch_id in BATCHES:
            for image_id in await get_image_ids(batch_id, base_url=IIIF_BASE):
                key = f"{batch_id}/{image_id}{ext}"
                url = build_image_url(
                    image_id, base_url=IIIF_BASE, query_params=QUERY_PARAMS
                )
                items.append((key, url))
        print(f"{len(items)} images across {len(BATCHES)} batches")

        # 2. fetch = retrying IIIF download over a shared pooled client.
        async def fetch(url: str) -> bytes:
            resp = await fetch_with_retry(iiif, url)
            return resp.content

        # 3. Stream to S3 — no disk; skip-existing + validate + verify.
        stats = await bulk_stream_upload(
            BulkStreamConfig(
                client=client,
                bucket=BUCKET,
                tracker=tracker,
                workers=20,
                skip_existing=True,
                validate_bytes=validate_bytes_by_extension,
                verify_upload=True,
                on_progress=lambda s: print(
                    f"  {s.done} done ({s.ok} ok, {s.skipped} skipped, {s.errors} err)"
                    f" — {s.mb_per_sec:.1f} MB/s"
                ),
                on_error=lambda key, exc: print(f"  FAILED {key} — {exc}"),
            ),
            items,
            fetch,
        )

    print(
        f"Done: {stats.ok} uploaded, {stats.skipped} skipped, {stats.errors} errors"
        f" — {stats.total_bytes / 1024 / 1024:.0f} MB in {stats.elapsed:.0f}s"
    )
    tracker.close()


if __name__ == "__main__":
    asyncio.run(main())
