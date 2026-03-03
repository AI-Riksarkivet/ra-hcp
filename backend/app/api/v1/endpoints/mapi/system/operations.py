"""System operations routes – health check, logs, support."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, UploadFile, File

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.health_check import HealthCheckPrepare, HealthCheckDownload
from app.schemas.logs import LogPrepare, LogDownload

router = APIRouter(tags=["System Admin: Operations"])


# ── Health Check ─────────────────────────────────────────────────────


@router.get("/healthCheckReport")
async def get_health_check_status(
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get("/healthCheckReport")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/healthCheckReport/prepare")
async def prepare_health_check(
    body: HealthCheckPrepare,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post("/healthCheckReport/prepare", body=body)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


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


@router.post("/healthCheckReport/cancel")
async def cancel_health_check(
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post("/healthCheckReport", query={"cancel": ""})
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


# ── Logs ─────────────────────────────────────────────────────────────


@router.get("/logs")
async def get_log_status(
    hcp: MapiService = Depends(get_mapi_service),
):
    """Retrieve the status of the log download in progress."""
    resp = await hcp.get("/logs")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/logs")
async def log_action(
    mark: Optional[str] = Query(None),
    cancel: Optional[bool] = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    """Mark the logs with a message, or cancel (clear) the log download."""
    q: dict = {}
    if mark is not None:
        q["mark"] = mark
    if cancel is not None:
        q["cancel"] = ""
    resp = await hcp.post("/logs", query=q or None)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.post("/logs/prepare")
async def prepare_logs(
    body: LogPrepare,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post("/logs/prepare", body=body)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.post("/logs/download")
async def download_logs(
    body: LogDownload,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post("/logs/download", body=body)
    raise_for_hcp_status(resp)
    return Response(
        content=resp.content,
        media_type="application/octet-stream",
        headers={"Content-Disposition": "attachment; filename=hcp-logs.zip"},
    )


# ── Support ──────────────────────────────────────────────────────────


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
