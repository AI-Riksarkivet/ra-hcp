"""Tests for MAPI log endpoints (status, mark, cancel, prepare, download)."""

from __future__ import annotations

import httpx
import respx
from httpx import AsyncClient

HCP_BASE = "https://test.hcp.example.com:9090/mapi"
PREFIX = "/api/v1/mapi/logs"
MAPI_PREFIX = f"{HCP_BASE}/logs"


async def test_get_log_status(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{MAPI_PREFIX}").mock(
        return_value=httpx.Response(200, json={"status": "IDLE"})
    )
    resp = await client.get(PREFIX, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "IDLE"


async def test_log_mark(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    route = hcp_mock.post(f"{MAPI_PREFIX}").mock(return_value=httpx.Response(200))
    resp = await client.post(PREFIX, headers=auth_headers, params={"mark": "deploy-v2"})
    assert resp.status_code == 200
    assert route.called


async def test_log_cancel(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    route = hcp_mock.post(f"{MAPI_PREFIX}").mock(return_value=httpx.Response(200))
    resp = await client.post(PREFIX, headers=auth_headers, params={"cancel": True})
    assert resp.status_code == 200
    assert route.called


async def test_prepare_logs(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    route = hcp_mock.post(f"{MAPI_PREFIX}/prepare").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(
        f"{PREFIX}/prepare",
        headers=auth_headers,
        json={"startDate": "2024-01-01"},
    )
    assert resp.status_code == 200
    assert route.called


async def test_download_logs(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.post(f"{MAPI_PREFIX}/download").mock(
        return_value=httpx.Response(200, content=b"PK\x03\x04fakezipdata")
    )
    resp = await client.post(f"{PREFIX}/download", headers=auth_headers, json={})
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/octet-stream"
    assert resp.headers["content-disposition"] == "attachment; filename=hcp-logs.zip"


async def test_logs_hcp_error(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{MAPI_PREFIX}").mock(return_value=httpx.Response(403))
    resp = await client.get(PREFIX, headers=auth_headers)
    assert resp.status_code == 403
