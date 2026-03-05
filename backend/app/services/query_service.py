"""HCP Metadata Query API HTTP client.

Handles POST requests to the tenant query endpoint for object and
operation metadata searches.
"""

from __future__ import annotations

import base64
import hashlib
import json
import logging
from typing import Any, Optional

import httpx
from fastapi import HTTPException

from app.core.config import MapiSettings
from app.core.tenant_routing import query_url_for_tenant
from app.schemas.query import (
    ObjectQuery,
    ObjectQueryRequest,
    ObjectQueryResponse,
    OperationQuery,
    OperationQueryRequest,
    OperationQueryResponse,
)

logger = logging.getLogger(__name__)


class QueryService:
    """Low-level HTTP client for the HCP Metadata Query API."""

    def __init__(self, settings: MapiSettings):
        self.settings = settings
        self._client: Optional[httpx.AsyncClient] = None

    # ── Authentication ─────────────────────────────────────────────────

    def _get_auth_header(
        self,
        username: str,
        password: str,
        auth_type: Optional[str] = None,
    ) -> str:
        at = auth_type or self.settings.hcp_auth_type

        if at == "ad":
            return f"AD {username}:{password}"
        user_b64 = base64.b64encode(username.encode()).decode()
        pass_md5 = hashlib.md5(password.encode()).hexdigest()
        return f"HCP {user_b64}:{pass_md5}"

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

    # ── Query execution ────────────────────────────────────────────────

    async def _post_query(
        self,
        tenant: str,
        body: dict[str, Any],
        *,
        username: str,
        password: str,
        auth_type: Optional[str] = None,
    ) -> dict:
        url = query_url_for_tenant(tenant, self.settings.hcp_domain)
        if not url:
            raise HTTPException(
                status_code=400,
                detail="HCP domain not configured — cannot build query URL",
            )

        client = await self._get_client()
        headers = {
            "Authorization": self._get_auth_header(username, password, auth_type),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

        try:
            resp = await client.post(url, headers=headers, content=json.dumps(body))
        except httpx.TimeoutException:
            logger.error("Query API timeout: POST %s", url)
            raise HTTPException(status_code=504, detail="HCP query timed out")
        except httpx.ConnectError:
            logger.error("Query API unreachable: POST %s", url)
            raise HTTPException(status_code=502, detail="HCP query unreachable")
        except httpx.TransportError as exc:
            logger.error("Query API transport error: POST %s — %s", url, exc)
            raise HTTPException(status_code=502, detail="HCP query connection error")

        if resp.status_code != 200:
            hcp_msg = resp.headers.get("x-hcp-errormessage", "")
            detail = hcp_msg or resp.text or f"HCP query returned {resp.status_code}"
            raise HTTPException(status_code=resp.status_code, detail=detail)

        data = resp.json()
        # HCP wraps responses in {"queryResult": {...}} — unwrap it.
        if "queryResult" in data:
            data = data["queryResult"]
        return data

    async def object_query(
        self,
        tenant: str,
        query: ObjectQuery,
        *,
        username: str,
        password: str,
        auth_type: Optional[str] = None,
    ) -> ObjectQueryResponse:
        request_body = ObjectQueryRequest(object=query)
        data = await self._post_query(
            tenant,
            request_body.model_dump(by_alias=True, exclude_none=True),
            username=username,
            password=password,
            auth_type=auth_type,
        )
        return ObjectQueryResponse.model_validate(data)

    async def operation_query(
        self,
        tenant: str,
        query: OperationQuery,
        *,
        username: str,
        password: str,
        auth_type: Optional[str] = None,
    ) -> OperationQueryResponse:
        request_body = OperationQueryRequest(operation=query)
        data = await self._post_query(
            tenant,
            request_body.model_dump(by_alias=True, exclude_none=True),
            username=username,
            password=password,
            auth_type=auth_type,
        )
        return OperationQueryResponse.model_validate(data)


class AuthenticatedQueryService(QueryService):
    """Wrapper that injects per-request credentials from the JWT."""

    def __init__(
        self,
        base: QueryService,
        username: str,
        password: str,
    ):
        self.settings = base.settings
        self._base = base
        self._username = username
        self._password = password

    async def _get_client(self):
        return await self._base._get_client()

    async def _post_query(self, tenant, body, **kwargs):
        kwargs["username"] = self._username
        kwargs["password"] = self._password
        return await self._base._post_query(tenant, body, **kwargs)

    async def close(self):
        pass  # base owns the client
