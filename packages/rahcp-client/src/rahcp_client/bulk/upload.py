"""Bulk upload — producer-consumer pipeline with batch presigning."""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path

import httpx

from rahcp_tracker import TransferStatus

from rahcp_client.bulk.config import BulkUploadConfig, TransferStats
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
    record_result,
)

log = logging.getLogger(__name__)


async def bulk_upload(cfg: BulkUploadConfig) -> TransferStats:
    """Upload a directory to S3 with batch presigning and connection pooling."""
    from rahcp_client.errors import ConflictError, NotFoundError

    src = cfg.source_dir
    counters = Counters(done_keys=cfg.tracker.done_keys())
    queue: asyncio.Queue[tuple[Path, str, str | None] | object] = asyncio.Queue(
        maxsize=cfg.workers * cfg.queue_depth
    )

    verify_ssl, pool_timeout, multipart_threshold = extract_client_settings(cfg.client)
    pool = make_pool(cfg.workers, verify_ssl=verify_ssl, timeout=pool_timeout)

    log.info(
        "Bulk upload: %s → s3://%s/%s (%d workers, presign batch %d, %d done)",
        src,
        cfg.bucket,
        cfg.prefix,
        cfg.workers,
        cfg.presign_batch_size,
        len(counters.done_keys),
    )

    async def transfer_one(
        file_path: Path, key: str, presigned_url: str | None
    ) -> tuple[str, int]:
        if key in counters.done_keys:
            return "skipped", 0

        local_size = file_path.stat().st_size

        # Pre-upload validation
        validated = False
        if cfg.validate_file:
            try:
                await asyncio.to_thread(cfg.validate_file, file_path)
                validated = True
            except Exception as exc:
                cfg.tracker.mark(
                    key,
                    local_size,
                    TransferStatus.error,
                    f"validation: {exc!s:.200}",
                    validated=False,
                )
                log.warning("Validation failed: %s — %s", key, exc)
                if cfg.on_error:
                    cfg.on_error(key, exc)
                return "error", 0

        # Skip existing (HEAD check)
        if cfg.skip_existing and not cfg.retry_errors:
            try:
                meta = await cfg.client.s3.head(cfg.bucket, key)
                remote_size = meta.get("content-length")
                if remote_size is None or int(remote_size) == local_size:
                    mark_done(
                        cfg.tracker,
                        counters.done_keys,
                        key,
                        local_size,
                        validated=validated,
                    )
                    return "skipped", 0
            except NotFoundError:
                pass
            except Exception:
                pass

        try:
            if presigned_url and local_size < multipart_threshold:
                content = await asyncio.to_thread(file_path.read_bytes)
                resp = await pool.put(presigned_url, content=content)
                if resp.status_code >= 400:
                    raise httpx.HTTPStatusError(
                        f"{resp.status_code} for {cfg.bucket}/{key}",
                        request=resp.request,
                        response=resp,
                    )
                etag = resp.headers.get("etag", "")
            else:
                etag = await cfg.client.s3.upload(cfg.bucket, key, file_path)

            verified = False
            if cfg.verify_upload:
                meta = await cfg.client.s3.head(cfg.bucket, key)
                remote_size = int(meta.get("content-length", 0))
                if remote_size != local_size:
                    raise ValueError(
                        f"Size mismatch: local={local_size}, remote={remote_size}"
                    )
                verified = True

            mark_done(
                cfg.tracker,
                counters.done_keys,
                key,
                local_size,
                etag=etag or None,
                validated=validated,
                verified=verified,
            )
            return "ok", local_size

        except (ConflictError, httpx.HTTPStatusError) as exc:
            if isinstance(exc, ConflictError) or (
                hasattr(exc, "response") and exc.response.status_code == 409
            ):
                mark_done(cfg.tracker, counters.done_keys, key, local_size)
                return "skipped", 0
            mark_error(cfg.tracker, key, local_size, exc, cfg.on_error)
            return "error", 0
        except Exception as exc:
            mark_error(cfg.tracker, key, local_size, exc, cfg.on_error)
            return "error", 0

    async def worker() -> None:
        while True:
            item = await queue.get()
            if item is _DONE:
                queue.task_done()
                break
            try:
                file_path, key, url = item  # type: ignore[misc]
                result, byte_count = await transfer_one(file_path, key, url)
                record_result(counters, result, byte_count)
                maybe_report(cfg.on_progress, cfg.progress_interval, counters)
            finally:
                queue.task_done()

    async def produce() -> None:
        batch_size = cfg.presign_batch_size

        if cfg.retry_errors:
            for key, _ in cfg.tracker.error_entries():
                await queue.put((src / key, key, None))
        else:
            pending: list[tuple[Path, str]] = []

            async def flush_batch() -> None:
                if not pending:
                    return
                keys = [k for _, k in pending]
                try:
                    url_map = await cfg.client.s3.presign_bulk(
                        cfg.bucket, keys, method="put_object"
                    )
                except Exception:
                    log.warning("Bulk presign failed, falling back to per-file")
                    url_map = {}
                for fp, k in pending:
                    await queue.put((fp, k, url_map.get(k)))
                pending.clear()

            file_list: list[tuple[Path, str]] = []

            def scan_files() -> None:
                for f in src.rglob("*"):
                    if f.is_file() and matches_filters(
                        f.name, cfg.include, cfg.exclude
                    ):
                        rel = f.relative_to(src)
                        key = f"{cfg.prefix}{rel}" if cfg.prefix else str(rel)
                        if key not in counters.done_keys:
                            file_list.append((f, key))

            await asyncio.to_thread(scan_files)

            for fp, key in file_list:
                pending.append((fp, key))
                if len(pending) >= batch_size:
                    await flush_batch()
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
