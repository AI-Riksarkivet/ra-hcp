"""Shared FastAPI dependencies for S3 and MAPI services."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import AsyncGenerator, Optional

from app.core.config import AuthSettings, CacheSettings, MapiSettings, S3Settings
from app.services.cache_service import CacheService
from app.services.mapi_service import MapiService
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


async def get_mapi_service() -> AsyncGenerator[MapiService, None]:
    """Yield a shared MapiService (singleton per process).

    If Redis is configured and connected, returns a CachedMapiService.
    """
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


_s3_instance: S3Service | None = None


async def get_s3_service() -> AsyncGenerator[S3Service, None]:
    """Yield a shared S3Service (singleton per process).

    If Redis is configured and connected, returns a CachedS3Service.
    """
    global _s3_instance
    if _s3_instance is None:
        settings = get_s3_settings()
        cache = _cache_instance
        if cache is not None and cache.enabled:
            from app.services.cached_s3 import CachedS3Service

            logger.info("Creating CachedS3Service singleton")
            _s3_instance = CachedS3Service(settings, cache, get_cache_settings())
        else:
            logger.info("Creating S3Service singleton")
            _s3_instance = S3Service(settings)
    yield _s3_instance


def reset_instances() -> None:
    """Reset cached singletons. Used by tests."""
    global _mapi_instance, _s3_instance, _cache_instance
    _mapi_instance = None
    _s3_instance = None
    _cache_instance = None
    get_mapi_settings.cache_clear()
    get_s3_settings.cache_clear()
    get_auth_settings.cache_clear()
    get_cache_settings.cache_clear()
