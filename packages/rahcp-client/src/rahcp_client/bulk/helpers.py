"""Shared helpers for the bulk transfer engine."""

from __future__ import annotations

import fnmatch
import logging
import time
from collections.abc import Callable

import httpx
from pydantic import BaseModel, ConfigDict, Field

from rahcp_tracker import TrackerProtocol, TransferStatus

from rahcp_client.bulk.config import TransferStats
from rahcp_client.bulk.protocol import BulkClient

log = logging.getLogger(__name__)

_DONE = object()


class Counters(BaseModel):
    """Mutable transfer counters — shared across workers."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ok: int = 0
    skipped: int = 0
    errors: int = 0
    total_bytes: int = 0
    done_keys: set[str] = Field(default_factory=set)
    t0: float = Field(default_factory=time.monotonic)
    last_report: float = Field(default_factory=time.monotonic)


def matches_filters(name: str, include: list[str], exclude: list[str]) -> bool:
    """Check if a filename matches include/exclude glob patterns."""
    if exclude and any(fnmatch.fnmatch(name, pat) for pat in exclude):
        return False
    if include and not any(fnmatch.fnmatch(name, pat) for pat in include):
        return False
    return True


def record_result(counters: Counters, result: str, byte_count: int = 0) -> None:
    """Update counters from a single transfer result."""
    if result == "ok":
        counters.ok += 1
        counters.total_bytes += byte_count
    elif result == "skipped":
        counters.skipped += 1
    else:
        counters.errors += 1


def mark_done(
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


def mark_error(
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


def maybe_report(
    on_progress: Callable[[TransferStats], None] | None,
    progress_interval: float,
    counters: Counters,
) -> None:
    """Fire progress callback if enough time has passed."""
    now = time.monotonic()
    if on_progress and now - counters.last_report >= progress_interval:
        counters.last_report = now
        on_progress(build_stats(counters))


def build_stats(counters: Counters) -> TransferStats:
    """Create a stats snapshot from the current counters."""
    return TransferStats(
        ok=counters.ok,
        skipped=counters.skipped,
        errors=counters.errors,
        total_bytes=counters.total_bytes,
        elapsed=time.monotonic() - counters.t0,
    )


def extract_client_settings(client: BulkClient) -> tuple[bool, float, int]:
    """Extract verify_ssl, timeout, and multipart_threshold from client.

    Returns safe defaults if the client doesn't expose internals (e.g. mocks).
    """
    verify = getattr(getattr(client.s3, "_client", None), "verify_ssl", True)
    raw_timeout = getattr(getattr(client.s3, "_client", None), "timeout", 60.0)
    raw_mp = getattr(getattr(client.s3, "_client", None), "multipart_threshold", None)

    timeout = (
        max(120.0, raw_timeout * 2) if isinstance(raw_timeout, (int, float)) else 120.0
    )
    multipart_threshold = raw_mp if isinstance(raw_mp, int) else 100 * 1024 * 1024

    return bool(verify), timeout, multipart_threshold


def make_pool(
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
