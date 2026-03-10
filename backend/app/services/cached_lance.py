"""Cached Lance service — Redis for metadata only.

Caches table list and schema in Redis. All data reads (rows, vectors,
cells) go directly through Lance with native push-down. Lance's internal
Session cache handles repeated metadata/index reads at the storage layer.
"""

from __future__ import annotations

import json
import logging
from typing import Any

from opentelemetry import trace

from app.core.config import CacheSettings
from app.services.cache_service import CacheService
from app.services.lance_service import LanceService

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class CachedLanceService(LanceService):
    """LanceService with Redis caching for metadata-only reads."""

    def __init__(
        self,
        base_uri: str,
        storage_options: dict[str, str],
        cache: CacheService,
        cache_settings: CacheSettings,
    ):
        super().__init__(base_uri, storage_options)
        self._cache = cache
        self._cs = cache_settings

    @classmethod
    def with_credentials(
        cls,
        base_uri: str,
        access_key: str,
        secret_key: str,
        endpoint_url: str,
        *,
        verify_ssl: bool = True,
        cache: CacheService | None = None,
        cache_settings: CacheSettings | None = None,
    ) -> CachedLanceService:
        opts: dict[str, str] = {
            "aws_access_key_id": access_key,
            "aws_secret_access_key": secret_key,
            "endpoint_url": endpoint_url,
            "allow_http": "false",
        }
        if not verify_ssl:
            opts["aws_allow_invalid_certificates"] = "true"
        instance = cls.__new__(cls)
        LanceService.__init__(instance, base_uri, storage_options=opts)
        instance._cache = cache
        instance._cs = cache_settings
        return instance

    def _key(self, *parts: str) -> str:
        return "lance:" + ":".join(parts)

    # ── Cached metadata reads ────────────────────────────────────

    def list_tables(self) -> list[str]:
        """Cache table list — S3 directory listing is expensive."""
        key = self._key("tables", self._base_uri)
        cached = self._cache.get_sync(key)
        if cached is not None:
            return json.loads(cached)
        result = super().list_tables()
        self._cache.set_sync(key, json.dumps(result), ttl=self._cs.cache_default_ttl)
        return result

    def get_schema(self, table_name: str) -> dict[str, Any]:
        """Cache schema — small, rarely changes, identical for all users."""
        key = self._key("schema", self._base_uri, table_name)
        cached = self._cache.get_sync(key)
        if cached is not None:
            return json.loads(cached)
        result = super().get_schema(table_name)
        self._cache.set_sync(key, json.dumps(result), ttl=self._cs.cache_config_ttl)
        return result

    # get_rows, get_vector_preview, get_cell_bytes are NOT cached.
    # They use Lance's native push-down which is more efficient than
    # serializing to Redis. Lance's Session cache handles storage-level
    # caching internally.
