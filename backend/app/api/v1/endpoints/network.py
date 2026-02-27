"""Network settings routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.network import NetworkSettings

router = APIRouter(tags=["Network"])


@router.get("/network")
async def get_network_settings(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get("/network", query={"verbose": str(verbose).lower()})
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/network")
async def modify_network_settings(
    body: NetworkSettings,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post("/network", body=body)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)
