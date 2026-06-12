"""Streaming bulk upload — fetch each object's bytes on the fly, never staged to disk.

Shares the producer/consumer pipeline, batched presigning, HEAD skip/verify guards,
and tracker bookkeeping with ``bulk_upload``; only the *source* differs (a caller
``fetch`` coroutine returning bytes instead of a local file).
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import PurePosixPath

import httpx

from rahcp_client.bulk.config import BulkStreamConfig, TransferStats
from rahcp_client.bulk.helpers import (
    Counters,
    make_pool,
    mark_done,
    mark_error,
    pool_put_bytes,
    pool_settings,
    remote_exists_matching,
    run_pipeline,
    verify_remote_size,
)

log = logging.getLogger(__name__)


async def bulk_stream_upload(
    cfg: BulkStreamConfig,
    items: list[tuple[str, str]],
    fetch: Callable[[str], Awaitable[bytes]],
) -> TransferStats:
    """Upload objects whose bytes are fetched on demand (no local staging).

    Args:
        cfg: Streaming upload configuration.
        items: ``(key, fetch_id)`` pairs — ``key`` is the full S3 object key,
            ``fetch_id`` is whatever ``fetch`` needs to produce the bytes.
        fetch: Async callable ``fetch_id -> bytes`` (e.g. a retrying IIIF
            download). It is the caller's job to make it resilient.

    Per item (unless already done / already in the bucket): skip-HEAD →
    ``fetch`` → optional byte validation → presigned PUT → optional verify →
    tracker mark. Reuses the same engine and guards as ``bulk_upload``.
    """
    from rahcp_client.errors import ConflictError

    counters = Counters(done_keys=await asyncio.to_thread(cfg.tracker.done_keys))
    verify_ssl, pool_timeout, _ = pool_settings(cfg.client)
    pool = make_pool(cfg.workers, verify_ssl=verify_ssl, timeout=pool_timeout)

    log.info(
        "Stream upload: %d items → s3://%s (%d workers, presign batch %d, %d done)",
        len(items),
        cfg.bucket,
        cfg.workers,
        cfg.presign_batch_size,
        len(counters.done_keys),
    )

    async def transfer_one(
        key: str, fetch_id: str, presigned_url: str | None
    ) -> tuple[str, int]:
        if key in counters.done_keys:
            return "skipped", 0

        # Skip before downloading — don't re-fetch what's already in the bucket.
        if await remote_exists_matching(
            cfg.client.s3,
            cfg.bucket,
            key,
            skip_existing=cfg.skip_existing,
            retry_errors=cfg.retry_errors,
        ):
            mark_done(cfg.tracker, counters.done_keys, key, 0)
            return "skipped", 0

        try:
            data = await fetch(fetch_id)
        except Exception as exc:
            mark_error(cfg.tracker, key, 0, exc, cfg.on_error, phase="download")
            return "error", 0

        size = len(data)

        if cfg.validate_bytes is not None:
            try:
                cfg.validate_bytes(data, PurePosixPath(key).suffix)
            except Exception as exc:
                mark_error(cfg.tracker, key, size, exc, cfg.on_error, phase="validate")
                return "error", 0

        try:
            if presigned_url:
                etag = await pool_put_bytes(pool, presigned_url, data, cfg.bucket, key)
            else:
                etag = await cfg.client.s3.upload(cfg.bucket, key, data)
        except ConflictError:
            mark_done(cfg.tracker, counters.done_keys, key, size)
            return "skipped", 0
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 409:
                mark_done(cfg.tracker, counters.done_keys, key, size)
                return "skipped", 0
            mark_error(cfg.tracker, key, size, exc, cfg.on_error, phase="upload")
            return "error", 0
        except Exception as exc:
            mark_error(cfg.tracker, key, size, exc, cfg.on_error, phase="upload")
            return "error", 0

        verified = False
        if cfg.verify_upload:
            try:
                await verify_remote_size(cfg.client.s3, cfg.bucket, key, size)
                verified = True
            except Exception as exc:
                mark_error(cfg.tracker, key, size, exc, cfg.on_error, phase="verify")
                return "error", 0

        mark_done(
            cfg.tracker,
            counters.done_keys,
            key,
            size,
            etag=etag or None,
            validated=cfg.validate_bytes is not None,
            verified=verified,
        )
        return "ok", size

    async def produce(queue: asyncio.Queue) -> None:
        if cfg.retry_errors:
            error_keys = {
                k for k, _ in await asyncio.to_thread(cfg.tracker.error_entries)
            }
            todo = [(k, fid) for k, fid in items if k in error_keys]
        else:
            todo = [(k, fid) for k, fid in items if k not in counters.done_keys]

        pending: list[tuple[str, str]] = []

        async def flush() -> None:
            if not pending:
                return
            keys = [k for k, _ in pending]
            try:
                url_map = await cfg.client.s3.presign_bulk(
                    cfg.bucket, keys, method="put_object"
                )
            except Exception:
                log.warning("Bulk presign failed, falling back to per-key presign")
                url_map = {}
            for key, fetch_id in pending:
                await queue.put((key, fetch_id, url_map.get(key)))
            pending.clear()

        for key, fetch_id in todo:
            pending.append((key, fetch_id))
            if len(pending) >= cfg.presign_batch_size:
                await flush()
        await flush()

    return await run_pipeline(
        workers=cfg.workers,
        queue_depth=cfg.queue_depth,
        pool=pool,
        counters=counters,
        tracker=cfg.tracker,
        on_progress=cfg.on_progress,
        progress_interval=cfg.progress_interval,
        transfer_fn=transfer_one,
        produce_fn=produce,
    )
