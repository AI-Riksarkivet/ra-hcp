"""Tests for MAPI retention class endpoints."""

from __future__ import annotations

import httpx
import respx
from httpx import AsyncClient

HCP_BASE = "https://test.hcp.example.com:9090/mapi"
T = "my-tenant"
NS = "my-ns"
RC = "my-retention-class"
PREFIX = f"/api/v1/mapi/tenants/{T}/namespaces/{NS}/retentionClasses"
MAPI_PREFIX = f"{HCP_BASE}/tenants/{T}/namespaces/{NS}/retentionClasses"


async def test_list_retention_classes(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{MAPI_PREFIX}").mock(
        return_value=httpx.Response(200, json={"name": ["rc1", "rc2"]})
    )
    resp = await client.get(PREFIX, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == ["rc1", "rc2"]


async def test_create_retention_class(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    route = hcp_mock.put(f"{MAPI_PREFIX}").mock(return_value=httpx.Response(200))
    resp = await client.put(
        PREFIX,
        headers=auth_headers,
        json={"name": RC, "value": "30d"},
    )
    assert resp.status_code == 200
    assert route.called


async def test_get_retention_class(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{MAPI_PREFIX}/{RC}").mock(
        return_value=httpx.Response(200, json={"name": RC, "value": "30d"})
    )
    resp = await client.get(f"{PREFIX}/{RC}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == RC


async def test_get_retention_class_not_found(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{MAPI_PREFIX}/missing").mock(return_value=httpx.Response(404))
    resp = await client.get(f"{PREFIX}/missing", headers=auth_headers)
    assert resp.status_code == 404


async def test_check_retention_class(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.head(f"{MAPI_PREFIX}/{RC}").mock(return_value=httpx.Response(200))
    resp = await client.head(f"{PREFIX}/{RC}", headers=auth_headers)
    assert resp.status_code == 200


async def test_update_retention_class(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    route = hcp_mock.post(f"{MAPI_PREFIX}/{RC}").mock(return_value=httpx.Response(200))
    resp = await client.post(
        f"{PREFIX}/{RC}",
        headers=auth_headers,
        json={"value": "60d"},
    )
    assert resp.status_code == 200
    assert route.called


async def test_delete_retention_class(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    route = hcp_mock.delete(f"{MAPI_PREFIX}/{RC}").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.delete(f"{PREFIX}/{RC}", headers=auth_headers)
    assert resp.status_code == 200
    assert route.called
