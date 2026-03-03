"""Replication routes – links, certificates, schedules, content, service."""

from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Query, Response, UploadFile, File

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.replication import (
    LinkCreate,
    LinkUpdate,
    Schedule,
    ReplicationService,
)

router = APIRouter(tags=["Replication"])


# ═══════════════════════════════════════════════════════════════════════
#  Replication Service  /services/replication
# ═══════════════════════════════════════════════════════════════════════


@router.get("/services/replication")
async def get_replication_service(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        "/services/replication", query={"verbose": str(verbose).lower()}
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post("/services/replication")
async def modify_replication_service(
    body: Optional[ReplicationService] = None,
    shutDownAllLinks: Optional[str] = Query(None),
    reestablishAllLinks: Optional[bool] = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    query = {}
    if shutDownAllLinks is not None:
        query["shutDownAllLinks"] = shutDownAllLinks
    if reestablishAllLinks is not None:
        query["reestablishAllLinks"] = ""
    resp = await hcp.post("/services/replication", body=body, query=query or None)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


# ═══════════════════════════════════════════════════════════════════════
#  Certificates  /services/replication/certificates
# ═══════════════════════════════════════════════════════════════════════


@router.get("/services/replication/certificates")
async def list_certificates(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        "/services/replication/certificates",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put("/services/replication/certificates")
async def upload_certificate(
    file: UploadFile = File(...),
    hcp: MapiService = Depends(get_mapi_service),
):
    content = await file.read()
    resp = await hcp.put("/services/replication/certificates", body=content)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.get("/services/replication/certificates/{certificate_id}")
async def get_certificate(
    certificate_id: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"/services/replication/certificates/{certificate_id}")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.delete("/services/replication/certificates/{certificate_id}")
async def delete_certificate(
    certificate_id: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"/services/replication/certificates/{certificate_id}")
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.get("/services/replication/certificates/server")
async def download_server_certificate(
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get("/services/replication/certificates/server")
    raise_for_hcp_status(resp)
    return Response(content=resp.text, media_type="text/plain")


# ═══════════════════════════════════════════════════════════════════════
#  Links  /services/replication/links
# ═══════════════════════════════════════════════════════════════════════

LINKS = "/services/replication/links"


@router.get(LINKS)
async def list_links(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(LINKS, query={"verbose": str(verbose).lower()})
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(LINKS)
async def create_link(
    body: LinkCreate,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.put(LINKS, body=body)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.get(LINKS + "/{link_name}")
async def get_link(
    link_name: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"{LINKS}/{link_name}", query={"verbose": str(verbose).lower()}
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.head(LINKS + "/{link_name}")
async def check_link(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(f"{LINKS}/{link_name}")
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.post(LINKS + "/{link_name}")
async def modify_or_action_link(
    link_name: str,
    body: Optional[LinkUpdate] = None,
    suspend: Optional[bool] = Query(None),
    resume: Optional[bool] = Query(None),
    failOver: Optional[bool] = Query(None),
    failBack: Optional[bool] = Query(None),
    beginRecover: Optional[bool] = Query(None),
    completeRecovery: Optional[bool] = Query(None),
    restore: Optional[bool] = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    query = {}
    for action_name, action_val in [
        ("suspend", suspend),
        ("resume", resume),
        ("failOver", failOver),
        ("failBack", failBack),
        ("beginRecover", beginRecover),
        ("completeRecovery", completeRecovery),
        ("restore", restore),
    ]:
        if action_val is not None:
            query[action_name] = ""
    resp = await hcp.post(f"{LINKS}/{link_name}", body=body, query=query or None)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.delete(LINKS + "/{link_name}")
async def delete_link(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"{LINKS}/{link_name}")
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


# ── Link Content ──────────────────────────────────────────────────────


@router.get(LINKS + "/{link_name}/content")
async def get_link_content(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/content")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


# ── Link Content – Tenants ────────────────────────────────────────────


@router.get(LINKS + "/{link_name}/content/tenants")
async def list_link_tenants(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/content/tenants")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(LINKS + "/{link_name}/content/tenants/{tenant_name}")
async def add_tenant_to_link(
    link_name: str,
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.request(
        "PUT", f"{LINKS}/{link_name}/content/tenants/{tenant_name}"
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.get(LINKS + "/{link_name}/content/tenants/{tenant_name}")
async def get_link_tenant(
    link_name: str,
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/content/tenants/{tenant_name}")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(LINKS + "/{link_name}/content/tenants/{tenant_name}")
async def action_link_tenant(
    link_name: str,
    tenant_name: str,
    pause: Optional[bool] = Query(None),
    resume: Optional[bool] = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    query = {}
    if pause is not None:
        query["pause"] = ""
    if resume is not None:
        query["resume"] = ""
    resp = await hcp.post(
        f"{LINKS}/{link_name}/content/tenants/{tenant_name}",
        query=query or None,
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.delete(LINKS + "/{link_name}/content/tenants/{tenant_name}")
async def remove_tenant_from_link(
    link_name: str,
    tenant_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(f"{LINKS}/{link_name}/content/tenants/{tenant_name}")
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


# ── Link Content – Default Namespace Directories ──────────────────────


@router.get(LINKS + "/{link_name}/content/defaultNamespaceDirectories")
async def list_link_default_ns_dirs(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/content/defaultNamespaceDirectories")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(LINKS + "/{link_name}/content/defaultNamespaceDirectories/{dir_name}")
async def add_default_ns_dir_to_link(
    link_name: str,
    dir_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.request(
        "PUT", f"{LINKS}/{link_name}/content/defaultNamespaceDirectories/{dir_name}"
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.delete(LINKS + "/{link_name}/content/defaultNamespaceDirectories/{dir_name}")
async def remove_default_ns_dir_from_link(
    link_name: str,
    dir_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(
        f"{LINKS}/{link_name}/content/defaultNamespaceDirectories/{dir_name}"
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


# ── Link Content – Chained Links ──────────────────────────────────────


@router.get(LINKS + "/{link_name}/content/chainedLinks")
async def list_chained_links(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/content/chainedLinks")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.put(LINKS + "/{link_name}/content/chainedLinks/{chained_link_name}")
async def add_chained_link(
    link_name: str,
    chained_link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.request(
        "PUT", f"{LINKS}/{link_name}/content/chainedLinks/{chained_link_name}"
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


@router.delete(LINKS + "/{link_name}/content/chainedLinks/{chained_link_name}")
async def remove_chained_link(
    link_name: str,
    chained_link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.delete(
        f"{LINKS}/{link_name}/content/chainedLinks/{chained_link_name}"
    )
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)


# ── Link Candidates ───────────────────────────────────────────────────


@router.get(LINKS + "/{link_name}/localCandidates")
async def get_local_candidates(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/localCandidates")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get(LINKS + "/{link_name}/localCandidates/tenants")
async def get_local_candidate_tenants(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/localCandidates/tenants")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get(LINKS + "/{link_name}/localCandidates/defaultNamespaceDirectories")
async def get_local_candidate_dirs(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"{LINKS}/{link_name}/localCandidates/defaultNamespaceDirectories"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get(LINKS + "/{link_name}/localCandidates/chainedLinks")
async def get_local_candidate_chained(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/localCandidates/chainedLinks")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get(LINKS + "/{link_name}/remoteCandidates")
async def get_remote_candidates(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/remoteCandidates")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get(LINKS + "/{link_name}/remoteCandidates/tenants")
async def get_remote_candidate_tenants(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/remoteCandidates/tenants")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get(LINKS + "/{link_name}/remoteCandidates/defaultNamespaceDirectories")
async def get_remote_candidate_dirs(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"{LINKS}/{link_name}/remoteCandidates/defaultNamespaceDirectories"
    )
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get(LINKS + "/{link_name}/remoteCandidates/chainedLinks")
async def get_remote_candidate_chained(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/remoteCandidates/chainedLinks")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


# ── Link Schedule ─────────────────────────────────────────────────────


@router.get(LINKS + "/{link_name}/schedule")
async def get_link_schedule(
    link_name: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(f"{LINKS}/{link_name}/schedule")
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.post(LINKS + "/{link_name}/schedule")
async def set_link_schedule(
    link_name: str,
    body: Schedule,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"{LINKS}/{link_name}/schedule", body=body)
    raise_for_hcp_status(resp)
    return Response(status_code=resp.status_code)
