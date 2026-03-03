"""System-level group account routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service

router = APIRouter(prefix="/groupAccounts", tags=["System Admin: Identity"])


@router.get("")
async def list_system_groups(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        "/groupAccounts", query={"verbose": str(verbose).lower()}
    )


@router.get("/{group_name}")
async def get_system_group(
    group_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/groupAccounts/{group_name}",
        resource=f"system group '{group_name}'",
        query={"verbose": str(verbose).lower()},
    )


@router.head("/{group_name}")
async def check_system_group(
    group_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("HEAD", f"/groupAccounts/{group_name}")
    return Response(status_code=200)
