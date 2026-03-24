"""Bulk download — producer-consumer pipeline with batch presigning."""

from __future__ import annotations

import asyncio
import logging

from rahcp_tracker import TransferStatus

from rahcp_client.bulk.config import BulkDownloadConfig, TransferStats
from rahcp_client.bulk.helpers import (
    Counters,
    _DONE,
    build_stats,
    extract_client_settings,
    make_pool,
    mark_done,
    mark_error,
    matches_filters,
    maybe_report,
    pool_download,
    record_result,
)

log = logging.getLogger(__name__)


async def bulk_download(cfg: BulkDownloadConfig) -> TransferStats:
    """Download objects from S3 with batch presigning and connection pooling."""
    dest = cfg.dest_dir
    dest.mkdir(parents=True, exist_ok=True)
    counters = Counters(done_keys=cfg.tracker.done_keys())
    queue: asyncio.Queue[tuple[str, int, str | None] | object] = asyncio.Queue(
        maxsize=cfg.workers * cfg.queue_depth
    )

    verify_ssl, pool_timeout, _ = extract_client_settings(cfg.client)
    pool = make_pool(cfg.workers, verify_ssl=verify_ssl, timeout=pool_timeout)

    log.info(
        "Bulk download: s3://%s/%s → %s (%d workers, presign batch %d, %d done)",
        cfg.bucket,
        cfg.prefix,
        dest,
        cfg.workers,
        cfg.presign_batch_size,
        len(counters.done_keys),
    )

    async def transfer_one(
        key: str, size: int, presigned_url: str | None
    ) -> tuple[str, int]:
        if key in counters.done_keys:
            return "skipped", 0

        file_path = dest / key
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists() and file_path.stat().st_size == size:
            mark_done(cfg.tracker, counters.done_keys, key, size)
            return "skipped", 0

        try:
            if presigned_url:
                bytes_dl = await pool_download(
                    pool,
                    presigned_url,
                    tmp_path,
                    cfg.bucket,
                    key,
                    size=size,
                    chunk_size=cfg.chunk_size,
                    stream_threshold=cfg.stream_threshold,
                )
            else:
                bytes_dl = await cfg.client.s3.download(cfg.bucket, key, tmp_path)

            if cfg.verify_download and tmp_path.stat().st_size != size:
                tmp_path.unlink(missing_ok=True)
                raise ValueError(
                    f"Size mismatch: expected={size}, got={tmp_path.stat().st_size}"
                )
            tmp_path.rename(file_path)

            # Post-download validation
            validated = False
            if cfg.validate_file:
                try:
                    await asyncio.to_thread(cfg.validate_file, file_path)
                    validated = True
                except Exception as exc:
                    file_path.unlink(missing_ok=True)
                    cfg.tracker.mark(
                        key,
                        size,
                        TransferStatus.error,
                        f"validation: {exc!s:.200}",
                        validated=False,
                    )
                    log.warning("Validation failed: %s — %s", key, exc)
                    if cfg.on_error:
                        cfg.on_error(key, exc)
                    return "error", 0

            mark_done(
                cfg.tracker,
                counters.done_keys,
                key,
                size,
                validated=validated,
            )
            return "ok", bytes_dl

        except Exception as exc:
            tmp_path.unlink(missing_ok=True)
            mark_error(cfg.tracker, key, size, exc, cfg.on_error)
            return "error", 0

    async def worker() -> None:
        while True:
            item = await queue.get()
            if item is _DONE:
                queue.task_done()
                break
            try:
                key, size, url = item  # type: ignore[misc]
                result, byte_count = await transfer_one(key, size, url)
                record_result(counters, result, byte_count)
                maybe_report(cfg.on_progress, cfg.progress_interval, counters)
            finally:
                queue.task_done()

    async def produce() -> None:
        batch_size = cfg.presign_batch_size

        if cfg.retry_errors:
            for key, size in cfg.tracker.error_entries():
                await queue.put((key, size, None))
        else:
            pending: list[tuple[str, int]] = []

            async def flush_batch() -> None:
                if not pending:
                    return
                keys = [k for k, _ in pending]
                try:
                    url_map = await cfg.client.s3.presign_bulk(
                        cfg.bucket, keys, method="get_object"
                    )
                except Exception:
                    log.warning("Bulk presign failed, falling back to per-file")
                    url_map = {}
                for k, sz in pending:
                    await queue.put((k, sz, url_map.get(k)))
                pending.clear()

            token = None
            while True:
                data = await cfg.client.s3.list_objects(
                    cfg.bucket, cfg.prefix, max_keys=1000, continuation_token=token
                )
                for obj in data.get("objects", []):
                    key = obj["Key"]
                    if key.endswith("/") and obj.get("Size", 0) == 0:
                        continue
                    filename = key.rsplit("/", 1)[-1]
                    if not matches_filters(filename, cfg.include, cfg.exclude):
                        continue
                    if key in counters.done_keys:
                        continue
                    pending.append((key, obj.get("Size", 0)))
                    if len(pending) >= batch_size:
                        await flush_batch()
                if not data.get("is_truncated"):
                    break
                token = data.get("next_continuation_token")
            await flush_batch()

        for _ in range(cfg.workers):
            await queue.put(_DONE)

    try:
        worker_tasks = [asyncio.create_task(worker()) for _ in range(cfg.workers)]
        await asyncio.create_task(produce())
        await asyncio.gather(*worker_tasks)
    finally:
        await pool.aclose()

    cfg.tracker.commit()
    return build_stats(counters)
