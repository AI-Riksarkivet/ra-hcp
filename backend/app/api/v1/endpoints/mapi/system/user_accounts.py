"""System-level user account routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.api.errors import raise_for_hcp_status, parse_json_response
from app.schemas.user_account import UpdatePasswordRequest

router = APIRouter(prefix="/userAccounts", tags=["System Admin: Identity"])

PREFIX = "/userAccounts"


@router.get("")
async def list_system_users(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(PREFIX, query={"verbose": str(verbose).lower()})
    raise_for_hcp_status(resp)
    return parse_json_response(resp)


@router.get("/{username}")
async def get_system_user(
    username: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.get(
        f"{PREFIX}/{username}",
        query={"verbose": str(verbose).lower()},
    )
    raise_for_hcp_status(resp, f"system user '{username}'")
    return parse_json_response(resp)


@router.head("/{username}")
async def check_system_user(
    username: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.head(f"{PREFIX}/{username}")
    raise_for_hcp_status(resp)
    return Response(status_code=200)


@router.post("/{username}")
async def modify_system_user_password(
    username: str,
    password: str = Query(None),
    hcp: MapiService = Depends(get_mapi_service),
):
    q = {}
    if password:
        q["password"] = password
    resp = await hcp.post(f"{PREFIX}/{username}", body={}, query=q or None)
    raise_for_hcp_status(resp)
    return {"status": "updated"}


@router.post("/{username}/changePassword")
async def change_system_user_password(
    username: str,
    body: UpdatePasswordRequest,
    hcp: MapiService = Depends(get_mapi_service),
):
    resp = await hcp.post(f"{PREFIX}/{username}/changePassword", body=body)
    raise_for_hcp_status(resp)
    return {"status": "password_changed"}
