"""Bulk transfer engine — producer-consumer pipeline for large-scale S3 operations.

Optimizations:
- Batch presigning: presign URLs in configurable batches (default 200)
  to minimize API round-trips. 1 call per batch instead of 1 per file.
- Connection pooling: one shared httpx.AsyncClient per transfer job,
  reusing TCP/TLS connections across all workers.
- Adaptive chunk size: configurable download chunk size (default 256KB).
  Larger chunks reduce I/O syscalls for large files.
- Producer-side filtering: done keys are skipped before presigning,
  so resumed jobs don't waste presign calls on completed files.
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import time
from pathlib import Path
from collections.abc import Callable
from typing import Protocol

import httpx
from pydantic import BaseModel, ConfigDict, Field, SkipValidation

from rahcp_tracker import TrackerProtocol, TransferStatus

log = logging.getLogger(__name__)

_DONE = object()

# Default chunk size for streaming downloads (256 KB)
DEFAULT_CHUNK_SIZE = 256 * 1024


# ── Protocols ───────────────────────────────────────────────────────


class S3Client(Protocol):
    """Minimal S3 interface required by the bulk transfer engine."""

    async def head(self, bucket: str, key: str) -> dict: ...
    async def upload(self, bucket: str, key: str, data: Path) -> str: ...
    async def download(self, bucket: str, key: str, dest: Path) -> int: ...
    async def presign_put(
        self, bucket: str, key: str, *, expires: int = 3600
    ) -> str: ...
    async def presign_get(
        self, bucket: str, key: str, *, expires: int = 3600
    ) -> str: ...
    async def presign_bulk(
        self,
        bucket: str,
        keys: list[str],
        *,
        method: str = "get_object",
        expires: int = 3600,
    ) -> dict[str, str]: ...
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
    presign_batch_size: int = 200
    chunk_size: int = DEFAULT_CHUNK_SIZE
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
    presign_batch_size: int = 200
    chunk_size: int = DEFAULT_CHUNK_SIZE
    on_progress: Callable[[TransferStats], None] | None = None
    on_error: Callable[[str, Exception], None] | None = None
    progress_interval: float = 5.0


# ── Internal helpers ────────────────────────────────────────────────


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


def _matches_filters(name: str, include: list[str], exclude: list[str]) -> bool:
    """Check if a filename matches include/exclude glob patterns."""
    if exclude and any(fnmatch.fnmatch(name, pat) for pat in exclude):
        return False
    if include and not any(fnmatch.fnmatch(name, pat) for pat in include):
        return False
    return True


def _record_result(counters: _Counters, result: str, byte_count: int = 0) -> None:
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
    tracker.mark(key, size, TransferStatus.error, str(exc)[:200])
    log.warning("Transfer failed: %s — %s", key, exc)
    if on_error:
        on_error(key, exc)


def _maybe_report(
    on_progress: Callable[[TransferStats], None] | None,
    progress_interval: float,
    counters: _Counters,
) -> None:
    now = time.monotonic()
    if on_progress and now - counters.last_report >= progress_interval:
        counters.last_report = now
        on_progress(_build_stats(counters))


def _build_stats(counters: _Counters) -> TransferStats:
    return TransferStats(
        ok=counters.ok,
        skipped=counters.skipped,
        errors=counters.errors,
        total_bytes=counters.total_bytes,
        elapsed=time.monotonic() - counters.t0,
    )


def _make_pool(
    max_connections: int,
    *,
    verify_ssl: bool = True,
    timeout: float = 120.0,
) -> httpx.AsyncClient:
    """Create a shared connection pool for presigned URL transfers.

    Reuses TCP/TLS connections across workers — avoids handshake overhead
    per file. The pool is sized to match the worker count.
    """
    return httpx.AsyncClient(
        verify=verify_ssl,
        timeout=httpx.Timeout(timeout, connect=10.0),
        limits=httpx.Limits(
            max_connections=max_connections,
            max_keepalive_connections=max_connections,
        ),
    )


# ── Upload ──────────────────────────────────────────────────────────


async def bulk_upload(cfg: BulkUploadConfig) -> TransferStats:
    """Upload a directory to S3 with batch presigning and connection pooling."""
    from rahcp_client.errors import ConflictError, NotFoundError

    src = cfg.source_dir
    counters = _Counters(done_keys=cfg.tracker.done_keys())
    queue: asyncio.Queue[tuple[Path, str, str | None] | object] = asyncio.Queue(
        maxsize=cfg.workers * cfg.queue_depth
    )

    log.info(
        "Bulk upload: %s → s3://%s/%s (%d workers, presign batch %d, %d done)",
        src,
        cfg.bucket,
        cfg.prefix,
        cfg.workers,
        cfg.presign_batch_size,
        len(counters.done_keys),
    )

    # Extract settings for pool (use defaults if client doesn't expose internals)
    _verify = getattr(getattr(cfg.client.s3, "_client", None), "verify_ssl", True)
    _raw_timeout = getattr(getattr(cfg.client.s3, "_client", None), "timeout", 60.0)
    _timeout = (
        max(120.0, _raw_timeout * 2)
        if isinstance(_raw_timeout, (int, float))
        else 120.0
    )
    _raw_mp = getattr(
        getattr(cfg.client.s3, "_client", None), "multipart_threshold", None
    )
    _multipart_threshold = _raw_mp if isinstance(_raw_mp, int) else 100 * 1024 * 1024

    pool = _make_pool(cfg.workers, verify_ssl=bool(_verify), timeout=_timeout)

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
            if presigned_url and local_size < _multipart_threshold:
                # Use pre-fetched URL + shared pool
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
                # Large files → multipart (presign handled internally)
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
            if isinstance(exc, ConflictError) or (
                hasattr(exc, "response") and exc.response.status_code == 409
            ):
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
                file_path, key, url = item  # type: ignore[misc]
                result, byte_count = await transfer_one(file_path, key, url)
                _record_result(counters, result, byte_count)
                _maybe_report(cfg.on_progress, cfg.progress_interval, counters)
            finally:
                queue.task_done()

    async def produce() -> None:
        batch_size = cfg.presign_batch_size

        if cfg.retry_errors:
            for key, _ in cfg.tracker.error_entries():
                await queue.put((src / key, key, None))
        else:
            pending: list[tuple[Path, str]] = []

            async def _flush_batch() -> None:
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
                for file_path, key in pending:
                    await queue.put((file_path, key, url_map.get(key)))
                pending.clear()

            file_list: list[tuple[Path, str]] = []

            def _scan_files() -> None:
                for f in src.rglob("*"):
                    if f.is_file() and _matches_filters(
                        f.name, cfg.include, cfg.exclude
                    ):
                        rel = f.relative_to(src)
                        key = f"{cfg.prefix}{rel}" if cfg.prefix else str(rel)
                        if key not in counters.done_keys:
                            file_list.append((f, key))

            await asyncio.to_thread(_scan_files)

            for file_path, key in file_list:
                pending.append((file_path, key))
                if len(pending) >= batch_size:
                    await _flush_batch()
            await _flush_batch()

        for _ in range(cfg.workers):
            await queue.put(_DONE)

    try:
        worker_tasks = [asyncio.create_task(worker()) for _ in range(cfg.workers)]
        await asyncio.create_task(produce())
        await asyncio.gather(*worker_tasks)
    finally:
        await pool.aclose()

    cfg.tracker.commit()
    return _build_stats(counters)


# ── Download ────────────────────────────────────────────────────────


async def bulk_download(cfg: BulkDownloadConfig) -> TransferStats:
    """Download objects from S3 with batch presigning and connection pooling."""
    dest = cfg.dest_dir
    dest.mkdir(parents=True, exist_ok=True)
    counters = _Counters(done_keys=cfg.tracker.done_keys())
    queue: asyncio.Queue[tuple[str, int, str | None] | object] = asyncio.Queue(
        maxsize=cfg.workers * cfg.queue_depth
    )

    log.info(
        "Bulk download: s3://%s/%s → %s (%d workers, presign batch %d, %d done)",
        cfg.bucket,
        cfg.prefix,
        dest,
        cfg.workers,
        cfg.presign_batch_size,
        len(counters.done_keys),
    )

    _verify = getattr(getattr(cfg.client.s3, "_client", None), "verify_ssl", True)
    _raw_timeout = getattr(getattr(cfg.client.s3, "_client", None), "timeout", 60.0)
    _timeout = (
        max(120.0, _raw_timeout * 2)
        if isinstance(_raw_timeout, (int, float))
        else 120.0
    )

    pool = _make_pool(cfg.workers, verify_ssl=bool(_verify), timeout=_timeout)
    chunk_size = cfg.chunk_size

    async def transfer_one(
        key: str, size: int, presigned_url: str | None
    ) -> tuple[str, int]:
        if key in counters.done_keys:
            return "skipped", 0

        file_path = dest / key
        tmp_path = file_path.with_suffix(file_path.suffix + ".tmp")
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_path.exists() and file_path.stat().st_size == size:
            _mark_done(cfg.tracker, counters.done_keys, key, size)
            return "skipped", 0

        try:
            if presigned_url:
                # Stream download using shared pool + configurable chunk size
                async with pool.stream("GET", presigned_url) as resp:
                    if resp.status_code >= 400:
                        raise httpx.HTTPStatusError(
                            f"{resp.status_code} for {cfg.bucket}/{key}",
                            request=resp.request,
                            response=resp,
                        )
                    total = 0
                    f = await asyncio.to_thread(tmp_path.open, "wb")
                    try:
                        async for chunk in resp.aiter_bytes(chunk_size=chunk_size):
                            await asyncio.to_thread(f.write, chunk)
                            total += len(chunk)
                    finally:
                        await asyncio.to_thread(f.close)
                bytes_dl = total
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
                key, size, url = item  # type: ignore[misc]
                result, byte_count = await transfer_one(key, size, url)
                _record_result(counters, result, byte_count)
                _maybe_report(cfg.on_progress, cfg.progress_interval, counters)
            finally:
                queue.task_done()

    async def produce() -> None:
        batch_size = cfg.presign_batch_size

        if cfg.retry_errors:
            for key, size in cfg.tracker.error_entries():
                await queue.put((key, size, None))
        else:
            pending: list[tuple[str, int]] = []

            async def _flush_batch() -> None:
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
                for key, size in pending:
                    await queue.put((key, size, url_map.get(key)))
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
                    if not _matches_filters(filename, cfg.include, cfg.exclude):
                        continue
                    if key in counters.done_keys:
                        continue
                    pending.append((key, obj.get("Size", 0)))
                    if len(pending) >= batch_size:
                        await _flush_batch()
                if not data.get("is_truncated"):
                    break
                token = data.get("next_continuation_token")
            await _flush_batch()

        for _ in range(cfg.workers):
            await queue.put(_DONE)

    try:
        worker_tasks = [asyncio.create_task(worker()) for _ in range(cfg.workers)]
        await asyncio.create_task(produce())
        await asyncio.gather(*worker_tasks)
    finally:
        await pool.aclose()

    cfg.tracker.commit()
    return _build_stats(counters)
