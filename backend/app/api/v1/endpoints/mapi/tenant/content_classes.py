"""Content class routes for tenants."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.schemas.content_class import ContentClassCreate, ContentClassUpdate

router = APIRouter(tags=["Tenant Admin: Content Classes"])

PREFIX = "/tenants/{tenant_name}/contentClasses"


@router.get(PREFIX)
async def list_content_classes(
    tenant_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/contentClasses",
        query={"verbose": str(verbose).lower()},
    )


@router.put(PREFIX)
async def create_content_class(
    tenant_name: str,
    body: ContentClassCreate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.send(
        "PUT", f"/tenants/{tenant_name}/contentClasses", body=body,
    )
    return Response(status_code=resp.status_code)


@router.get(PREFIX + "/{content_class_name}")
async def get_content_class(
    tenant_name: str,
    content_class_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"/tenants/{tenant_name}/contentClasses/{content_class_name}",
        query={"verbose": str(verbose).lower()},
    )


@router.head(PREFIX + "/{content_class_name}")
async def check_content_class(
    tenant_name: str,
    content_class_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.send(
        "HEAD", f"/tenants/{tenant_name}/contentClasses/{content_class_name}",
    )
    return Response(status_code=resp.status_code)


@router.post(PREFIX + "/{content_class_name}")
async def update_content_class(
    tenant_name: str,
    content_class_name: str,
    body: ContentClassUpdate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.send(
        "POST", f"/tenants/{tenant_name}/contentClasses/{content_class_name}",
        body=body,
    )
    return Response(status_code=resp.status_code)


@router.delete(PREFIX + "/{content_class_name}")
async def delete_content_class(
    tenant_name: str,
    content_class_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.send(
        "DELETE", f"/tenants/{tenant_name}/contentClasses/{content_class_name}",
    )
    return Response(status_code=resp.status_code)
