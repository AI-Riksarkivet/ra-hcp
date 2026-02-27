"""Support access credentials routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, UploadFile, File

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response

router = APIRouter(tags=["Support"])


@router.get("/supportaccesscredentials")
async def get_support_credentials(
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get("/supportaccesscredentials")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put("/supportaccesscredentials")
async def upload_support_credentials(
    file: UploadFile = File(...),
    hcp: MapiService = Depends(get_mapi_service),
):
    content = await file.read()
    resp = await hcp.put("/supportaccesscredentials", body=content)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)
