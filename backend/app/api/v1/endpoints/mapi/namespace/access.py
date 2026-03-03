"""Namespace access routes – permissions, protocols, CORS, replication collision."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.schemas.namespace import (
    ReplicationCollisionSettings,
    HttpProtocol,
    CifsProtocol,
    NfsProtocol,
    SmtpProtocol,
    Protocols,
    CorsConfiguration,
)
from app.schemas.common import StatusResponse, PermissionsResponse

router = APIRouter(tags=["Namespace: Access"])

PREFIX = "/tenants/{tenant_name}/namespaces"


# ── Namespace permissions ────────────────────────────────────────────


@router.get(PREFIX + "/{ns_name}/permissions", response_model=PermissionsResponse)
async def get_ns_permissions(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/permissions"
    )


@router.post(PREFIX + "/{ns_name}/permissions", response_model=StatusResponse)
async def modify_ns_permissions(
    tenant_name: str,
    ns_name: str,
    body: PermissionsResponse,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "POST",
        f"/tenants/{tenant_name}/namespaces/{ns_name}/permissions",
        body=body,
    )
    return {"status": "updated"}


# ── Protocols ────────────────────────────────────────────────────────


@router.get(PREFIX + "/{ns_name}/protocols", response_model=Protocols)
async def get_default_protocols(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    """Retrieve default namespace protocol settings (legacy, for default namespaces only)."""
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols"
    )


@router.post(PREFIX + "/{ns_name}/protocols", response_model=StatusResponse)
async def modify_default_protocols(
    tenant_name: str,
    ns_name: str,
    body: Protocols,
    hcp: MapiService = Depends(get_mapi_service),
):
    """Modify default namespace protocol settings (legacy, for default namespaces only)."""
    await hcp.send(
        "POST",
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols",
        body=body,
    )
    return {"status": "updated"}


@router.get(PREFIX + "/{ns_name}/protocols/{protocol_name}")
async def get_protocol(
    tenant_name: str,
    ns_name: str,
    protocol_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/{protocol_name}"
    )


@router.post(PREFIX + "/{ns_name}/protocols/http", response_model=StatusResponse)
async def modify_http_protocol(
    tenant_name: str,
    ns_name: str,
    body: HttpProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "POST",
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/http",
        body=body,
    )
    return {"status": "updated"}


@router.post(PREFIX + "/{ns_name}/protocols/cifs", response_model=StatusResponse)
async def modify_cifs_protocol(
    tenant_name: str,
    ns_name: str,
    body: CifsProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "POST",
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/cifs",
        body=body,
    )
    return {"status": "updated"}


@router.post(PREFIX + "/{ns_name}/protocols/nfs", response_model=StatusResponse)
async def modify_nfs_protocol(
    tenant_name: str,
    ns_name: str,
    body: NfsProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "POST",
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/nfs",
        body=body,
    )
    return {"status": "updated"}


@router.post(PREFIX + "/{ns_name}/protocols/smtp", response_model=StatusResponse)
async def modify_smtp_protocol(
    tenant_name: str,
    ns_name: str,
    body: SmtpProtocol,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "POST",
        f"/tenants/{tenant_name}/namespaces/{ns_name}/protocols/smtp",
        body=body,
    )
    return {"status": "updated"}


# ── Replication collision settings ───────────────────────────────────


@router.get(
    PREFIX + "/{ns_name}/replicationCollisionSettings",
    response_model=ReplicationCollisionSettings,
)
async def get_replication_collision(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/namespaces/{ns_name}/replicationCollisionSettings"
    )


@router.post(
    PREFIX + "/{ns_name}/replicationCollisionSettings", response_model=StatusResponse
)
async def modify_replication_collision(
    tenant_name: str,
    ns_name: str,
    body: ReplicationCollisionSettings,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "POST",
        f"/tenants/{tenant_name}/namespaces/{ns_name}/replicationCollisionSettings",
        body=body,
    )
    return {"status": "updated"}


# ── Namespace CORS ───────────────────────────────────────────────────


@router.get(PREFIX + "/{ns_name}/cors", response_model=CorsConfiguration)
async def get_ns_cors(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(f"/tenants/{tenant_name}/namespaces/{ns_name}/cors")


@router.put(PREFIX + "/{ns_name}/cors", response_model=StatusResponse)
async def set_ns_cors(
    tenant_name: str,
    ns_name: str,
    body: CorsConfiguration,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "PUT",
        f"/tenants/{tenant_name}/namespaces/{ns_name}/cors",
        body=body,
    )
    return {"status": "created"}


@router.delete(PREFIX + "/{ns_name}/cors", response_model=StatusResponse)
async def delete_ns_cors(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send(
        "DELETE",
        f"/tenants/{tenant_name}/namespaces/{ns_name}/cors",
    )
    return {"status": "deleted"}
