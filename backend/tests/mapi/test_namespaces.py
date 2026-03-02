"""Tests for MAPI namespace endpoints."""

from __future__ import annotations

import httpx
import respx
from httpx import AsyncClient

HCP_BASE = "https://test.hcp.example.com:9090/mapi"
T = "my-tenant"
NS = "my-ns"
PREFIX = f"/api/v1/mapi/tenants/{T}/namespaces"
MAPI_PREFIX = f"{HCP_BASE}/tenants/{T}/namespaces"


# ── Namespace CRUD ────────────────────────────────────────────────────


async def test_list_namespaces(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}").mock(
        return_value=httpx.Response(200, json={"name": ["ns-a", "ns-b"]})
    )
    resp = await client.get(PREFIX, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == ["ns-a", "ns-b"]


async def test_create_namespace(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.put(f"{MAPI_PREFIX}").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.put(PREFIX, headers=auth_headers, json={"name": "new-ns"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "created"
    assert route.called


async def test_create_namespace_conflict(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.put(f"{MAPI_PREFIX}").mock(
        return_value=httpx.Response(409)
    )
    resp = await client.put(PREFIX, headers=auth_headers, json={"name": "existing-ns"})
    assert resp.status_code == 409


async def test_get_namespace(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}/{NS}").mock(
        return_value=httpx.Response(200, json={"name": NS, "hardQuota": "10GB"})
    )
    resp = await client.get(f"{PREFIX}/{NS}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == NS


async def test_get_namespace_not_found(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}/missing").mock(
        return_value=httpx.Response(404)
    )
    resp = await client.get(f"{PREFIX}/missing", headers=auth_headers)
    assert resp.status_code == 404


async def test_check_namespace(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.head(f"{MAPI_PREFIX}/{NS}").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.head(f"{PREFIX}/{NS}", headers=auth_headers)
    assert resp.status_code == 200


async def test_modify_namespace(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.post(f"{MAPI_PREFIX}/{NS}").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(
        f"{PREFIX}/{NS}", headers=auth_headers, json={"description": "updated"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"
    assert route.called


async def test_delete_namespace(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.delete(f"{MAPI_PREFIX}/{NS}").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.delete(f"{PREFIX}/{NS}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert route.called


# ── Compliance settings ──────────────────────────────────────────────


async def test_get_compliance(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}/{NS}/complianceSettings").mock(
        return_value=httpx.Response(200, json={"retentionDefault": "0"})
    )
    resp = await client.get(f"{PREFIX}/{NS}/complianceSettings", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["retentionDefault"] == "0"


async def test_modify_compliance(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.post(f"{MAPI_PREFIX}/{NS}/complianceSettings").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(
        f"{PREFIX}/{NS}/complianceSettings",
        headers=auth_headers,
        json={"retentionDefault": "30d"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"
    assert route.called


# ── Versioning settings ──────────────────────────────────────────────


async def test_get_versioning(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}/{NS}/versioningSettings").mock(
        return_value=httpx.Response(200, json={"enabled": True})
    )
    resp = await client.get(f"{PREFIX}/{NS}/versioningSettings", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["enabled"] is True


async def test_modify_versioning(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.post(f"{MAPI_PREFIX}/{NS}/versioningSettings").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(
        f"{PREFIX}/{NS}/versioningSettings",
        headers=auth_headers,
        json={"enabled": True, "pruneDays": 30},
    )
    assert resp.status_code == 200
    assert route.called


async def test_delete_versioning(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.delete(f"{MAPI_PREFIX}/{NS}/versioningSettings").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.delete(f"{PREFIX}/{NS}/versioningSettings", headers=auth_headers)
    assert resp.status_code == 200
    assert route.called


# ── Permissions ──────────────────────────────────────────────────────


async def test_get_permissions(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}/{NS}/permissions").mock(
        return_value=httpx.Response(200, json={"namespacePermission": []})
    )
    resp = await client.get(f"{PREFIX}/{NS}/permissions", headers=auth_headers)
    assert resp.status_code == 200


# ── Statistics ───────────────────────────────────────────────────────


async def test_get_ns_statistics(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}/{NS}/statistics").mock(
        return_value=httpx.Response(200, json={"objectCount": 100})
    )
    resp = await client.get(f"{PREFIX}/{NS}/statistics", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["objectCount"] == 100


# ── CORS ─────────────────────────────────────────────────────────────


async def test_get_ns_cors(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}/{NS}/cors").mock(
        return_value=httpx.Response(200, json={"cors": "<CORSRule/>"})
    )
    resp = await client.get(f"{PREFIX}/{NS}/cors", headers=auth_headers)
    assert resp.status_code == 200


async def test_set_ns_cors(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.put(f"{MAPI_PREFIX}/{NS}/cors").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.put(
        f"{PREFIX}/{NS}/cors", headers=auth_headers, json={"cors": "<CORSRule/>"},
    )
    assert resp.status_code == 200
    assert route.called


async def test_delete_ns_cors(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.delete(f"{MAPI_PREFIX}/{NS}/cors").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.delete(f"{PREFIX}/{NS}/cors", headers=auth_headers)
    assert resp.status_code == 200
    assert route.called


# ── Chargeback ───────────────────────────────────────────────────────


async def test_get_ns_chargeback(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}/{NS}/chargebackReport").mock(
        return_value=httpx.Response(200, json={"chargebackData": []})
    )
    resp = await client.get(f"{PREFIX}/{NS}/chargebackReport", headers=auth_headers)
    assert resp.status_code == 200


# ── Error propagation ────────────────────────────────────────────────


async def test_namespace_hcp_error(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{MAPI_PREFIX}").mock(
        return_value=httpx.Response(403)
    )
    resp = await client.get(PREFIX, headers=auth_headers)
    assert resp.status_code == 403
