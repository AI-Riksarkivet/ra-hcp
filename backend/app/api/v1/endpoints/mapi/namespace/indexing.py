"""Namespace custom metadata indexing routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.namespace import CustomMetadataIndexingSettings

router = APIRouter(tags=["Namespace: Indexing"])

PREFIX = "/tenants/{tenant_name}/namespaces"


@router.get(PREFIX + "/{ns_name}/customMetadataIndexingSettings")
async def get_custom_metadata_indexing(
    tenant_name: str,
    ns_name: str,
    hcp: MapiService = Depends(get_mapi_service),
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
