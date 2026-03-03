"""Node and service statistics routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response

router = APIRouter(tags=["System Statistics"])


@router.get("/nodes/statistics")
async def get_node_statistics(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get("/nodes/statistics", query={"verbose": str(verbose).lower()})
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get("/services/statistics")
async def get_service_statistics(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        "/services/statistics", query={"verbose": str(verbose).lower()}
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)
