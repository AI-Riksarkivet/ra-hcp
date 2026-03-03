"""Tests for MAPI health check report endpoints."""

from __future__ import annotations

import httpx
import respx
from httpx import AsyncClient

HCP_BASE = "https://test.hcp.example.com:9090/mapi"
PREFIX = "/api/v1/mapi/healthCheckReport"
MAPI_PREFIX = f"{HCP_BASE}/healthCheckReport"


async def test_get_health_check_status(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{MAPI_PREFIX}").mock(
        return_value=httpx.Response(200, json={"status": "IDLE"})
    )
    resp = await client.get(PREFIX, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "IDLE"


async def test_prepare_health_check(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    route = hcp_mock.post(f"{MAPI_PREFIX}/prepare").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(
        f"{PREFIX}/prepare",
        headers=auth_headers,
        json={"collectCurrent": True},
    )
    assert resp.status_code == 200
    assert route.called


async def test_download_health_check(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.post(f"{MAPI_PREFIX}/download").mock(
        return_value=httpx.Response(200, content=b"PK\x03\x04fakezipdata")
    )
    resp = await client.post(f"{PREFIX}/download", headers=auth_headers, json={})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/octet-stream"
    assert (
        resp.headers["content-disposition"]
        == "attachment; filename=hcp-health-check.zip"
    )


async def test_cancel_health_check(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    route = hcp_mock.post(f"{HCP_BASE}/healthCheckReport").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(f"{PREFIX}/cancel", headers=auth_headers)
    assert resp.status_code == 200
    assert route.called


async def test_health_check_hcp_error(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{MAPI_PREFIX}").mock(return_value=httpx.Response(403))
    resp = await client.get(PREFIX, headers=auth_headers)
    assert resp.status_code == 403
