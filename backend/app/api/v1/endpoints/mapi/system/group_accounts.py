"""System-level group account routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response

router = APIRouter(prefix="/groupAccounts", tags=["System Admin: Identity"])


@router.get("")
async def list_system_groups(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get("/groupAccounts", query={"verbose": str(verbose).lower()})
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get("/{group_name}")
async def get_system_group(
    group_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/groupAccounts/{group_name}",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp, f"system group '{group_name}'")
    return parse_json_response(resp)


@router.head("/{group_name}")
async def check_system_group(
    group_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(f"/groupAccounts/{group_name}")
    raise_for_hcp_status(resp)
    return Response(status_code=200)
