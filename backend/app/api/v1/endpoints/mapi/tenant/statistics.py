"""Tenant-level statistics and chargeback routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.common import ChargebackParams

router = APIRouter(prefix="/tenants", tags=["Tenant Admin: Statistics"])


@router.get("/{tenant_name}/chargebackReport")
async def get_tenant_chargeback(
    tenant_name: str,
    params: ChargebackParams = Depends(),
    hcp: MapiService = Depends(get_mapi_service),
):
    q = {}
    if params.start:
        q["start"] = params.start
    if params.end:
        q["end"] = params.end
    if params.granularity:
        q["granularity"] = params.granularity

    resp = await hcp.get(f"/tenants/{tenant_name}/chargebackReport", query=q)
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get("/{tenant_name}/statistics")
async def get_tenant_statistics(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/statistics")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)
