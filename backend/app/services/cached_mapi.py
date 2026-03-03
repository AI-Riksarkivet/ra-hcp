"""Cached MAPI service — subclasses MapiService to add Redis caching.

GET responses are cached; PUT/POST/DELETE invalidate affected entries.
Zero changes to endpoint files required.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional
from urllib.parse import urlencode

import httpx
from opentelemetry import trace

from app.core.config import CacheSettings, MapiSettings
from app.services.cache_service import CacheService
from app.services.mapi_service import MapiService

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)

# Paths that should never be cached
_NO_CACHE_PATHS = ("/logs", "/healthCheck", "/support")

# Path fragments → TTL override
_TTL_RULES: list[tuple[str, str]] = [
    ("statistics", "cache_stats_ttl"),
    ("chargeback", "cache_stats_ttl"),
    ("consoleSecurity", "cache_config_ttl"),
    ("permissions", "cache_config_ttl"),
    ("cifsShares", "cache_config_ttl"),
    ("protocolSettings", "cache_config_ttl"),
    ("emailNotification", "cache_config_ttl"),
    ("namespaceDefaults", "cache_config_ttl"),
    ("searchSecurity", "cache_config_ttl"),
]


class CachedMapiService(MapiService):
    """MapiService with transparent Redis caching on GET requests."""

    def __init__(
        self,
        settings: MapiSettings,
        cache: CacheService,
        cache_settings: CacheSettings,
    ):
        super().__init__(settings)
        self._cache = cache
        self._cache_settings = cache_settings

    def _cache_key(self, path: str, query: Optional[Dict[str, Any]]) -> str:
        key = f"mapi:{path}"
        if query:
            filtered = {k: v for k, v in sorted(query.items()) if v is not None}
            if filtered:
                key += "?" + urlencode(filtered, doseq=True)
        return key

    def _select_ttl(self, path: str) -> int:
        for fragment, attr in _TTL_RULES:
            if fragment in path:
                return getattr(self._cache_settings, attr)
        return self._cache_settings.cache_default_ttl

    def _should_cache(self, path: str) -> bool:
        return not any(path.startswith(p) or path.endswith(p) for p in _NO_CACHE_PATHS)

    async def request(
        self,
        method: str,
        path: str,
        *,
        host: Optional[str] = None,
        body: Optional[Any] = None,
        query: Optional[Dict[str, Any]] = None,
        content_type: str = "application/json",
        accept: str = "application/json",
        username: Optional[str] = None,
        password: Optional[str] = None,
        auth_type: Optional[str] = None,
        raw_body: Optional[bytes] = None,
    ) -> httpx.Response:
        is_get = method.upper() == "GET"

        with tracer.start_as_current_span(
            "cached_mapi.request",
            attributes={"mapi.method": method, "mapi.path": path},
        ) as span:
            # GET: try cache first
            if is_get and self._cache.enabled and self._should_cache(path):
                cache_key = self._cache_key(path, query)
                cached = await self._cache.get(cache_key)
                if cached is not None:
                    span.set_attribute("cache.hit", True)
                    logger.debug("Cache HIT: %s", cache_key)
                    return httpx.Response(
                        status_code=200,
                        json=cached,
                    )
                span.set_attribute("cache.hit", False)

            # Delegate to real MapiService
            resp = await super().request(
                method,
                path,
                host=host,
                body=body,
                query=query,
                content_type=content_type,
                accept=accept,
                username=username,
                password=password,
                auth_type=auth_type,
                raw_body=raw_body,
            )

            if not self._cache.enabled:
                return resp

            if is_get and self._should_cache(path) and 200 <= resp.status_code < 300:
                # Cache the successful GET response
                cache_key = self._cache_key(path, query)
                try:
                    data = resp.json()
                    ttl = self._select_ttl(path)
                    await self._cache.set(cache_key, data, ttl=ttl)
                    span.set_attribute("cache.stored", True)
                    logger.debug("Cache SET: %s (ttl=%d)", cache_key, ttl)
                except ValueError, TypeError:
                    pass  # Non-JSON responses are not cached
            elif not is_get:
                # Write operation: invalidate affected entries
                await self._invalidate_for_write(path)

            return resp

    async def _invalidate_for_write(self, path: str) -> None:
        """Invalidate cache entries affected by a write to *path*.

        Strategy:
        - Invalidate the exact resource + sub-resources: ``mapi:{path}*``
        - Invalidate the parent collection (e.g. writing to
          ``/tenants/t1/namespaces/ns1`` invalidates ``mapi:/tenants/t1/namespaces*``)
        """
        # Invalidate resource and sub-resources
        await self._cache.invalidate_pattern(f"mapi:{path}*")

        # Invalidate parent collection
        parts = path.rstrip("/").rsplit("/", 1)
        if len(parts) == 2:
            parent = parts[0]
            await self._cache.invalidate_pattern(f"mapi:{parent}*")
