"""Tests for namespace statistics endpoints."""

from __future__ import annotations

import httpx
import respx
from httpx import AsyncClient

HCP_BASE = "https://test.hcp.example.com:9090/mapi"
T = "my-tenant"
NS = "my-ns"
PREFIX = f"/api/v1/mapi/tenants/{T}/namespaces"
MAPI_PREFIX = f"{HCP_BASE}/tenants/{T}/namespaces"


async def test_get_ns_statistics(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{MAPI_PREFIX}/{NS}/statistics").mock(
        return_value=httpx.Response(200, json={"objectCount": 100})
    )
    resp = await client.get(f"{PREFIX}/{NS}/statistics", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["objectCount"] == 100


async def test_get_ns_chargeback(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{MAPI_PREFIX}/{NS}/chargebackReport").mock(
        return_value=httpx.Response(200, json={"chargebackData": []})
    )
    resp = await client.get(f"{PREFIX}/{NS}/chargebackReport", headers=auth_headers)
    assert resp.status_code == 200
