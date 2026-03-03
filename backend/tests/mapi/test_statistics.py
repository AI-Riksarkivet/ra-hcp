"""Tests for MAPI statistics endpoints (node and service)."""

from __future__ import annotations

import httpx
import respx
from httpx import AsyncClient

HCP_BASE = "https://test.hcp.example.com:9090/mapi"


async def test_get_node_statistics(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{HCP_BASE}/nodes/statistics").mock(
        return_value=httpx.Response(200, json={"nodeCount": 4})
    )
    resp = await client.get("/api/v1/mapi/nodes/statistics", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["nodeCount"] == 4


async def test_get_node_statistics_hcp_error(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{HCP_BASE}/nodes/statistics").mock(return_value=httpx.Response(403))
    resp = await client.get("/api/v1/mapi/nodes/statistics", headers=auth_headers)
    assert resp.status_code == 403


async def test_get_service_statistics(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{HCP_BASE}/services/statistics").mock(
        return_value=httpx.Response(200, json={"serviceCount": 5})
    )
    resp = await client.get("/api/v1/mapi/services/statistics", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["serviceCount"] == 5


async def test_get_service_statistics_hcp_error(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{HCP_BASE}/services/statistics").mock(
        return_value=httpx.Response(403)
    )
    resp = await client.get("/api/v1/mapi/services/statistics", headers=auth_headers)
    assert resp.status_code == 403
