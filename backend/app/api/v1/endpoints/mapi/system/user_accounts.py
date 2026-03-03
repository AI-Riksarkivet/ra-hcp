"""System-level user account routes."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response

from app.services.mapi_service import MapiService
from app.api.dependencies import get_mapi_service
from app.schemas.user_account import UpdatePasswordRequest

router = APIRouter(prefix="/userAccounts", tags=["System Admin: Identity"])

PREFIX = "/userAccounts"


@router.get("")
async def list_system_users(
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(PREFIX, query={"verbose": str(verbose).lower()})


@router.get("/{username}")
async def get_system_user(
    username: str,
    verbose: bool = False,
    hcp: MapiService = Depends(get_mapi_service),
):
    return await hcp.fetch_json(
        f"{PREFIX}/{username}",
        resource=f"system user '{username}'",
        query={"verbose": str(verbose).lower()},
    )


@router.head("/{username}")
async def check_system_user(
    username: str,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("HEAD", f"{PREFIX}/{username}")
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
    await hcp.send("POST", f"{PREFIX}/{username}", body={}, query=q or None)
    return {"status": "updated"}


@router.post("/{username}/changePassword")
async def change_system_user_password(
    username: str,
    body: UpdatePasswordRequest,
    hcp: MapiService = Depends(get_mapi_service),
):
    await hcp.send("POST", f"{PREFIX}/{username}/changePassword", body=body)
    return {"status": "password_changed"}
