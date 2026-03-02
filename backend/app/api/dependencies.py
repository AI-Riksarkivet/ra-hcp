"""Shared FastAPI dependencies for S3 and MAPI services."""

from __future__ import annotations

import logging
from functools import lru_cache
from typing import AsyncGenerator

from app.core.config import AuthSettings, MapiSettings, S3Settings
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


_mapi_instance: MapiService | None = None


async def get_mapi_service() -> AsyncGenerator[MapiService, None]:
    """Yield a shared MapiService (singleton per process)."""
    global _mapi_instance
    if _mapi_instance is None:
        logger.info("Creating MapiService singleton")
        _mapi_instance = MapiService(get_mapi_settings())
    yield _mapi_instance


_s3_instance: S3Service | None = None


async def get_s3_service() -> AsyncGenerator[S3Service, None]:
    """Yield a shared S3Service (singleton per process)."""
    global _s3_instance
    if _s3_instance is None:
        logger.info("Creating S3Service singleton")
        _s3_instance = S3Service(get_s3_settings())
    yield _s3_instance


def reset_instances() -> None:
    """Reset cached singletons. Used by tests."""
    global _mapi_instance, _s3_instance
    _mapi_instance = None
    _s3_instance = None
    get_mapi_settings.cache_clear()
    get_s3_settings.cache_clear()
    get_auth_settings.cache_clear()
