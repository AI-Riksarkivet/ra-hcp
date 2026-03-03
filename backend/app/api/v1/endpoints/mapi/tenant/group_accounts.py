"""Tenant-level group account routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.group_account import GroupAccountCreate, GroupAccountUpdate
from app.schemas.common import DataAccessPermissions

router = APIRouter(tags=["Tenant Admin: Identity"])

T_PREFIX = "/tenants/{tenant_name}/groupAccounts"


@router.get(T_PREFIX)
async def list_group_accounts(
    tenant_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/groupAccounts",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(T_PREFIX)
async def create_group_account(
    tenant_name: str,
    body: GroupAccountCreate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.put(f"/tenants/{tenant_name}/groupAccounts", body=body)
    raise_for_hcp_status(resp, "group account")
    return {"status": "created"}


@router.get(T_PREFIX + "/{group_name}")
async def get_group_account(
    tenant_name: str,
    group_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/groupAccounts/{group_name}",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp, f"group '{group_name}'")
    return parse_json_response(resp)


@router.head(T_PREFIX + "/{group_name}")
async def check_group_account(
    tenant_name: str,
    group_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(f"/tenants/{tenant_name}/groupAccounts/{group_name}")
    raise_for_hcp_status(resp)
    return Response(status_code=200)


@router.post(T_PREFIX + "/{group_name}")
async def modify_group_account(
    tenant_name: str,
    group_name: str,
    body: GroupAccountUpdate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/groupAccounts/{group_name}",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.delete(T_PREFIX + "/{group_name}")
async def delete_group_account(
    tenant_name: str,
    group_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"/tenants/{tenant_name}/groupAccounts/{group_name}")
    raise_for_hcp_status(resp)
    return {"status": "deleted"}


# ── Data access permissions ──────────────────────────────────────────


@router.get(T_PREFIX + "/{group_name}/dataAccessPermissions")
async def get_group_data_perms(
    tenant_name: str,
    group_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/groupAccounts/{group_name}/dataAccessPermissions"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(T_PREFIX + "/{group_name}/dataAccessPermissions")
async def modify_group_data_perms(
    tenant_name: str,
    group_name: str,
    body: DataAccessPermissions,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/groupAccounts/{group_name}/dataAccessPermissions",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}
