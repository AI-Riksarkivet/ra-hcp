"""Bulk transfer engine — producer-consumer pipeline for large-scale S3 operations."""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import time
from pathlib import Path
from collections.abc import Callable
from typing import Protocol

from pydantic import BaseModel, ConfigDict, Field, SkipValidation

from rahcp_tracker import TrackerProtocol, TransferStatus

log = logging.getLogger(__name__)

_DONE = object()


# ── Protocols ───────────────────────────────────────────────────────


class S3Client(Protocol):
    """Minimal S3 interface required by the bulk transfer engine."""

    async def head(self, bucket: str, key: str) -> dict: ...
    async def upload(self, bucket: str, key: str, data: Path) -> str: ...
    async def download(self, bucket: str, key: str, dest: Path) -> int: ...
    async def list_objects(
        self,
        bucket: str,
        prefix: str,
        *,
        max_keys: int = 1000,
        continuation_token: str | None = None,
    ) -> dict: ...


class BulkClient(Protocol):
    """Client that exposes an ``s3`` property satisfying :class:`S3Client`."""

    @property
    def s3(self) -> S3Client: ...


# ── Stats ───────────────────────────────────────────────────────────


class TransferStats(BaseModel):
    """Snapshot of a running bulk transfer."""

    ok: int = 0
    skipped: int = 0
    errors: int = 0
    total_bytes: int = 0
    elapsed: float = 0.0

    @property
    def done(self) -> int:
        """Total files processed (ok + skipped + errors)."""
        return self.ok + self.skipped + self.errors

    @property
    def files_per_sec(self) -> float:
        """Throughput in files per second."""
        return self.ok / self.elapsed if self.elapsed > 0 else 0.0

    @property
    def mb_per_sec(self) -> float:
        """Throughput in megabytes per second."""
        return (
            (self.total_bytes / 1024 / 1024) / self.elapsed if self.elapsed > 0 else 0.0
        )


# ── Config ──────────────────────────────────────────────────────────


class BulkUploadConfig(BaseModel):
    """Configuration for a bulk upload job."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: SkipValidation[BulkClient]
    bucket: str
    source_dir: Path
    tracker: TrackerProtocol
    prefix: str = ""
    workers: int = 10
    queue_depth: int = 8
    skip_existing: bool = True
    retry_errors: bool = False
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    validate_file: Callable[[Path], None] | None = None
    verify_upload: bool = False
    on_progress: Callable[[TransferStats], None] | None = None
    on_error: Callable[[str, Exception], None] | None = None
    progress_interval: float = 5.0


class BulkDownloadConfig(BaseModel):
    """Configuration for a bulk download job."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    client: SkipValidation[BulkClient]
    bucket: str
    dest_dir: Path
    tracker: TrackerProtocol
    prefix: str = ""
    workers: int = 10
    queue_depth: int = 8
    retry_errors: bool = False
    include: list[str] = Field(default_factory=list)
    exclude: list[str] = Field(default_factory=list)
    validate_file: Callable[[Path], None] | None = None
    verify_download: bool = False
    on_progress: Callable[[TransferStats], None] | None = None
    on_error: Callable[[str, Exception], None] | None = None
    progress_interval: float = 5.0


# ── Internal state ──────────────────────────────────────────────────


