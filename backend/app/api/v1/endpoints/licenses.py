"""License management routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, UploadFile, File

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response

router = APIRouter(tags=["Licenses"])


@router.get("/storage/licenses")
async def list_licenses(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get("/storage/licenses", query={"verbose": str(verbose).lower()})
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put("/storage/licenses")
async def upload_license(
    file: UploadFile = File(...),
    hcp: MapiService = Depends(get_mapi_service),
):
    content = await file.read()
    resp = await hcp.put("/storage/licenses", body=content)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.get("/storage/licenses/{serial_number}")
async def get_license(
    serial_number: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/storage/licenses/{serial_number}")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)
