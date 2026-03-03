"""User account routes – tenant-level and system-level."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.user_account import (
    UserAccountCreate,
    UserAccountUpdate,
    UpdatePasswordRequest,
)
from app.schemas.common import ListQueryParams, DataAccessPermissions

router = APIRouter(tags=["User Accounts"])

# ═══════════════════════════════════════════════════════════════════════
#  Tenant-level user accounts
# ═══════════════════════════════════════════════════════════════════════

T_PREFIX = "/tenants/{tenant_name}/userAccounts"


@router.get(T_PREFIX)
async def list_user_accounts(
    tenant_name: str,
    qp: ListQueryParams = Depends(),
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    q: dict = {"verbose": str(verbose).lower()}
    if qp.offset is not None:
        q["offset"] = qp.offset
    if qp.count is not None:
        q["count"] = qp.count
    if qp.sortType:
        q["sortType"] = qp.sortType
    if qp.sortOrder:
        q["sortOrder"] = qp.sortOrder
    if qp.filterType:
        q["filterType"] = qp.filterType
    if qp.filterString:
        q["filterString"] = qp.filterString
    resp = await hcp.get(f"/tenants/{tenant_name}/userAccounts", query=q)
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(T_PREFIX)
async def create_user_account(
    tenant_name: str,
    body: UserAccountCreate,
    password: str = Query(...),
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.put(
        f"/tenants/{tenant_name}/userAccounts",
        body=body,
        query={"password": password},
    )
    raise_for_hcp_status(resp, "user account")
    return {"status": "created"}


@router.post(T_PREFIX)
async def reset_passwords(
    tenant_name: str,
    resetPasswords: str = Query(...),
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/userAccounts",
        body={},
        query={"resetPasswords": resetPasswords},
    )
    raise_for_hcp_status(resp)
    return {"status": "passwords_reset"}


@router.get(T_PREFIX + "/{username}")
async def get_user_account(
    tenant_name: str,
    username: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/userAccounts/{username}",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp, f"user '{username}'")
    return parse_json_response(resp)


@router.head(T_PREFIX + "/{username}")
async def check_user_account(
    tenant_name: str,
    username: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(f"/tenants/{tenant_name}/userAccounts/{username}")
    raise_for_hcp_status(resp, f"user '{username}'")
    return Response(status_code=200)


@router.post(T_PREFIX + "/{username}")
async def modify_user_account(
    tenant_name: str,
    username: str,
    body: UserAccountUpdate,
    password: str | None = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    q = {}
    if password:
        q["password"] = password
    resp = await hcp.post(
        f"/tenants/{tenant_name}/userAccounts/{username}",
        body=body,
        query=q or None,
    )
    raise_for_hcp_status(resp, f"user '{username}'")
    return {"status": "updated"}


@router.delete(T_PREFIX + "/{username}")
async def delete_user_account(
    tenant_name: str,
    username: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"/tenants/{tenant_name}/userAccounts/{username}")
    raise_for_hcp_status(resp, f"user '{username}'")
    return {"status": "deleted"}


# ── Change password ───────────────────────────────────────────────────


@router.post(T_PREFIX + "/{username}/changePassword")
async def change_password(
    tenant_name: str,
    username: str,
    body: UpdatePasswordRequest,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/userAccounts/{username}/changePassword",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "password_changed"}


# ── Data access permissions ───────────────────────────────────────────


@router.get(T_PREFIX + "/{username}/dataAccessPermissions")
async def get_user_data_perms(
    tenant_name: str,
    username: str,
    qp: ListQueryParams = Depends(),
    hcp: MapiService = Depends(get_mapi_service),
):
    q: dict = {}
    if qp.offset is not None:
        q["offset"] = qp.offset
    if qp.count is not None:
        q["count"] = qp.count
    if qp.sortType:
        q["sortType"] = qp.sortType
    if qp.sortOrder:
        q["sortOrder"] = qp.sortOrder
    resp = await hcp.get(
        f"/tenants/{tenant_name}/userAccounts/{username}/dataAccessPermissions",
        query=q or None,
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(T_PREFIX + "/{username}/dataAccessPermissions")
async def modify_user_data_perms(
    tenant_name: str,
    username: str,
    body: DataAccessPermissions,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/userAccounts/{username}/dataAccessPermissions",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ═══════════════════════════════════════════════════════════════════════
#  System-level user accounts
# ═══════════════════════════════════════════════════════════════════════

S_PREFIX = "/userAccounts"

system_router = APIRouter(prefix="/userAccounts", tags=["System User Accounts"])


@system_router.get("")
async def list_system_users(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(S_PREFIX, query={"verbose": str(verbose).lower()})
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@system_router.get("/{username}")
async def get_system_user(
    username: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"{S_PREFIX}/{username}",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp, f"system user '{username}'")
    return parse_json_response(resp)


@system_router.head("/{username}")
async def check_system_user(
    username: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(f"{S_PREFIX}/{username}")
    raise_for_hcp_status(resp)
    return Response(status_code=200)


@system_router.post("/{username}")
async def modify_system_user_password(
    username: str,
    password: str = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    q = {}
    if password:
        q["password"] = password
    resp = await hcp.post(f"{S_PREFIX}/{username}", body={}, query=q or None)
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@system_router.post("/{username}/changePassword")
async def change_system_user_password(
    username: str,
    body: UpdatePasswordRequest,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"{S_PREFIX}/{username}/changePassword", body=body)
    raise_for_hcp_status(resp)
    return {"status": "password_changed"}
