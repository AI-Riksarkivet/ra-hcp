"""Retention class routes for namespaces."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.retention_class import RetentionClassCreate, RetentionClassUpdate

router = APIRouter(tags=["Retention Classes"])

PREFIX = "/tenants/{tenant_name}/namespaces/{namespace_name}/retentionClasses"


@router.get(PREFIX)
async def list_retention_classes(
    tenant_name: str,
    namespace_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{namespace_name}/retentionClasses",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(PREFIX)
async def create_retention_class(
    tenant_name: str,
    namespace_name: str,
    body: RetentionClassCreate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.put(
        f"/tenants/{tenant_name}/namespaces/{namespace_name}/retentionClasses",
        body=body,
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.get(PREFIX + "/{retention_class_name}")
async def get_retention_class(
    tenant_name: str,
    namespace_name: str,
    retention_class_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"/tenants/{tenant_name}/namespaces/{namespace_name}/retentionClasses/{retention_class_name}",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.head(PREFIX + "/{retention_class_name}")
async def check_retention_class(
    tenant_name: str,
    namespace_name: str,
    retention_class_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(
        f"/tenants/{tenant_name}/namespaces/{namespace_name}/retentionClasses/{retention_class_name}",
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.post(PREFIX + "/{retention_class_name}")
async def update_retention_class(
    tenant_name: str,
    namespace_name: str,
    retention_class_name: str,
    body: RetentionClassUpdate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(
        f"/tenants/{tenant_name}/namespaces/{namespace_name}/retentionClasses/{retention_class_name}",
        body=body,
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.delete(PREFIX + "/{retention_class_name}")
async def delete_retention_class(
    tenant_name: str,
    namespace_name: str,
    retention_class_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(
        f"/tenants/{tenant_name}/namespaces/{namespace_name}/retentionClasses/{retention_class_name}",
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)
