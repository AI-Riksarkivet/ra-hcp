"""Namespace access routes – permissions, protocols, CORS, replication collision."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.namespace import (
    ReplicationCollisionSettings,
    HttpProtocol,
    CifsProtocol,
    NfsProtocol,
    SmtpProtocol,
    Protocols,
    CorsConfiguration,
)

router = APIRouter(tags=["Namespace: Access"])

PREFIX = "/tenants/{tenant_name}/namespaces"


# ── Namespace permissions ────────────────────────────────────────────


@router.get(PREFIX + "/{ns_name}/permissions")
async def get_ns_permissions(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/namespaces/{ns_name}/permissions")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/permissions")
async def modify_ns_permissions(
    tenant_name: str,
    ns_name: str,
    body: dict,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/permissions",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Protocols ────────────────────────────────────────────────────────


@router.get(PREFIX + "/{ns_name}/protocols")
async def get_default_protocols(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    """Retrieve default namespace protocol settings (legacy, for default namespaces only)."""
    resp = await hcp.get(f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/protocols")
async def modify_default_protocols(
    tenant_name: str,
    ns_name: str,
    body: Protocols,
    hcp: MapiService = Depends(get_mapi_service),
):
    """Modify default namespace protocol settings (legacy, for default namespaces only)."""
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.get(PREFIX + "/{ns_name}/protocols/{protocol_name}")
async def get_protocol(
    tenant_name: str,
    ns_name: str,
    protocol_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/{protocol_name}"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/protocols/http")
async def modify_http_protocol(
    tenant_name: str,
    ns_name: str,
    body: HttpProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/http",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.post(PREFIX + "/{ns_name}/protocols/cifs")
async def modify_cifs_protocol(
    tenant_name: str,
    ns_name: str,
    body: CifsProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/cifs",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.post(PREFIX + "/{ns_name}/protocols/nfs")
async def modify_nfs_protocol(
    tenant_name: str,
    ns_name: str,
    body: NfsProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/nfs",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.post(PREFIX + "/{ns_name}/protocols/smtp")
async def modify_smtp_protocol(
    tenant_name: str,
    ns_name: str,
    body: SmtpProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/smtp",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Replication collision settings ───────────────────────────────────


@router.get(PREFIX + "/{ns_name}/replicationCollisionSettings")
async def get_replication_collision(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/replicationCollisionSettings"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(PREFIX + "/{ns_name}/replicationCollisionSettings")
async def modify_replication_collision(
    tenant_name: str,
    ns_name: str,
    body: ReplicationCollisionSettings,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/replicationCollisionSettings",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "updated"}


# ── Namespace CORS ───────────────────────────────────────────────────


@router.get(PREFIX + "/{ns_name}/cors")
async def get_ns_cors(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/tenants/{tenant_name}/namespaces/{ns_name}/cors")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(PREFIX + "/{ns_name}/cors")
async def set_ns_cors(
    tenant_name: str,
    ns_name: str,
    body: CorsConfiguration,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.put(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/cors",
        body=body,
    )
    raise_for_hcp_status(resp)
    return {"status": "created"}


@router.delete(PREFIX + "/{ns_name}/cors")
async def delete_ns_cors(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"/tenants/{tenant_name}/namespaces/{ns_name}/cors")
    raise_for_hcp_status(resp)
    return {"status": "deleted"}
