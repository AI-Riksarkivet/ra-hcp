"""Health check report routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.health_check import HealthCheckPrepare, HealthCheckDownload

router = APIRouter(tags=["Health Check"])


# ── Status ─────────────────────────────────────────────────────────────

@router.get("/healthCheckReport")
async def get_health_check_status(
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get("/healthCheckReport")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


# ── Prepare ────────────────────────────────────────────────────────────

@router.post("/healthCheckReport/prepare")
async def prepare_health_check(
    body: HealthCheckPrepare,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post("/healthCheckReport/prepare", body=body)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


# ── Download ───────────────────────────────────────────────────────────

@router.post("/healthCheckReport/download")
async def download_health_check(
    body: HealthCheckDownload,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post("/healthCheckReport/download", body=body)
    raise_for_hcp_status(resp)
    return Response(
        content=resp.content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=hcp-health-check.zip"},
    )


# ── Cancel ─────────────────────────────────────────────────────────────

@router.post("/healthCheckReport/cancel")
async def cancel_health_check(
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post("/healthCheckReport", query={"cancel": ""})
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)
