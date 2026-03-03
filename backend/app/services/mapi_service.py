"""HCP Management API HTTP client.

Handles authentication (HCP token + AD), request building,
and communication with the HCP system.
"""

from __future__ import annotations

import base64
import hashlib
import json
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import logging

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from app.core.config import MapiSettings

logger = logging.getLogger(__name__)


class MapiService:
    """Low-level HTTP client for the HCP management API."""

    def __init__(self, settings: MapiSettings):
        self.settings = settings
        self._client: Optional[httpx.AsyncClient] = None

    # ── Authentication ─────────────────────────────────────────────────

    def _build_hcp_auth_token(self, username: str, password: str) -> str:
        """Build HCP authentication token: base64(user):md5(password)."""
        user_b64 = base64.b64encode(username.encode()).decode()
        pass_md5 = hashlib.md5(password.encode()).hexdigest()
        return f"{user_b64}:{pass_md5}"

    def _get_auth_header(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        auth_type: Optional[str] = None,
    ) -> str:
        """Return the Authorization header value."""
        u = username or self.settings.hcp_username
        p = password or self.settings.hcp_password
        at = auth_type or self.settings.hcp_auth_type

        if at == "ad":
            return f"AD {u}:{p}"
        else:
            token = self._build_hcp_auth_token(u, p)
            return f"HCP {token}"

    # ── Client lifecycle ───────────────────────────────────────────────

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                verify=self.settings.hcp_verify_ssl,
                timeout=self.settings.hcp_timeout,
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    # ── URL building ───────────────────────────────────────────────────

    def _build_url(
        self,
        path: str,
        host: Optional[str] = None,
        query: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build full URL for a MAPI request."""
        h = host or self.settings.hcp_host
        port = self.settings.hcp_port
        url = f"https://{h}:{port}/mapi{path}"
        if query:
            filtered = {k: v for k, v in query.items() if v is not None}
            if filtered:
                url += "?" + urlencode(filtered, doseq=True)
        return url

    # ── Generic request ────────────────────────────────────────────────

    async def request(
        self,
        method: str,
        path: str,
        *,
        host: Optional[str] = None,
        body: Optional[Any] = None,
        query: Optional[Dict[str, Any]] = None,
        content_type: str = "application/json",
        accept: str = "application/json",
        username: Optional[str] = None,
        password: Optional[str] = None,
        auth_type: Optional[str] = None,
        raw_body: Optional[bytes] = None,
    ) -> httpx.Response:
        """Execute an HTTP request against the HCP management API."""
        client = await self._get_client()
        url = self._build_url(path, host=host, query=query)

        headers = {
            "Authorization": self._get_auth_header(username, password, auth_type),
            "Accept": accept,
        }

        content = None
        if raw_body is not None:
            content = raw_body
            headers["Content-Type"] = content_type
        elif body is not None:
            if isinstance(body, BaseModel):
                content = body.model_dump_json(exclude_none=True).encode()
            elif isinstance(body, dict):
                content = json.dumps(body).encode()
            elif isinstance(body, str):
                content = body.encode()
            else:
                content = body
            headers["Content-Type"] = content_type

        try:
            resp = await client.request(method, url, headers=headers, content=content)
        except httpx.TimeoutException:
            logger.error("MAPI timeout: %s %s", method, url)
            raise HTTPException(status_code=504, detail="HCP timed out")
        except httpx.ConnectError:
            logger.error("MAPI unreachable: %s %s", method, url)
            raise HTTPException(status_code=502, detail="HCP unreachable")
        except httpx.TransportError as exc:
            logger.error("MAPI transport error: %s %s — %s", method, url, exc)
            raise HTTPException(status_code=502, detail="HCP connection error")
        return resp

    # ── Connectivity check ─────────────────────────────────────────────

    async def ping(self) -> bool:
        """Return True if HCP is reachable, False otherwise.

        Sends an unauthenticated HEAD — any response (including 401/403)
        proves the network path is up.  Only transport errors mean
        "unreachable".
        """
        try:
            client = await self._get_client()
            url = self._build_url("/tenants")
            await client.head(url, timeout=5.0)
            return True
        except Exception:
            return False

    # ── Convenience methods ────────────────────────────────────────────

    async def get(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("GET", path, **kwargs)

    async def put(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("PUT", path, **kwargs)

    async def post(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("POST", path, **kwargs)

    async def delete(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("DELETE", path, **kwargs)

    async def head(self, path: str, **kwargs) -> httpx.Response:
        return await self.request("HEAD", path, **kwargs)

    # ── High-level helpers (raise on error) ───────────────────────────

    async def fetch_json(
        self, path: str, *, resource: str = "resource", **kwargs
    ) -> dict:
        """GET + raise_for_hcp_status + parse JSON. One-liner for read endpoints."""
        from app.api.errors import raise_for_hcp_status, parse_json_response

        resp = await self.get(path, **kwargs)
        raise_for_hcp_status(resp, resource)
        return parse_json_response(resp)

    async def send(
        self, method: str, path: str, *, resource: str = "resource", **kwargs
    ) -> httpx.Response:
        """request + raise_for_hcp_status. Returns the validated response."""
        from app.api.errors import raise_for_hcp_status

        resp = await self.request(method, path, **kwargs)
        raise_for_hcp_status(resp, resource)
        return resp


class AuthenticatedMapiService(MapiService):
    """Wrapper that injects per-request credentials from the JWT."""

    def __init__(
        self,
        base: MapiService,
        username: str,
        password: str,
        host: Optional[str] = None,
    ):
        self.settings = base.settings
        self._base = base
        self._username = username
        self._password = password
        self._host = host

    async def _get_client(self):
        return await self._base._get_client()

    async def request(
        self, method, path, *, username=None, password=None, host=None, **kwargs
    ):
        return await self._base.request(
            method,
            path,
            username=username or self._username,
            password=password or self._password,
            host=host or self._host,
            **kwargs,
        )

    async def close(self):
        pass  # base owns the client
