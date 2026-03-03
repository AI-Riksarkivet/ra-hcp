"""Authentication endpoint — OAuth2 password flow."""

from __future__ import annotations

import re

from fastapi import APIRouter, Depends, Form, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])

# Valid HCP tenant names: alphanumeric, may contain hyphens (not leading/trailing).
_TENANT_RE = re.compile(r"^[a-zA-Z0-9]([a-zA-Z0-9-]*[a-zA-Z0-9])?$")


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    tenant: str | None = Form(None),
):
    """Authenticate with HCP credentials and receive a JWT bearer token.

    Credentials are stored in the JWT and passed through to HCP on every
    API call.  HCP validates them — login itself always succeeds.

    Optionally provide a **tenant** name to scope requests to a specific
    HCP tenant (virtual-hosted routing).  Omit for system-level access.

    Use the Authorize button (lock icon) in Swagger UI to log in.
    """
    if tenant is not None:
        tenant = tenant.strip()
        if not tenant:
            tenant = None
        elif not _TENANT_RE.match(tenant):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
                detail="Invalid tenant name",
            )
    token = create_access_token(form_data.username, form_data.password, tenant=tenant)
    return {"access_token": token, "token_type": "bearer"}
