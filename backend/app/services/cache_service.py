"""Async Redis cache wrapper with graceful degradation.

All operations swallow connection errors so the app works normally
when Redis is unavailable.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Optional

import redis as sync_redis
import redis.asyncio as aioredis
from opentelemetry import trace

from app.core.config import CacheSettings

logger = logging.getLogger(__name__)
tracer = trace.get_tracer(__name__)


class CacheService:
    """Async Redis wrapper. Safe to call even when Redis is down.

    Also provides sync variants (get_sync, set_sync, etc.) for use
    inside ``asyncio.to_thread()`` — used by CachedS3Service.
    """

    def __init__(self, settings: CacheSettings):
        self._settings = settings
        self._redis: Optional[aioredis.Redis] = None
        self._sync_redis: Optional[sync_redis.Redis] = None
        self._enabled = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    async def connect(self) -> None:
        """Connect to Redis. If unreachable, disable caching silently."""
        if not self._settings.redis_url:
            logger.info("No REDIS_URL configured — caching disabled")
            return
        try:
            self._redis = aioredis.from_url(
                self._settings.redis_url,
                decode_responses=True,
            )
            await self._redis.ping()
            self._sync_redis = sync_redis.from_url(
                self._settings.redis_url,
                decode_responses=True,
            )
            self._enabled = True
            logger.info("Redis connected — caching enabled")
        except Exception:
            logger.warning("Redis unavailable — caching disabled", exc_info=True)
            self._redis = None
            self._sync_redis = None
            self._enabled = False

    async def close(self) -> None:
        if self._redis is not None:
            try:
                await self._redis.aclose()
            except Exception:
                pass
            self._redis = None
        if self._sync_redis is not None:
            try:
                self._sync_redis.close()
            except Exception:
                pass
            self._sync_redis = None
        self._enabled = False

    def _key(self, key: str) -> str:
        return f"{self._settings.cache_key_prefix}:{key}"

    # ── Async methods (for CachedMapiService) ──────────────────────────

    async def get(self, key: str) -> Optional[Any]:
        if not self._enabled:
            return None
        with tracer.start_as_current_span(
            "cache.get",
            attributes={"cache.key": key},
        ) as span:
            try:
                raw = await self._redis.get(self._key(key))  # type: ignore[union-attr]
                hit = raw is not None
                span.set_attribute("cache.hit", hit)
                if not hit:
                    return None
                return json.loads(raw)
            except Exception:
                span.set_attribute("cache.error", True)
                logger.warning("Cache GET failed for %s", key, exc_info=True)
                return None

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not self._enabled:
            return
        effective_ttl = ttl or self._settings.cache_default_ttl
        with tracer.start_as_current_span(
            "cache.set",
            attributes={"cache.key": key, "cache.ttl": effective_ttl},
        ) as span:
            try:
                raw = json.dumps(value, default=str)
                await self._redis.set(  # type: ignore[union-attr]
                    self._key(key),
                    raw,
                    ex=effective_ttl,
                )
            except Exception:
                span.set_attribute("cache.error", True)
                logger.warning("Cache SET failed for %s", key, exc_info=True)

    async def delete(self, key: str) -> None:
        if not self._enabled:
            return
        with tracer.start_as_current_span(
            "cache.delete",
            attributes={"cache.key": key},
        ) as span:
            try:
                await self._redis.delete(self._key(key))  # type: ignore[union-attr]
            except Exception:
                span.set_attribute("cache.error", True)
                logger.warning("Cache DELETE failed for %s", key, exc_info=True)

    async def invalidate_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern. Uses SCAN for safety."""
        if not self._enabled:
            return 0
        with tracer.start_as_current_span(
            "cache.invalidate",
            attributes={"cache.pattern": pattern},
        ) as span:
            deleted = 0
            try:
                full_pattern = self._key(pattern)
                async for key in self._redis.scan_iter(match=full_pattern):  # type: ignore[union-attr]
                    await self._redis.delete(key)  # type: ignore[union-attr]
                    deleted += 1
                span.set_attribute("cache.keys_deleted", deleted)
            except Exception:
                span.set_attribute("cache.error", True)
                logger.warning("Cache INVALIDATE failed for %s", pattern, exc_info=True)
            return deleted

    # ── Sync methods (for CachedS3Service inside asyncio.to_thread) ───

    def get_sync(self, key: str) -> Optional[Any]:
        if not self._enabled or self._sync_redis is None:
            return None
        with tracer.start_as_current_span(
            "cache.get",
            attributes={"cache.key": key},
        ) as span:
            try:
                raw = self._sync_redis.get(self._key(key))
                hit = raw is not None
                span.set_attribute("cache.hit", hit)
                if not hit:
                    return None
                return json.loads(raw)
            except Exception:
                span.set_attribute("cache.error", True)
                logger.warning("Sync cache GET failed for %s", key, exc_info=True)
                return None

    def set_sync(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not self._enabled or self._sync_redis is None:
            return
        effective_ttl = ttl or self._settings.cache_default_ttl
        with tracer.start_as_current_span(
            "cache.set",
            attributes={"cache.key": key, "cache.ttl": effective_ttl},
        ) as span:
            try:
                raw = json.dumps(value, default=str)
                self._sync_redis.set(self._key(key), raw, ex=effective_ttl)
            except Exception:
                span.set_attribute("cache.error", True)
                logger.warning("Sync cache SET failed for %s", key, exc_info=True)

    def delete_sync(self, key: str) -> None:
        if not self._enabled or self._sync_redis is None:
            return
        with tracer.start_as_current_span(
            "cache.delete",
            attributes={"cache.key": key},
        ) as span:
            try:
                self._sync_redis.delete(self._key(key))
            except Exception:
                span.set_attribute("cache.error", True)
                logger.warning("Sync cache DELETE failed for %s", key, exc_info=True)

    def invalidate_pattern_sync(self, pattern: str) -> int:
        """Blocking pattern invalidation for sync code."""
        if not self._enabled or self._sync_redis is None:
            return 0
        with tracer.start_as_current_span(
            "cache.invalidate",
            attributes={"cache.pattern": pattern},
        ) as span:
            deleted = 0
            try:
                full_pattern = self._key(pattern)
                for key in self._sync_redis.scan_iter(match=full_pattern):
                    self._sync_redis.delete(key)
                    deleted += 1
                span.set_attribute("cache.keys_deleted", deleted)
            except Exception:
                span.set_attribute("cache.error", True)
                logger.warning(
                    "Sync cache INVALIDATE failed for %s", pattern, exc_info=True
                )
            return deleted
