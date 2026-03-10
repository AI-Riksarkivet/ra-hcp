"""Shared FastAPI dependencies for S3 and MAPI services."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import Annotated, AsyncGenerator, Optional

from fastapi import Depends, Request

from app.core.auth_utils import derive_s3_keys
from app.core.config import CacheSettings, MapiSettings, S3Settings
from app.core.security import (
    HcpCredentials,
    oauth2_scheme,
    verify_token_with_credentials,
)
from app.core.tenant_routing import mapi_host_for_tenant, s3_endpoint_for_tenant
from app.services.cache_service import CacheService
from app.services.mapi_service import AuthenticatedMapiService, MapiService
from app.services.query_service import AuthenticatedQueryService, QueryService
from app.schemas.lance import LanceDatasetParams
from app.services.lance_service import LanceService
from app.services.s3_service import S3Service

logger = logging.getLogger(__name__)


@lru_cache()
def get_mapi_settings() -> MapiSettings:
    return MapiSettings()


@lru_cache()
def get_s3_settings() -> S3Settings:
    return S3Settings()


@lru_cache()
def get_cache_settings() -> CacheSettings:
    return CacheSettings()


# ── Service access via app.state ─────────────────────────────────────
#
# All singletons (cache, mapi, s3_cache) live on app.state and are
# initialised in the lifespan handler (see main.py).  Dependencies
# read from request.app.state — no module-level mutable globals.


def get_cache_service(request: Request) -> Optional[CacheService]:
    """Return the shared CacheService from app.state (or None)."""
    return getattr(request.app.state, "cache", None)


async def get_mapi_service(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> AsyncGenerator[AuthenticatedMapiService, None]:
    """Yield an AuthenticatedMapiService wrapping the singleton with JWT creds."""
    base: MapiService = request.app.state.mapi
    creds = verify_token_with_credentials(token)
    settings = get_mapi_settings()
    host = mapi_host_for_tenant(creds.tenant, settings.hcp_domain)
    yield AuthenticatedMapiService(base, creds.username, creds.password, host=host)


# ── Metadata Query service ───────────────────────────────────────────


async def get_query_service(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> AsyncGenerator[AuthenticatedQueryService, None]:
    """Yield an AuthenticatedQueryService wrapping the singleton with JWT creds."""
    base: QueryService = request.app.state.query
    creds = verify_token_with_credentials(token)
    yield AuthenticatedQueryService(base, creds.username, creds.password)


# ── S3 per-credential cache ──────────────────────────────────────────


def _derive_s3_keys(creds: HcpCredentials) -> tuple[str, str]:
    """Derive HCP S3 access_key / secret_key from plain credentials."""
    return derive_s3_keys(creds.username, creds.password)


async def get_s3_service(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
) -> AsyncGenerator[S3Service, None]:
    """Yield an S3Service keyed by the caller's credentials.

    When Redis caching is enabled, returns a CachedS3Service that
    transparently caches metadata reads and invalidates on writes.
    """
    creds = verify_token_with_credentials(token)
    s3_cache: dict[HcpCredentials, S3Service] = request.app.state.s3_cache
    if creds not in s3_cache:
        settings = get_s3_settings()
        access_key, secret_key = _derive_s3_keys(creds)
        endpoint_url = s3_endpoint_for_tenant(creds.tenant, settings.hcp_domain)

        cache: CacheService | None = getattr(request.app.state, "cache", None)
        if cache and cache.enabled:
            from app.services.cached_s3 import CachedS3Service

            logger.info("Creating CachedS3Service for user %s", creds.username)
            s3_cache[creds] = CachedS3Service.with_credentials(
                settings,
                access_key,
                secret_key,
                endpoint_url=endpoint_url,
                cache=cache,
                cache_settings=get_cache_settings(),
            )
        else:
            logger.info("Creating S3Service for user %s", creds.username)
            s3_cache[creds] = S3Service.with_credentials(
                settings,
                access_key,
                secret_key,
                endpoint_url=endpoint_url,
            )
    yield s3_cache[creds]


# ── Lance per-credential cache ────────────────────────────────────────


async def get_lance_service(
    request: Request,
    token: Annotated[str, Depends(oauth2_scheme)],
    params: LanceDatasetParams = Depends(),
) -> AsyncGenerator[LanceService, None]:
    """Yield a LanceService for the given S3 bucket/path, keyed by credentials."""
    creds = verify_token_with_credentials(token)
    access_key, secret_key = _derive_s3_keys(creds)
    settings = get_s3_settings()
    endpoint_url = s3_endpoint_for_tenant(creds.tenant, settings.hcp_domain)
    s3_uri = (
        f"s3://{params.bucket}/{params.path}"
        if params.path
        else f"s3://{params.bucket}"
    )

    cache_key = (creds, params.bucket, params.path)
    lance_cache: dict = request.app.state.lance_cache
    if cache_key not in lance_cache:
        cache: CacheService | None = getattr(request.app.state, "cache", None)
        if cache and cache.enabled:
            from app.services.cached_lance import CachedLanceService

            logger.info(
                "Creating CachedLanceService for %s/%s",
                params.bucket,
                params.path,
            )
            lance_cache[cache_key] = CachedLanceService.with_credentials(
                s3_uri,
                access_key,
                secret_key,
                endpoint_url,
                cache=cache,
                cache_settings=get_cache_settings(),
            )
        else:
            logger.info(
                "Creating LanceService for %s/%s",
                params.bucket,
                params.path,
            )
            lance_cache[cache_key] = LanceService.with_credentials(
                s3_uri, access_key, secret_key, endpoint_url
            )
    yield lance_cache[cache_key]
