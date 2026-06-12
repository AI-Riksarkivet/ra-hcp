"""IIIF manifest parsing — extract image IDs from Riksarkivet manifests."""

from __future__ import annotations

import logging

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from rahcp_iiif.config import IIIF_QUERY_PARAMS, IIIF_TIMEOUT, IIIF_URL

log = logging.getLogger(__name__)

# Transient HTTP statuses worth retrying. Other 4xx (e.g. 404) are terminal.
_RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class _TransientStatus(Exception):
    """Internal marker: a retryable HTTP status code was returned."""


async def fetch_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    attempts: int = 4,
    base_delay: float = 0.5,
) -> httpx.Response:
    """GET ``url``, retrying transient failures with exponential backoff + jitter.

    Retries connection/timeout errors and 408/425/429/5xx responses. Any other
    4xx (e.g. 404) is treated as terminal and raised immediately — retrying it
    would only waste time.

    Args:
        client: An open ``httpx.AsyncClient``.
        url: The URL to GET.
        attempts: Maximum number of attempts (1 disables retrying).
        base_delay: Base backoff delay in seconds; also bounds the jitter, so
            ``0.0`` retries with no wait (useful in tests).
    """
    async for attempt in AsyncRetrying(
        stop=stop_after_attempt(max(1, attempts)),
        wait=wait_exponential_jitter(initial=base_delay, max=30.0, jitter=base_delay),
        retry=retry_if_exception_type((httpx.TransportError, _TransientStatus)),
        reraise=True,
    ):
        with attempt:
            resp = await client.get(url)
            if resp.status_code in _RETRYABLE_STATUS:
                raise _TransientStatus(f"HTTP {resp.status_code} for {url}")
            resp.raise_for_status()
            return resp
    raise RuntimeError("unreachable")  # pragma: no cover


async def get_image_ids(
    batch_id: str,
    *,
    base_url: str = IIIF_URL,
    timeout: float = IIIF_TIMEOUT,
    attempts: int = 4,
    base_delay: float = 0.5,
) -> list[str]:
    """Fetch a IIIF manifest and extract image IDs.

    Args:
        batch_id: Volume/batch identifier (e.g. "C0074667").
        base_url: IIIF server base URL.
        timeout: HTTP request timeout in seconds.
        attempts: Maximum manifest-fetch attempts (transient failures retried).
        base_delay: Base backoff delay in seconds between retries.

    Returns:
        Sorted list of image IDs (e.g. ["C0074667_00001", "C0074667_00002", ...]).
    """
    manifest_url = f"{base_url}/arkis!{batch_id}/manifest"
    log.info("Fetching manifest: %s", manifest_url)

    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await fetch_with_retry(
            client, manifest_url, attempts=attempts, base_delay=base_delay
        )
        data = resp.json()

    image_ids = []
    for item in data.get("items", []):
        raw_id = item.get("id", "")
        if "!" in raw_id:
            image_id = raw_id.split("!")[1][:14].upper()
            image_ids.append(image_id)

    log.info("Found %d images in batch %s", len(image_ids), batch_id)
    return sorted(image_ids)


def build_image_url(
    image_id: str,
    *,
    base_url: str = IIIF_URL,
    query_params: str = IIIF_QUERY_PARAMS,
) -> str:
    """Build the IIIF image URL for a given image ID.

    Args:
        image_id: Image identifier (e.g. "C0074667_00001").
        base_url: IIIF server base URL.
        query_params: IIIF image API parameters (region/size/rotation/quality.format).

    Returns:
        Full image URL.
    """
    return f"{base_url}/arkis!{image_id}/{query_params}"


def file_extension(query_params: str = IIIF_QUERY_PARAMS) -> str:
    """Extract file extension from IIIF query params (e.g. '.jpg')."""
    return "." + query_params.rsplit(".", 1)[-1]
