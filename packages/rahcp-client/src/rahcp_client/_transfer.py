"""Retry wrapper for presigned-URL transfers (direct PUT/GET to HCP S3).

Presigned transfers bypass :meth:`HCPClient.request` (which has its own retry),
so this adds equivalent retry + backoff for the data plane: transient transport
errors and 408/425/429/5xx responses are retried with exponential backoff +
jitter, while terminal responses (e.g. 404) propagate immediately.
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from rahcp_client.errors import RetryableError

T = TypeVar("T")

# Transient HTTP statuses worth retrying on a presigned transfer.
RETRYABLE_TRANSFER_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


def raise_if_transient(resp: httpx.Response, bucket: str, key: str) -> None:
    """Raise :class:`RetryableError` if a presigned response is transiently failed.

    Call this before the terminal ``_raise_for_presigned`` check: transient
    statuses become a retry signal, everything else falls through to be handled
    (and, for other 4xx, raised) as a terminal error.
    """
    if resp.status_code in RETRYABLE_TRANSFER_STATUS:
        raise RetryableError(
            f"{resp.status_code} for {bucket}/{key}", status_code=resp.status_code
        )


async def transfer_with_retry(
    attempt: Callable[[], Awaitable[T]],
    *,
    max_attempts: int,
    base_delay: float,
) -> T:
    """Run a presigned-transfer ``attempt`` coroutine, retrying transient failures.

    Retries ``httpx.TransportError`` (connection/read/timeout) and
    :class:`RetryableError` (transient HTTP statuses) with exponential backoff +
    jitter. ``base_delay`` also bounds the jitter, so ``0.0`` retries with no
    wait (useful in tests). Terminal errors propagate immediately.

    Args:
        attempt: A coroutine factory performing one full transfer attempt. It
            must be safe to call more than once (re-open files, re-read bytes).
        max_attempts: Maximum attempts (1 disables retrying).
        base_delay: Base backoff delay in seconds.
    """
    async for retry_state in AsyncRetrying(
        stop=stop_after_attempt(max(1, max_attempts)),
        wait=wait_exponential_jitter(initial=base_delay, max=60.0, jitter=base_delay),
        retry=retry_if_exception_type((httpx.TransportError, RetryableError)),
        reraise=True,
    ):
        with retry_state:
            return await attempt()
    raise RuntimeError("unreachable")  # pragma: no cover
