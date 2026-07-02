"""Minimal async Transkribus TRP REST client (httpx + tenacity).

Reimplements just the handful of read calls an export needs — login, list
documents, list pages, fetch transcript/image bytes — against the Transkribus
REST API. Auth is a ``JSESSIONID`` cookie obtained from ``/auth/login``.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from types import TracebackType

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

from rahcp_transkribus.config import (
    TRANSKRIBUS_TIMEOUT,
    TRANSKRIBUS_URL,
    resolve_verify_ssl,
)
from rahcp_transkribus.errors import TranskribusAuthError, TranskribusError
from rahcp_transkribus.models import Document, Page

log = logging.getLogger(__name__)

# Transient HTTP statuses worth retrying. Other 4xx (e.g. 404) are terminal.
_RETRYABLE_STATUS = frozenset({408, 425, 429, 500, 502, 503, 504})


class _TransientStatus(Exception):
    """Internal marker: a retryable HTTP status code was returned."""


def _extract_session_id(xml_text: str) -> str:
    """Pull the ``sessionId`` element out of a login response (namespace-agnostic)."""
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise TranskribusAuthError(f"malformed login response: {exc}") from exc
    for el in root.iter():
        tag = el.tag.rsplit("}", 1)[-1]
        if tag == "sessionId" and el.text and el.text.strip():
            return el.text.strip()
    raise TranskribusAuthError("login response contained no sessionId")


class TranskribusClient:
    """Async client for the Transkribus TRP REST API.

    Use as an async context manager — it logs in on entry and out on exit::

        async with TranskribusClient(user, pw) as client:
            docs = await client.list_docs(collection_id)

    Args:
        username: Transkribus login (email).
        password: Transkribus password.
        base_url: TRP REST base URL.
        timeout: Per-request timeout in seconds.
        verify_ssl: TLS verification; ``None`` honours ``SKIP_SSL_VERIFY``.
        max_attempts: Max attempts per request (transient failures retried).
        retry_base_delay: Base backoff delay in seconds between retries.
    """

    def __init__(
        self,
        username: str,
        password: str,
        *,
        base_url: str = TRANSKRIBUS_URL,
        timeout: float = TRANSKRIBUS_TIMEOUT,
        verify_ssl: bool | None = None,
        max_attempts: int = 4,
        retry_base_delay: float = 0.5,
    ) -> None:
        self._username = username
        self._password = password
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._verify_ssl = resolve_verify_ssl(verify_ssl)
        self._max_attempts = max_attempts
        self._retry_base_delay = retry_base_delay
        self._client: httpx.AsyncClient | None = None
        self._session_id: str | None = None

    @property
    def base_url(self) -> str:
        """The TRP REST base URL (no trailing slash)."""
        return self._base_url

    @property
    def session_id(self) -> str | None:
        """The active ``JSESSIONID``, or ``None`` before login."""
        return self._session_id

    # ── Lifecycle ─────────────────────────────────────────────────

    async def __aenter__(self) -> TranskribusClient:
        self._client = httpx.AsyncClient(
            base_url=self._base_url,
            timeout=self._timeout,
            verify=self._verify_ssl,
            follow_redirects=True,
        )
        try:
            await self._login()
        except BaseException:
            # __aexit__ is not called when __aenter__ raises — close here so a
            # failed login (bad credentials, network) never leaks the client.
            await self._client.aclose()
            self._client = None
            raise
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self._client is None:
            return
        try:
            await self._logout()
        finally:
            await self._client.aclose()
            self._client = None
            self._session_id = None

    def _require_client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise TranskribusError(
                "TranskribusClient must be used as an async context manager"
            )
        return self._client

    async def _login(self) -> None:
        client = self._require_client()
        try:
            resp = await client.post(
                "/auth/login",
                data={"user": self._username, "pw": self._password},
            )
        except httpx.HTTPError as exc:
            raise TranskribusAuthError(f"login request failed: {exc}") from exc
        if resp.status_code in (401, 403):
            raise TranskribusAuthError("invalid Transkribus credentials")
        if resp.status_code >= 400:
            raise TranskribusAuthError(
                f"login failed: HTTP {resp.status_code} {resp.reason_phrase}"
            )
        self._session_id = _extract_session_id(resp.text)
        client.cookies.set("JSESSIONID", self._session_id)
        log.info("Authenticated with Transkribus as %s", self._username)

    async def _logout(self) -> None:
        client = self._require_client()
        try:
            await client.post("/auth/logout")
        except httpx.HTTPError:
            log.debug("Transkribus logout failed", exc_info=True)

    # ── Requests ──────────────────────────────────────────────────

    async def _request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Send a request, retrying transient failures with backoff + jitter."""
        client = self._require_client()
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(max(1, self._max_attempts)),
            wait=wait_exponential_jitter(
                initial=self._retry_base_delay,
                max=30.0,
                jitter=self._retry_base_delay,
            ),
            retry=retry_if_exception_type((httpx.TransportError, _TransientStatus)),
            reraise=True,
        ):
            with attempt:
                resp = await client.request(method, url, **kwargs)
                if resp.status_code in _RETRYABLE_STATUS:
                    raise _TransientStatus(f"HTTP {resp.status_code} for {url}")
                resp.raise_for_status()
                return resp
        raise RuntimeError("unreachable")  # pragma: no cover

    # ── API surface ───────────────────────────────────────────────

    async def list_docs(self, collection_id: int) -> list[Document]:
        """List all documents in a collection."""
        resp = await self._request(
            "GET",
            f"/collections/{collection_id}/list",
            params={"index": 0, "nValues": 0},
        )
        return [Document.model_validate(d) for d in resp.json()]

    async def get_pages(
        self,
        collection_id: int,
        doc_id: int,
        *,
        status: str | None = None,
        skip_pages_with_missing_status: bool = False,
        pages: str | None = None,
    ) -> list[Page]:
        """List pages of a document, filtered server-side by transcript status.

        Args:
            collection_id: Collection ID.
            doc_id: Document ID.
            status: Transcript status filter (e.g. ``"GT"``, ``"FINAL"``); each
                returned page's ``tsList`` is restricted to versions with it.
            skip_pages_with_missing_status: Omit pages that have no transcript
                with ``status``.
            pages: Optional page-range string (e.g. ``"1-5,8"``).
        """
        params: dict[str, object] = {
            "skipPagesWithMissingStatus": skip_pages_with_missing_status
        }
        if status:
            params["status"] = status
        if pages:
            params["pages"] = pages
        resp = await self._request(
            "GET", f"/collections/{collection_id}/{doc_id}/pages", params=params
        )
        return [Page.model_validate(p) for p in resp.json()]

    async def get_transcript_text(
        self, collection_id: int, doc_id: int, page_nr: int
    ) -> bytes:
        """Fetch the current PAGE-XML transcript for a page via the ``/text`` endpoint."""
        resp = await self._request(
            "GET", f"/collections/{collection_id}/{doc_id}/{page_nr}/text"
        )
        return resp.content

    async def fetch_bytes(self, url: str) -> bytes:
        """GET raw bytes from a URL (absolute or base-relative).

        Used for page images and transcript file-store URLs. The session cookie
        rides along automatically for same-host (REST) URLs and is harmlessly
        ignored by the file store.
        """
        resp = await self._request("GET", url)
        return resp.content
