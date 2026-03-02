"""Tenant resource routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.tenant import (
    TenantCreate,
    TenantUpdate,
    ConsoleSecurity,
    ContactInfo,
    EmailNotification,
    SearchSecurity,
)
from app.schemas.namespace import NamespaceDefaults, CorsConfiguration
from app.schemas.common import ListQueryParams, ChargebackParams

router = APIRouter(prefix="/tenants", tags=["Tenant Settings"])


# ── Tenant list (system-level) ─────────────────────────────────────────

@router.get("", tags=["System Tenants"])
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


@router.put("", tags=["System Tenants"])
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


# ── Single tenant ──────────────────────────────────────────────────────

@router.get("/{tenant_name}")
async def get_tenant(
    tenant_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp, f"tenant '{tenant_name}'")
    return parse_json_response(resp)


@router.head("/{tenant_name}")
async def check_tenant(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(f"/tenants/{tenant_name}")
    raise_for_hcp_status(resp, f"tenant '{tenant_name}'")
    return Response(status_code=200)


@router.post("/{tenant_name}")
async def modify_tenant(
    tenant_name: str,
    body: TenantUpdate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"/tenants/{tenant_name}", body=body)
    raise_for_hcp_status(resp, f"tenant '{tenant_name}'")
    return {"status": "updated"}


# ── Console security ──────────────────────────────────────────────────

@router.get("/{tenant_name}/consoleSecurity")
async def get_console_security(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/consoleSecurity")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/{tenant_name}/consoleSecurity")
async def modify_console_security(
    tenant_name: str,
    body: ConsoleSecurity,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"/tenants/{tenant_name}/consoleSecurity", body=body)
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Contact info ───────────────────────────────────────────────────────

@router.get("/{tenant_name}/contactInfo")
async def get_contact_info(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/contactInfo")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/{tenant_name}/contactInfo")
async def modify_contact_info(
    tenant_name: str,
    body: ContactInfo,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"/tenants/{tenant_name}/contactInfo", body=body)
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Email notification ─────────────────────────────────────────────────

@router.get("/{tenant_name}/emailNotification")
async def get_email_notification(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/emailNotification")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/{tenant_name}/emailNotification")
async def modify_email_notification(
    tenant_name: str,
    body: EmailNotification,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"/tenants/{tenant_name}/emailNotification", body=body)
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Namespace defaults ─────────────────────────────────────────────────

@router.get("/{tenant_name}/namespaceDefaults")
async def get_namespace_defaults(
    tenant_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaceDefaults",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/{tenant_name}/namespaceDefaults")
async def modify_namespace_defaults(
    tenant_name: str,
    body: NamespaceDefaults,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"/tenants/{tenant_name}/namespaceDefaults", body=body)
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Search security ───────────────────────────────────────────────────

@router.get("/{tenant_name}/searchSecurity")
async def get_search_security(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/searchSecurity")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/{tenant_name}/searchSecurity")
async def modify_search_security(
    tenant_name: str,
    body: SearchSecurity,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"/tenants/{tenant_name}/searchSecurity", body=body)
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Tenant permissions ─────────────────────────────────────────────────

@router.get("/{tenant_name}/permissions")
async def get_tenant_permissions(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/permissions")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/{tenant_name}/permissions")
async def modify_tenant_permissions(
    tenant_name: str,
    body: dict,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"/tenants/{tenant_name}/permissions", body=body)
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Available service plans ────────────────────────────────────────────

@router.get("/{tenant_name}/availableServicePlans")
async def list_available_service_plans(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/availableServicePlans")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get("/{tenant_name}/availableServicePlans/{plan_name}")
async def get_available_service_plan(
    tenant_name: str,
    plan_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/availableServicePlans/{plan_name}")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


# ── Chargeback report ─────────────────────────────────────────────────

@router.get("/{tenant_name}/chargebackReport", tags=["Tenant Statistics"])
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


# ── Tenant statistics ─────────────────────────────────────────────────

@router.get("/{tenant_name}/statistics", tags=["Tenant Statistics"])
async def get_tenant_statistics(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/statistics")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


# ── Tenant CORS ───────────────────────────────────────────────────────

@router.get("/{tenant_name}/cors")
async def get_tenant_cors(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/cors")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put("/{tenant_name}/cors")
async def set_tenant_cors(
    tenant_name: str,
    body: CorsConfiguration,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.put(f"/tenants/{tenant_name}/cors", body=body)
    raise_for_hcp_status(resp)
    return {"status": "created"}


@router.delete("/{tenant_name}/cors")
async def delete_tenant_cors(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"/tenants/{tenant_name}/cors")
    raise_for_hcp_status(resp)
    return {"status": "deleted"}
