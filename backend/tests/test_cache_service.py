"""Unit tests for CacheService."""

from __future__ import annotations

import pytest
import fakeredis

from app.core.config import CacheSettings
from app.services.cache_service import CacheService


def _settings(url: str = "redis://localhost") -> CacheSettings:
    return CacheSettings(redis_url=url, cache_key_prefix="test")


@pytest.fixture
async def cache() -> CacheService:
    """CacheService backed by fakeredis."""
    settings = _settings()
    svc = CacheService(settings)
    # Inject fakeredis instances directly
    svc._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    svc._sync_redis = fakeredis.FakeRedis(decode_responses=True)
    svc._enabled = True
    yield svc
    await svc.close()


# ── Basic get/set/delete ───────────────────────────────────────────────


async def test_get_returns_none_on_miss(cache: CacheService):
    assert await cache.get("nonexistent") is None


async def test_set_and_get(cache: CacheService):
    await cache.set("key1", {"hello": "world"}, ttl=60)
    result = await cache.get("key1")
    assert result == {"hello": "world"}


async def test_delete(cache: CacheService):
    await cache.set("key1", "value")
    await cache.delete("key1")
    assert await cache.get("key1") is None


async def test_set_with_datetime(cache: CacheService):
    """datetime objects are serialized via default=str."""
    from datetime import datetime

    data = {"ts": datetime(2024, 1, 1, 12, 0)}
    await cache.set("dt", data)
    result = await cache.get("dt")
    assert result["ts"] == "2024-01-01 12:00:00"


# ── Pattern invalidation ──────────────────────────────────────────────


async def test_invalidate_pattern(cache: CacheService):
    await cache.set("mapi:/tenants/t1", "a")
    await cache.set("mapi:/tenants/t1/namespaces", "b")
    await cache.set("mapi:/tenants/t2", "c")

    deleted = await cache.invalidate_pattern("mapi:/tenants/t1*")
    assert deleted == 2
    assert await cache.get("mapi:/tenants/t1") is None
    assert await cache.get("mapi:/tenants/t1/namespaces") is None
    # t2 should survive
    assert await cache.get("mapi:/tenants/t2") == "c"


# ── Sync variants ─────────────────────────────────────────────────────


async def test_sync_get_set_delete(cache: CacheService):
    cache.set_sync("skey", {"sync": True}, ttl=60)
    assert cache.get_sync("skey") == {"sync": True}
    cache.delete_sync("skey")
    assert cache.get_sync("skey") is None


async def test_sync_invalidate_pattern(cache: CacheService):
    cache.set_sync("s3:list_objects:bucket1:a", "x")
    cache.set_sync("s3:list_objects:bucket1:b", "y")
    cache.set_sync("s3:list_objects:bucket2:a", "z")

    deleted = cache.invalidate_pattern_sync("s3:list_objects:bucket1:*")
    assert deleted == 2
    assert cache.get_sync("s3:list_objects:bucket2:a") == "z"


# ── Graceful degradation ──────────────────────────────────────────────


async def test_disabled_when_no_url():
    svc = CacheService(_settings(url=""))
    await svc.connect()
    assert not svc.enabled
    # All ops are no-ops
    assert await svc.get("k") is None
    await svc.set("k", "v")
    await svc.delete("k")
    assert await svc.invalidate_pattern("*") == 0
    assert svc.get_sync("k") is None
    await svc.close()


async def test_ops_dont_raise_when_redis_broken(cache: CacheService):
    """If the Redis connection breaks mid-operation, ops return gracefully."""
    # Force-close the underlying connection
    await cache._redis.aclose()

    # Async ops should not raise
    assert await cache.get("k") is None
    await cache.set("k", "v")
    await cache.delete("k")
    assert await cache.invalidate_pattern("*") == 0
