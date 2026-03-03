"""Tests for tenant-level statistics endpoints."""

from __future__ import annotations

import httpx
import respx
from httpx import AsyncClient

HCP_BASE = "https://test.hcp.example.com:9090/mapi"


async def test_get_tenant_statistics(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{HCP_BASE}/tenants/my-tenant/statistics").mock(
        return_value=httpx.Response(200, json={"objectCount": 42})
    )
    resp = await client.get(
        "/api/v1/mapi/tenants/my-tenant/statistics", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["objectCount"] == 42
