"""Authentication endpoint — OAuth2 password flow."""

from __future__ import annotations

import secrets

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from app.api.dependencies import get_mapi_settings
from app.core.config import MapiSettings
from app.core.security import create_access_token

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/token")
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    settings: MapiSettings = Depends(get_mapi_settings),
):
    """Authenticate with HCP credentials and receive a JWT bearer token.

    Use the Authorize button (lock icon) in Swagger UI to log in.
    """
    # Timing-safe credential comparison
    username_ok = secrets.compare_digest(form_data.username, settings.hcp_username)
    password_ok = secrets.compare_digest(form_data.password, settings.hcp_password)
    if not (username_ok and password_ok):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = create_access_token(form_data.username)
    return {"access_token": token, "token_type": "bearer"}
