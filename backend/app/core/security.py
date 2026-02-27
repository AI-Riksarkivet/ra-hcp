"""OAuth2 password flow with JWT bearer tokens."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from app.core.config import AuthSettings, MapiSettings

_ENV_FILE = "../.env"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")


def _get_auth_settings() -> AuthSettings:
    return AuthSettings()


def _get_mapi_settings() -> MapiSettings:
    return MapiSettings()


def create_access_token(username: str, settings: AuthSettings | None = None) -> str:
    """Create a JWT access token for the given username."""
    if settings is None:
        settings = _get_auth_settings()
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.api_token_expire_minutes)
    payload = {"sub": username, "exp": expire}
    return jwt.encode(payload, settings.api_secret_key, algorithm="HS256")


def verify_token(token: str, settings: AuthSettings | None = None) -> str:
    """Verify a JWT token and return the username."""
    if settings is None:
        settings = _get_auth_settings()
    try:
        payload = jwt.decode(token, settings.api_secret_key, algorithms=["HS256"])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: no subject",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return username
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> str:
    """Dependency that extracts and validates the current user from JWT."""
    return verify_token(token)
