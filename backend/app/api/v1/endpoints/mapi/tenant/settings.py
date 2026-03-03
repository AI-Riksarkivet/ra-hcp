"""Tenant-level settings routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.schemas.tenant import (
    TenantUpdate,
    ConsoleSecurity,
    ContactInfo,
    EmailNotification,
    SearchSecurity,
    AvailableServicePlan,
)
from app.schemas.namespace import NamespaceDefaults, CorsConfiguration

router = APIRouter(prefix="/tenants", tags=["Tenant Admin: Settings"])


# ── Single tenant ────────────────────────────────────────────────────


@router.get("/{tenant_name}")
async def get_tenant(
    tenant_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}",
        resource=f"tenant '{tenant_name}'",
        query={"verbose": str(verbose).lower()},
    )


@router.head("/{tenant_name}")
async def check_tenant(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "HEAD", f"/tenants/{tenant_name}", resource=f"tenant '{tenant_name}'"
    )
    return Response(status_code=200)


@router.post("/{tenant_name}")
async def modify_tenant(
    tenant_name: str,
    body: TenantUpdate,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "POST",
        f"/tenants/{tenant_name}",
        resource=f"tenant '{tenant_name}'",
        body=body,
    )
    return {"status": "updated"}


# ── Console security ─────────────────────────────────────────────────


@router.get("/{tenant_name}/consoleSecurity", response_model=ConsoleSecurity)
async def get_console_security(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(f"/tenants/{tenant_name}/consoleSecurity")


@router.post("/{tenant_name}/consoleSecurity")
async def modify_console_security(
    tenant_name: str,
    body: ConsoleSecurity,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("POST", f"/tenants/{tenant_name}/consoleSecurity", body=body)
    return {"status": "updated"}


# ── Contact info ─────────────────────────────────────────────────────


@router.get("/{tenant_name}/contactInfo", response_model=ContactInfo)
async def get_contact_info(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(f"/tenants/{tenant_name}/contactInfo")


@router.post("/{tenant_name}/contactInfo")
async def modify_contact_info(
    tenant_name: str,
    body: ContactInfo,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("POST", f"/tenants/{tenant_name}/contactInfo", body=body)
    return {"status": "updated"}


# ── Email notification ───────────────────────────────────────────────


@router.get("/{tenant_name}/emailNotification", response_model=EmailNotification)
async def get_email_notification(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(f"/tenants/{tenant_name}/emailNotification")


@router.post("/{tenant_name}/emailNotification")
async def modify_email_notification(
    tenant_name: str,
    body: EmailNotification,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("POST", f"/tenants/{tenant_name}/emailNotification", body=body)
    return {"status": "updated"}


# ── Namespace defaults ───────────────────────────────────────────────


@router.get("/{tenant_name}/namespaceDefaults", response_model=NamespaceDefaults)
async def get_namespace_defaults(
    tenant_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/namespaceDefaults",
        query={"verbose": str(verbose).lower()},
    )


@router.post("/{tenant_name}/namespaceDefaults")
async def modify_namespace_defaults(
    tenant_name: str,
    body: NamespaceDefaults,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("POST", f"/tenants/{tenant_name}/namespaceDefaults", body=body)
    return {"status": "updated"}


# ── Search security ──────────────────────────────────────────────────


@router.get("/{tenant_name}/searchSecurity", response_model=SearchSecurity)
async def get_search_security(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(f"/tenants/{tenant_name}/searchSecurity")


@router.post("/{tenant_name}/searchSecurity")
async def modify_search_security(
    tenant_name: str,
    body: SearchSecurity,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("POST", f"/tenants/{tenant_name}/searchSecurity", body=body)
    return {"status": "updated"}


# ── Tenant permissions ───────────────────────────────────────────────


@router.get("/{tenant_name}/permissions")
async def get_tenant_permissions(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(f"/tenants/{tenant_name}/permissions")


@router.post("/{tenant_name}/permissions")
async def modify_tenant_permissions(
    tenant_name: str,
    body: dict,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("POST", f"/tenants/{tenant_name}/permissions", body=body)
    return {"status": "updated"}


# ── Available service plans ──────────────────────────────────────────


@router.get("/{tenant_name}/availableServicePlans")
async def list_available_service_plans(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(f"/tenants/{tenant_name}/availableServicePlans")


@router.get(
    "/{tenant_name}/availableServicePlans/{plan_name}",
    response_model=AvailableServicePlan,
)
async def get_available_service_plan(
    tenant_name: str,
    plan_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/availableServicePlans/{plan_name}"
    )


# ── Tenant CORS ──────────────────────────────────────────────────────


@router.get("/{tenant_name}/cors", response_model=CorsConfiguration)
async def get_tenant_cors(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(f"/tenants/{tenant_name}/cors")


@router.put("/{tenant_name}/cors")
async def set_tenant_cors(
    tenant_name: str,
    body: CorsConfiguration,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("PUT", f"/tenants/{tenant_name}/cors", body=body)
    return {"status": "created"}


@router.delete("/{tenant_name}/cors")
async def delete_tenant_cors(
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("DELETE", f"/tenants/{tenant_name}/cors")
    return {"status": "deleted"}