class _Counters(BaseModel):
    """Mutable transfer counters — not part of public API."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ok: int = 0
    skipped: int = 0
    errors: int = 0
    total_bytes: int = 0
    done_keys: set[str] = Field(default_factory=set)
    t0: float = Field(default_factory=time.monotonic)
    last_report: float = Field(default_factory=time.monotonic)


def _matches_filters(
    name: str,
    include: list[str],
    exclude: list[str],
) -> bool:
    """Check if a filename matches include/exclude glob patterns.

    If include is empty, all files match. If exclude matches, the file is skipped.
    Patterns are matched against the filename only (not the full path).
    """
    if exclude and any(fnmatch.fnmatch(name, pat) for pat in exclude):
        return False
    if include and not any(fnmatch.fnmatch(name, pat) for pat in include):
        return False
    return True


def _record_result(counters: _Counters, result: str, byte_count: int = 0) -> None:
    """Update counters from a transfer result."""
    if result == "ok":
        counters.ok += 1
        counters.total_bytes += byte_count
    elif result == "skipped":
        counters.skipped += 1
    else:
        counters.errors += 1


def _mark_done(
    tracker: TrackerProtocol,
    done_keys: set[str],
    key: str,
    size: int,
    *,
    etag: str | None = None,
    validated: bool = False,
    verified: bool = False,
) -> None:
    """Mark a key as done in both the tracker and the in-memory set."""
    tracker.mark(
        key,
        size,
        TransferStatus.done,
        etag=etag,
        validated=validated,
        verified=verified,
    )
    done_keys.add(key)


def _mark_error(
    tracker: TrackerProtocol,
    key: str,
    size: int,
    exc: Exception,
    on_error: Callable[[str, Exception], None] | None,
) -> None:
    """Mark a key as failed and notify the error callback."""
    tracker.mark(key, size, TransferStatus.error, str(exc)[:200])
    log.warning("Transfer failed: %s — %s", key, exc)
    if on_error:
        on_error(key, exc)


def _maybe_report(
    on_progress: Callable[[TransferStats], None] | None,
    progress_interval: float,
    counters: _Counters,
) -> None:
    """Fire progress callback if enough time has passed."""
    now = time.monotonic()
    if on_progress and now - counters.last_report >= progress_interval:
        counters.last_report = now
        on_progress(_build_stats(counters))


def _build_stats(counters: _Counters) -> TransferStats:
    """Create a ``TransferStats`` snapshot from the current counters."""
    return TransferStats(
        ok=counters.ok,
        skipped=counters.skipped,
        errors=counters.errors,
        total_bytes=counters.total_bytes,
        elapsed=time.monotonic() - counters.t0,
    )


# ── Upload ──────────────────────────────────────────────────────────


async def bulk_upload(cfg: BulkUploadConfig) -> TransferStats:
    """Upload a directory to S3 using a producer-consumer pipeline."""
    import httpx

    from rahcp_client.errors import ConflictError, NotFoundError

    src = cfg.source_dir
    counters = _Counters(done_keys=cfg.tracker.done_keys())
    queue: asyncio.Queue[Path | object] = asyncio.Queue(
        maxsize=cfg.workers * cfg.queue_depth
    )

    log.info(
        "Bulk upload: %s → s3://%s/%s (%d workers, %d already done)",
        src,
        cfg.bucket,
        cfg.prefix,
        cfg.workers,
        len(counters.done_keys),
    )

    async def transfer_one(file_path: Path) -> tuple[str, int]:
        """Upload a single file. Returns (result, byte_count)."""
        rel = file_path.relative_to(src)
        key = f"{cfg.prefix}{rel}" if cfg.prefix else str(rel)

        if key in counters.done_keys:
            return "skipped", 0

        local_size = file_path.stat().st_size

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

        if cfg.skip_existing and not cfg.retry_errors:
            try:
                meta = await cfg.client.s3.head(cfg.bucket, key)
                remote_size = meta.get("content-length")
                if remote_size is None or int(remote_size) == local_size:
                    _mark_done(
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
            etag = await cfg.client.s3.upload(cfg.bucket, key, file_path)
            verified = False
            if cfg.verify_upload:
                meta = await cfg.client.s3.head(cfg.bucket, key)
                remote_size = int(meta.get("content-length", 0))
                if remote_size != local_size:
                    raise ValueError(
                        f"Size mismatch after upload: local={local_size}, remote={remote_size}"
                    )
                verified = True
            _mark_done(
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
            if isinstance(exc, ConflictError) or exc.response.status_code == 409:
                _mark_done(cfg.tracker, counters.done_keys, key, local_size)
                return "skipped", 0
            _mark_error(cfg.tracker, key, local_size, exc, cfg.on_error)
            return "error", 0
        except Exception as exc:
            _mark_error(cfg.tracker, key, local_size, exc, cfg.on_error)
            return "error", 0

    async def worker() -> None:
        while True:
            item = await queue.get()
            if item is _DONE:
                queue.task_done()
                break
            try:
                result, byte_count = await transfer_one(item)  # type: ignore[arg-type]
                _record_result(counters, result, byte_count)
                _maybe_report(cfg.on_progress, cfg.progress_interval, counters)
            finally:
                queue.task_done()

    async def produce() -> None:
        if cfg.retry_errors:
            for key, _ in cfg.tracker.error_entries():
                await queue.put(src / key)
        else:
            loop = asyncio.get_running_loop()

            def _scan_and_enqueue() -> None:
                for f in src.rglob("*"):
                    if f.is_file() and _matches_filters(
                        f.name, cfg.include, cfg.exclude
                    ):
                        future = asyncio.run_coroutine_threadsafe(queue.put(f), loop)
                        future.result()  # blocks thread until queue has space

            await asyncio.to_thread(_scan_and_enqueue)
        for _ in range(cfg.workers):
            await queue.put(_DONE)

    worker_tasks = [asyncio.create_task(worker()) for _ in range(cfg.workers)]
    await asyncio.create_task(produce())
    await asyncio.gather(*worker_tasks)

    cfg.tracker.commit()
    return _build_stats(counters)


# ── Download ────────────────────────────────────────────────────────


async def bulk_download(cfg: BulkDownloadConfig) -> TransferStats:
    """Download objects from S3 using a producer-consumer pipeline."""
    dest = cfg.dest_dir
    dest.mkdir(parents=True, exist_ok=True)
    counters = _Counters(done_keys=cfg.tracker.done_keys())
    queue: asyncio.Queue[tuple[str, int] | object] = asyncio.Queue(
        maxsize=cfg.workers * cfg.queue_depth
    )

    log.info(
        "Bulk download: s3://%s/%s → %s (%d workers, %d already done)",
        cfg.bucket,
        cfg.prefix,
        dest,
        cfg.workers,
        len(counters.done_keys),
    )

    async def transfer_one(key: str, size: int) -> tuple[str, int]:
        """Download a single object. Returns (result, byte_count)."""
        if key in counters.done_keys:
            return "skipped", 0

        file_path = dest / key
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists() and file_path.stat().st_size == size:
            _mark_done(cfg.tracker, counters.done_keys, key, size)
            return "skipped", 0

        try:
            bytes_dl = await cfg.client.s3.download(cfg.bucket, key, tmp_path)
            if cfg.verify_download and tmp_path.stat().st_size != size:
                tmp_path.unlink(missing_ok=True)
                raise ValueError(
                    f"Size mismatch after download: expected={size}, got={tmp_path.stat().st_size}"
                )
            tmp_path.rename(file_path)

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
                    log.warning("Validation failed after download: %s — %s", key, exc)
                    if cfg.on_error:
                        cfg.on_error(key, exc)
                    return "error", 0

            _mark_done(
                cfg.tracker,
                counters.done_keys,
                key,
                size,
                validated=validated,
            )
            return "ok", bytes_dl
        except Exception as exc:
            tmp_path.unlink(missing_ok=True)
            _mark_error(cfg.tracker, key, size, exc, cfg.on_error)
            return "error", 0

    async def worker() -> None:
        while True:
            item = await queue.get()
            if item is _DONE:
                queue.task_done()
                break
            try:
                key, size = item  # type: ignore[misc]
                result, byte_count = await transfer_one(key, size)
                _record_result(counters, result, byte_count)
                _maybe_report(cfg.on_progress, cfg.progress_interval, counters)
            finally:
                queue.task_done()

    async def produce() -> None:
        if cfg.retry_errors:
            for key, size in cfg.tracker.error_entries():
                await queue.put((key, size))
        else:
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
                    if not _matches_filters(filename, cfg.include, cfg.exclude):
                        continue
                    await queue.put((key, obj.get("Size", 0)))
                if not data.get("is_truncated"):
                    break
                token = data.get("next_continuation_token")
        for _ in range(cfg.workers):
            await queue.put(_DONE)

    worker_tasks = [asyncio.create_task(worker()) for _ in range(cfg.workers)]
    await asyncio.create_task(produce())
    await asyncio.gather(*worker_tasks)

    cfg.tracker.commit()
    return _build_stats(counters)
