"""HCPClient — async HTTP client with auth, retry, and auto-refresh."""

from __future__ import annotations

import asyncio
import logging
from types import TracebackType
from typing import TYPE_CHECKING, Any

import httpx

from rahcp_client.config import HCPSettings
from rahcp_client.errors import (
    AuthenticationError,
    RetryableError,
    error_for_status,
)

if TYPE_CHECKING:
    from rahcp_client.mapi import MapiOps
    from rahcp_client.s3 import S3Ops

log = logging.getLogger(__name__)

_RETRYABLE_STATUSES = frozenset({408, 429, 500, 503, 504})


class HCPClient:
    """Async HTTP client for the HCP Unified API.

    Usage::

        async with HCPClient.from_env() as hcp:
            buckets = await hcp.s3.list_objects("bucket", "prefix/")
            ns = await hcp.mapi.list_namespaces("tenant")
    """

    def __init__(
        self,
        endpoint: str = "http://localhost:8000/api/v1",
        username: str = "",
        password: str = "",
        tenant: str | None = None,
        *,
        timeout: float = 30.0,
        max_retries: int = 4,
        retry_base_delay: float = 1.0,
        multipart_threshold: int = 64 * 1024 * 1024,
        multipart_chunk: int = 16 * 1024 * 1024,
        verify_ssl: bool = True,
    ) -> None:
        self.endpoint = endpoint.rstrip("/")
        self.username = username
        self.password = password
        self.tenant = tenant
        self.max_retries = max_retries
        self.retry_base_delay = retry_base_delay
        self.multipart_threshold = multipart_threshold
        self.multipart_chunk = multipart_chunk
        self.verify_ssl = verify_ssl

        self._http = httpx.AsyncClient(
            base_url=self.endpoint,
            timeout=timeout,
        )
        self._token: str | None = None
        self._s3: S3Ops | None = None
        self._mapi: MapiOps | None = None

    @property
    def token(self) -> str | None:
        """The current bearer token (set after login)."""
        return self._token

    @classmethod
    def from_env(cls) -> HCPClient:
        """Create a client configured from ``HCP_*`` environment variables."""
        settings = HCPSettings()
        return cls(
            endpoint=settings.endpoint,
            username=settings.username,
            password=settings.password,
            tenant=settings.tenant,
            timeout=settings.timeout,
            max_retries=settings.max_retries,
            retry_base_delay=settings.retry_base_delay,
            multipart_threshold=settings.multipart_threshold,
            multipart_chunk=settings.multipart_chunk,
            verify_ssl=settings.verify_ssl,
        )

    # ── Context manager ─────────────────────────────────────────────

    async def __aenter__(self) -> HCPClient:
        try:
            if self.username and self.password:
                await self._login()
        except Exception:
            await self._http.aclose()
            raise
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        await self._http.aclose()

    # ── Operation namespaces ────────────────────────────────────────

    @property
    def s3(self) -> S3Ops:
        """S3 data-plane operations."""
        if self._s3 is None:
            from rahcp_client.s3 import S3Ops

            self._s3 = S3Ops(self)
        return self._s3

    @property
    def mapi(self) -> MapiOps:
        """MAPI management-plane operations."""
        if self._mapi is None:
            from rahcp_client.mapi import MapiOps

            self._mapi = MapiOps(self)
        return self._mapi

    # ── Auth ────────────────────────────────────────────────────────

    async def _login(self) -> None:
        """Authenticate and store the bearer token."""
        form: dict[str, str] = {"username": self.username, "password": self.password}
        if self.tenant:
            form["tenant"] = self.tenant
        response = await self._http.post("/auth/token", data=form)
        if response.status_code != 200:
            raise AuthenticationError(
                f"Login failed: {response.status_code} {response.text}",
                status_code=response.status_code,
            )
        data = response.json()
        self._token = data["access_token"]
        log.debug("Authenticated as %s", self.username)

    def _auth_headers(self) -> dict[str, str]:
        """Return authorization headers if a token is available."""
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}

    # ── Core request with retry + auto-refresh ──────────────────────

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: Any = None,
        data: Any = None,
        content: bytes | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """Send an HTTP request with retry and automatic 401 refresh.

        This is the internal workhorse — operation classes (S3Ops, MapiOps)
        delegate here.
        """
        merged_headers = {**self._auth_headers(), **(headers or {})}
        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = await self._http.request(
                    method,
                    path,
                    params=params,
                    json=json,
                    data=data,
                    content=content,
                    headers=merged_headers,
                )
            except httpx.TransportError as exc:
                last_error = RetryableError(str(exc))
                await self._backoff(attempt)
                continue

            # Auto-refresh on 401
            if response.status_code == 401 and self.username and attempt == 0:
                log.debug("Token expired, refreshing...")
                await self._login()
                merged_headers = {**self._auth_headers(), **(headers or {})}
                continue

            # Retry on transient status codes
            if response.status_code in _RETRYABLE_STATUSES:
                last_error = error_for_status(response.status_code, response.text)
                if attempt < self.max_retries:
                    await self._backoff(attempt)
                    continue

            # Success or non-retryable error
            if response.status_code >= 400:
                raise error_for_status(response.status_code, response.text)

            return response

        # Exhausted all retries
        if last_error:
            raise last_error
        raise RetryableError("All retries exhausted")  # pragma: no cover

    async def _backoff(self, attempt: int) -> None:
        """Exponential backoff: base * 2^attempt."""
        delay = self.retry_base_delay * (2**attempt)
        log.debug("Retry attempt %d, backing off %.1fs", attempt + 1, delay)
        await asyncio.sleep(delay)
