"""System-level tenant routes (list & create)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.tenant import TenantCreate

router = APIRouter(prefix="/tenants", tags=["System Admin: Tenants"])


@router.get("")
async def list_tenants(
    verbose: bool = False,
    prettyprint: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        "/tenants",
        query={"verbose": str(verbose).lower(), "prettyprint": prettyprint or None},
    )
    raise_for_hcp_status(resp, "tenants")
    return parse_json_response(resp)


@router.put("")
async def create_tenant(
    body: TenantCreate,
    username: str = Query(...),
    password: str = Query(...),
    forcePasswordChange: bool = Query(False),
    initialSecurityGroup: str | None = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    """Create an HCP tenant (system-level)."""
    q: dict = {
        "username": username,
        "password": password,
        "forcePasswordChange": str(forcePasswordChange).lower(),
    }
    if initialSecurityGroup is not None:
        q["initialSecurityGroup"] = initialSecurityGroup
    resp = await hcp.put("/tenants", body=body, query=q)
    raise_for_hcp_status(resp, "tenant")
    return {"status": "created"}
