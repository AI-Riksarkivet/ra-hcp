"""Namespace resource routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.namespace import (
    NamespaceCreate,
    NamespaceUpdate,
    ComplianceSettings,
    CustomMetadataIndexingSettings,
    ReplicationCollisionSettings,
    HttpProtocol,
    CifsProtocol,
    NfsProtocol,
    SmtpProtocol,
    Protocols,
    CorsConfiguration,
)
from app.schemas.common import ListQueryParams, ChargebackParams, VersioningSettings

router = APIRouter(tags=["Namespaces"])

PREFIX = "/tenants/{tenant_name}/namespaces"


# ── Namespace list & create ────────────────────────────────────────────

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


# ── Single namespace ───────────────────────────────────────────────────

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


# ── Compliance settings ────────────────────────────────────────────────

@router.get(PREFIX + "/{ns_name}/complianceSettings")
async def get_compliance(
    tenant_name: str, ns_name: str, hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/namespaces/{ns_name}/complianceSettings")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/complianceSettings")
async def modify_compliance(
    tenant_name: str,
    ns_name: str,
    body: ComplianceSettings,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/complianceSettings", body=body
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Custom metadata indexing settings ──────────────────────────────────

@router.get(PREFIX + "/{ns_name}/customMetadataIndexingSettings")
async def get_custom_metadata_indexing(
    tenant_name: str, ns_name: str, hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/customMetadataIndexingSettings"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/customMetadataIndexingSettings")
async def modify_custom_metadata_indexing(
    tenant_name: str,
    ns_name: str,
    body: CustomMetadataIndexingSettings,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/customMetadataIndexingSettings",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Namespace permissions ──────────────────────────────────────────────

@router.get(PREFIX + "/{ns_name}/permissions")
async def get_ns_permissions(
    tenant_name: str, ns_name: str, hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/namespaces/{ns_name}/permissions")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/permissions")
async def modify_ns_permissions(
    tenant_name: str, ns_name: str, body: dict,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/permissions", body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Protocols ──────────────────────────────────────────────────────────

@router.get(PREFIX + "/{ns_name}/protocols")
async def get_default_protocols(
    tenant_name: str, ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    """Retrieve default namespace protocol settings (legacy, for default namespaces only)."""
    resp = await hcp.get(f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/protocols")
async def modify_default_protocols(
    tenant_name: str, ns_name: str, body: Protocols,
    hcp: MapiService = Depends(get_mapi_service),
):
    """Modify default namespace protocol settings (legacy, for default namespaces only)."""
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols", body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.get(PREFIX + "/{ns_name}/protocols/{protocol_name}")
async def get_protocol(
    tenant_name: str, ns_name: str, protocol_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/{protocol_name}"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/protocols/http")
async def modify_http_protocol(
    tenant_name: str, ns_name: str, body: HttpProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/http", body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.post(PREFIX + "/{ns_name}/protocols/cifs")
async def modify_cifs_protocol(
    tenant_name: str, ns_name: str, body: CifsProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/cifs", body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.post(PREFIX + "/{ns_name}/protocols/nfs")
async def modify_nfs_protocol(
    tenant_name: str, ns_name: str, body: NfsProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/nfs", body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.post(PREFIX + "/{ns_name}/protocols/smtp")
async def modify_smtp_protocol(
    tenant_name: str, ns_name: str, body: SmtpProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/smtp", body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Replication collision settings ─────────────────────────────────────

@router.get(PREFIX + "/{ns_name}/replicationCollisionSettings")
async def get_replication_collision(
    tenant_name: str, ns_name: str, hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/replicationCollisionSettings"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/replicationCollisionSettings")
async def modify_replication_collision(
    tenant_name: str, ns_name: str, body: ReplicationCollisionSettings,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/replicationCollisionSettings",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Versioning settings ───────────────────────────────────────────────

@router.get(PREFIX + "/{ns_name}/versioningSettings")
async def get_versioning(
    tenant_name: str, ns_name: str, hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/versioningSettings"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/versioningSettings")
async def modify_versioning(
    tenant_name: str, ns_name: str, body: VersioningSettings,
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
    tenant_name: str, ns_name: str, hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/versioningSettings"
    )
    raise_for_hcp_status(resp)
    return {"status": "deleted"}


# ── Namespace statistics ──────────────────────────────────────────────

@router.get(PREFIX + "/{ns_name}/statistics", tags=["Tenant Statistics"])
async def get_ns_statistics(
    tenant_name: str, ns_name: str, hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/namespaces/{ns_name}/statistics")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


# ── Namespace chargeback report ────────────────────────────────────────

@router.get(PREFIX + "/{ns_name}/chargebackReport", tags=["Tenant Statistics"])
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
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/chargebackReport",
        query=q or None,
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


# ── Namespace CORS ────────────────────────────────────────────────────

@router.get(PREFIX + "/{ns_name}/cors")
async def get_ns_cors(
    tenant_name: str, ns_name: str, hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/namespaces/{ns_name}/cors")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(PREFIX + "/{ns_name}/cors")
async def set_ns_cors(
    tenant_name: str, ns_name: str, body: CorsConfiguration,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.put(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/cors", body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "created"}


@router.delete(PREFIX + "/{ns_name}/cors")
async def delete_ns_cors(
    tenant_name: str, ns_name: str, hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"/tenants/{tenant_name}/namespaces/{ns_name}/cors")
    raise_for_hcp_status(resp)
    return {"status": "deleted"}
