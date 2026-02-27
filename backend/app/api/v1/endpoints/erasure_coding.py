"""Erasure coding topology routes."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.erasure_coding import ECTopologyCreate

router = APIRouter(tags=["Erasure Coding"])

EC = "/services/erasureCoding"
TOPOS = f"{EC}/ecTopologies"


# ═══════════════════════════════════════════════════════════════════════
#  EC Topologies
# ═══════════════════════════════════════════════════════════════════════

@router.get(TOPOS)
async def list_ec_topologies(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(TOPOS, query={"verbose": str(verbose).lower()})
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(TOPOS)
async def create_ec_topology(
    body: ECTopologyCreate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.put(TOPOS, body=body)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.get(TOPOS + "/{topology_name}")
async def get_ec_topology(
    topology_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{TOPOS}/{topology_name}", query={"verbose": str(verbose).lower()})
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.head(TOPOS + "/{topology_name}")
async def check_ec_topology(
    topology_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(f"{TOPOS}/{topology_name}")
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.post(TOPOS + "/{topology_name}")
async def modify_or_retire_ec_topology(
    topology_name: str,
    retire: Optional[bool] = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    query = {}
    if retire is not None:
        query["retire"] = ""
    resp = await hcp.post(f"{TOPOS}/{topology_name}", query=query or None)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.delete(TOPOS + "/{topology_name}")
async def delete_ec_topology(
    topology_name: str,
    force: Optional[bool] = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    query = {}
    if force:
        query["force"] = "true"
    resp = await hcp.delete(f"{TOPOS}/{topology_name}", query=query or None)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


# ═══════════════════════════════════════════════════════════════════════
#  EC Topology – Tenant Candidates
# ═══════════════════════════════════════════════════════════════════════

@router.get(TOPOS + "/{topology_name}/tenantCandidates")
async def get_ec_tenant_candidates(
    topology_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"{TOPOS}/{topology_name}/tenantCandidates",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get(TOPOS + "/{topology_name}/tenantConflictingCandidates")
async def get_ec_tenant_conflicting_candidates(
    topology_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"{TOPOS}/{topology_name}/tenantConflictingCandidates",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


# ═══════════════════════════════════════════════════════════════════════
#  EC Topology – Tenants
# ═══════════════════════════════════════════════════════════════════════

@router.get(TOPOS + "/{topology_name}/tenants")
async def list_ec_topology_tenants(
    topology_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{TOPOS}/{topology_name}/tenants")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(TOPOS + "/{topology_name}/tenants/{tenant_name}")
async def add_tenant_to_ec_topology(
    topology_name: str,
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.request("PUT", f"{TOPOS}/{topology_name}/tenants/{tenant_name}")
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.delete(TOPOS + "/{topology_name}/tenants/{tenant_name}")
async def remove_tenant_from_ec_topology(
    topology_name: str,
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"{TOPOS}/{topology_name}/tenants/{tenant_name}")
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


# ═══════════════════════════════════════════════════════════════════════
#  EC Link Candidates
# ═══════════════════════════════════════════════════════════════════════

@router.get(f"{EC}/linkCandidates")
async def get_ec_link_candidates(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"{EC}/linkCandidates",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)
