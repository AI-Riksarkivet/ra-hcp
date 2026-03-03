"""Namespace statistics and chargeback routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.schemas.common import ChargebackParams

router = APIRouter(tags=["Namespace: Statistics"])

PREFIX = "/tenants/{tenant_name}/namespaces"


@router.get(PREFIX + "/{ns_name}/statistics")
async def get_ns_statistics(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/statistics"
    )


@router.get(PREFIX + "/{ns_name}/chargebackReport")
async def get_ns_chargeback(
    tenant_name: str,
    ns_name: str,
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
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/chargebackReport",
        query=q or None,
    )
