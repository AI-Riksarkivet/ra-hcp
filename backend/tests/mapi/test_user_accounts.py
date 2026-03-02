"""Tests for MAPI user account endpoints (tenant-level and system-level)."""

from __future__ import annotations

import httpx
import respx
from httpx import AsyncClient

HCP_BASE = "https://test.hcp.example.com:9090/mapi"
T = "my-tenant"
USER = "jdoe"
T_PREFIX = f"/api/v1/mapi/tenants/{T}/userAccounts"
T_MAPI = f"{HCP_BASE}/tenants/{T}/userAccounts"
S_PREFIX = "/api/v1/mapi/userAccounts"
S_MAPI = f"{HCP_BASE}/userAccounts"


# ═══════════════════════════════════════════════════════════════════════
#  Tenant-level user accounts
# ═══════════════════════════════════════════════════════════════════════


async def test_list_user_accounts(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{T_MAPI}").mock(
        return_value=httpx.Response(200, json={"userAccount": [{"username": "u1"}]})
    )
    resp = await client.get(T_PREFIX, headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["userAccount"][0]["username"] == "u1"


async def test_create_user_account(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.put(f"{T_MAPI}").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.put(
        T_PREFIX,
        headers=auth_headers,
        params={"password": "s3cret"},
        json={
            "username": USER,
            "fullName": "John Doe",
            "localAuthentication": True,
            "enabled": True,
            "forcePasswordChange": False,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "created"
    assert route.called


async def test_get_user_account(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{T_MAPI}/{USER}").mock(
        return_value=httpx.Response(200, json={"username": USER, "fullName": "John Doe"})
    )
    resp = await client.get(f"{T_PREFIX}/{USER}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == USER


async def test_get_user_account_not_found(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{T_MAPI}/nobody").mock(
        return_value=httpx.Response(404)
    )
    resp = await client.get(f"{T_PREFIX}/nobody", headers=auth_headers)
    assert resp.status_code == 404


async def test_check_user_account(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.head(f"{T_MAPI}/{USER}").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.head(f"{T_PREFIX}/{USER}", headers=auth_headers)
    assert resp.status_code == 200


async def test_modify_user_account(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.post(f"{T_MAPI}/{USER}").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(
        f"{T_PREFIX}/{USER}", headers=auth_headers, json={"enabled": False},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"
    assert route.called


async def test_delete_user_account(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.delete(f"{T_MAPI}/{USER}").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.delete(f"{T_PREFIX}/{USER}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert route.called


async def test_change_password(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.post(f"{T_MAPI}/{USER}/changePassword").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(
        f"{T_PREFIX}/{USER}/changePassword",
        headers=auth_headers,
        json={"newPassword": "newpass123"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "password_changed"
    assert route.called


async def test_get_user_data_perms(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{T_MAPI}/{USER}/dataAccessPermissions").mock(
        return_value=httpx.Response(200, json={"namespacePermission": []})
    )
    resp = await client.get(f"{T_PREFIX}/{USER}/dataAccessPermissions", headers=auth_headers)
    assert resp.status_code == 200


async def test_modify_user_data_perms(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.post(f"{T_MAPI}/{USER}/dataAccessPermissions").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(
        f"{T_PREFIX}/{USER}/dataAccessPermissions",
        headers=auth_headers,
        json={"namespacePermission": []},
    )
    assert resp.status_code == 200
    assert route.called


# ═══════════════════════════════════════════════════════════════════════
#  System-level user accounts
# ═══════════════════════════════════════════════════════════════════════


async def test_list_system_users(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{S_MAPI}").mock(
        return_value=httpx.Response(200, json={"username": ["admin", "monitor"]})
    )
    resp = await client.get(S_PREFIX, headers=auth_headers)
    assert resp.status_code == 200


async def test_get_system_user(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.get(f"{S_MAPI}/admin").mock(
        return_value=httpx.Response(200, json={"username": "admin"})
    )
    resp = await client.get(f"{S_PREFIX}/admin", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["username"] == "admin"


async def test_check_system_user(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    hcp_mock.head(f"{S_MAPI}/admin").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.head(f"{S_PREFIX}/admin", headers=auth_headers)
    assert resp.status_code == 200


async def test_modify_system_user_password(client: AsyncClient, auth_headers: dict, hcp_mock: respx.Router):
    route = hcp_mock.post(f"{S_MAPI}/admin").mock(
        return_value=httpx.Response(200)
    )
    resp = await client.post(
        f"{S_PREFIX}/admin", headers=auth_headers, params={"password": "newpass"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"
    assert route.called
