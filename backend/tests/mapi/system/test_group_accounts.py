"""Tests for system-level group account endpoints."""

from __future__ import annotations

import httpx
import respx
from httpx import AsyncClient

HCP_BASE = "https://test.hcp.example.com:9090/mapi"
S_PREFIX = "/api/v1/mapi/groupAccounts"
S_MAPI = f"{HCP_BASE}/groupAccounts"


async def test_list_system_groups(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{S_MAPI}").mock(
        return_value=httpx.Response(200, json={"groupname": ["admins"]})
    )
    resp = await client.get(S_PREFIX, headers=auth_headers)
    assert resp.status_code == 200


async def test_get_system_group(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.get(f"{S_MAPI}/admins").mock(
        return_value=httpx.Response(200, json={"groupname": "admins"})
    )
    resp = await client.get(f"{S_PREFIX}/admins", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["groupname"] == "admins"


async def test_check_system_group(
    client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router
):
    hcp_mock.head(f"{S_MAPI}/admins").mock(return_value=httpx.Response(200))
    resp = await client.head(f"{S_PREFIX}/admins", headers=auth_headers)
    assert resp.status_code == 200
