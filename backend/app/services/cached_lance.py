"""Cached Lance service — wraps LanceService with Redis for metadata only.

Caches table list and schema in Redis. All data reads (rows, vectors,
cells) go directly through Lance with native push-down. Lance's internal
Session cache handles repeated metadata/index reads at the storage layer.
"""

from __future__ import annotations

import logging
from typing import Any

from opentelemetry import trace

from app.core.config import CacheSettings
from app.services.cache_service import CacheService
from app.services.lance_service import LanceService

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class CachedLanceService:
    """LanceService wrapper with Redis caching for metadata-only reads."""

    def __init__(
        self,
        inner: LanceService,
        cache: CacheService,
        cache_settings: CacheSettings,
    ):
        self._inner = inner
        self._cache = cache
        self._cs = cache_settings

    def __getattr__(self, name: str):
        """Forward uncached methods to the inner LanceService."""
        return getattr(self._inner, name)

    def _key(self, *parts: str) -> str:
        return "lance:" + ":".join(parts)

    # ── Cached metadata reads ────────────────────────────────────

    def list_tables(self) -> list[str]:
        """Cache table list — S3 directory listing is expensive."""
        key = self._key("tables", self._inner._base_uri)
        cached = self._cache.get_sync(key)
        if cached is not None:
            return cached
        result = self._inner.list_tables()
        self._cache.set_sync(key, result, ttl=self._cs.cache_default_ttl)
        return result

    def get_schema(self, table_name: str) -> dict[str, Any]:
        """Cache schema — small, rarely changes, identical for all users."""
        key = self._key("schema", self._inner._base_uri, table_name)
        cached = self._cache.get_sync(key)
        if cached is not None:
            return cached
        result = self._inner.get_schema(table_name)
        self._cache.set_sync(key, result, ttl=self._cs.cache_config_ttl)
        return result

    # get_rows, get_vector_preview, get_cell_bytes are NOT cached.
    # They use Lance's native push-down which is more efficient than
    # serializing to Redis. Lance's Session cache handles storage-level
    # caching internally.
