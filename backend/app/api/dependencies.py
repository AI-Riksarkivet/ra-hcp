"""Shared FastAPI dependencies for S3 and MAPI services."""

from __future__ import annotations

import base64
import hashlib
import logging
from functools import lru_cache
from typing import Annotated, AsyncGenerator, Optional

from fastapi import Depends

from app.core.config import AuthSettings, CacheSettings, MapiSettings, S3Settings
from app.core.security import (
    HcpCredentials,
    oauth2_scheme,
    verify_token_with_credentials,
)
from app.core.tenant_routing import mapi_host_for_tenant, s3_endpoint_for_tenant
from app.services.cache_service import CacheService
from app.services.mapi_service import AuthenticatedMapiService, MapiService
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)


@lru_cache()
def get_mapi_settings() -> MapiSettings:
    return MapiSettings()


@lru_cache()
def get_s3_settings() -> S3Settings:
    return S3Settings()


@lru_cache()
def get_auth_settings() -> AuthSettings:
    return AuthSettings()


@lru_cache()
def get_cache_settings() -> CacheSettings:
    return CacheSettings()


# ── Cache singleton ───────────────────────────────────────────────────

_cache_instance: Optional[CacheService] = None


def set_cache_instance(cache: CacheService) -> None:
    global _cache_instance
    _cache_instance = cache


def get_cache_service() -> Optional[CacheService]:
    return _cache_instance


# ── Service singletons ───────────────────────────────────────────────

_mapi_instance: MapiService | None = None


async def _get_base_mapi_service() -> AsyncGenerator[MapiService, None]:
    """Yield the shared MapiService singleton (no per-user credentials)."""
    global _mapi_instance
    if _mapi_instance is None:
        settings = get_mapi_settings()
        cache = _cache_instance
        if cache is not None and cache.enabled:
            from app.services.cached_mapi import CachedMapiService

            logger.info("Creating CachedMapiService singleton")
            _mapi_instance = CachedMapiService(settings, cache, get_cache_settings())
        else:
            logger.info("Creating MapiService singleton")
            _mapi_instance = MapiService(settings)
    yield _mapi_instance


async def get_mapi_service(
    token: Annotated[str, Depends(oauth2_scheme)],
    base: Annotated[MapiService, Depends(_get_base_mapi_service)],
) -> AsyncGenerator[AuthenticatedMapiService, None]:
    """Yield an AuthenticatedMapiService wrapping the singleton with JWT creds."""
    creds = verify_token_with_credentials(token)
    settings = get_mapi_settings()
    host = mapi_host_for_tenant(creds.tenant, settings.hcp_domain)
    yield AuthenticatedMapiService(base, creds.username, creds.password, host=host)


# ── S3 per-credential cache ──────────────────────────────────────────

_s3_cache: dict[HcpCredentials, S3Service] = {}


def _derive_s3_keys(creds: HcpCredentials) -> tuple[str, str]:
    """Derive HCP S3 access_key / secret_key from plain credentials."""
    access_key = base64.b64encode(creds.username.encode()).decode()
    secret_key = hashlib.md5(creds.password.encode()).hexdigest()
    return access_key, secret_key


async def get_s3_service(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> AsyncGenerator[S3Service, None]:
    """Yield an S3Service keyed by the caller's credentials."""
    creds = verify_token_with_credentials(token)
    if creds not in _s3_cache:
        settings = get_s3_settings()
        access_key, secret_key = _derive_s3_keys(creds)
        endpoint_url = s3_endpoint_for_tenant(creds.tenant, settings.hcp_domain)
        logger.info("Creating S3Service for user %s", creds.username)
        _s3_cache[creds] = S3Service.with_credentials(
            settings, access_key, secret_key, endpoint_url=endpoint_url
        )
    yield _s3_cache[creds]


def reset_instances() -> None:
    """Reset cached singletons. Used by tests."""
    global _mapi_instance, _cache_instance
    _mapi_instance = None
    _s3_cache.clear()
    _cache_instance = None
    get_mapi_settings.cache_clear()
    get_s3_settings.cache_clear()
    get_auth_settings.cache_clear()
    get_cache_settings.cache_clear()
