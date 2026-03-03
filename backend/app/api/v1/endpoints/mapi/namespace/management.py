"""Namespace CRUD and versioning routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.namespace import NamespaceCreate, NamespaceUpdate
from app.schemas.common import ListQueryParams, VersioningSettings

router = APIRouter(tags=["Namespace: Management"])

PREFIX = "/tenants/{tenant_name}/namespaces"


# ── Namespace list & create ──────────────────────────────────────────


@router.get(PREFIX)
async def list_namespaces(
    tenant_name: str,
    qp: ListQueryParams = Depends(),
    hcp: MapiService = Depends(get_mapi_service),
):
    q: dict = {}
    if qp.offset is not None:
        q["offset"] = qp.offset
    if qp.count is not None:
        q["count"] = qp.count
    if qp.sortType:
        q["sortType"] = qp.sortType
    if qp.sortOrder:
        q["sortOrder"] = qp.sortOrder
    if qp.filterType:
        q["filterType"] = qp.filterType
    if qp.filterString:
        q["filterString"] = qp.filterString

    resp = await hcp.get(f"/tenants/{tenant_name}/namespaces", query=q or None)
    raise_for_hcp_status(resp, "namespaces")
    return parse_json_response(resp)


@router.put(PREFIX)
async def create_namespace(
    tenant_name: str,
    body: NamespaceCreate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.put(f"/tenants/{tenant_name}/namespaces", body=body)
    raise_for_hcp_status(resp, "namespace")
    return {"status": "created"}


# ── Single namespace ─────────────────────────────────────────────────


@router.get(PREFIX + "/{ns_name}")
async def get_namespace(
    tenant_name: str,
    ns_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{ns_name}",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp, f"namespace '{ns_name}'")
    return parse_json_response(resp)


@router.head(PREFIX + "/{ns_name}")
async def check_namespace(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(f"/tenants/{tenant_name}/namespaces/{ns_name}")
    raise_for_hcp_status(resp, f"namespace '{ns_name}'")
    return Response(status_code=200)


@router.post(PREFIX + "/{ns_name}")
async def modify_namespace(
    tenant_name: str,
    ns_name: str,
    body: NamespaceUpdate,
    resetMQECheckpoint: str | None = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    q = {}
    if resetMQECheckpoint is not None:
        q["resetMQECheckpoint"] = resetMQECheckpoint
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}",
        body=body,
        query=q or None,
    )
    raise_for_hcp_status(resp, f"namespace '{ns_name}'")
    return {"status": "updated"}


@router.delete(PREFIX + "/{ns_name}")
async def delete_namespace(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"/tenants/{tenant_name}/namespaces/{ns_name}")
    raise_for_hcp_status(resp, f"namespace '{ns_name}'")
    return {"status": "deleted"}


# ── Versioning settings ─────────────────────────────────────────────


@router.get(PREFIX + "/{ns_name}/versioningSettings")
async def get_versioning(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/versioningSettings"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/versioningSettings")
async def modify_versioning(
    tenant_name: str,
    ns_name: str,
    body: VersioningSettings,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/versioningSettings",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.delete(PREFIX + "/{ns_name}/versioningSettings")
async def delete_versioning(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/versioningSettings"
    )
    raise_for_hcp_status(resp)
    return {"status": "deleted"}
