"""Unit tests for CachedMapiService."""

from __future__ import annotations

import pytest
import fakeredis
import respx
from httpx import Response

from app.core.config import CacheSettings, MapiSettings
from app.services.cache_service import CacheService
from app.services.cached_mapi import CachedMapiService

HCP_BASE = "https://test.hcp.example.com:9090/mapi"


def _mapi_settings() -> MapiSettings:
    return MapiSettings(
        hcp_host="test.hcp.example.com",
        hcp_port=9090,
        hcp_username="testuser",
        hcp_password="testpass",
        hcp_auth_type="hcp",
        hcp_verify_ssl=False,
        hcp_timeout=30,
    )


def _cache_settings() -> CacheSettings:
    return CacheSettings(
        redis_url="redis://localhost",
        cache_key_prefix="test",
        cache_default_ttl=300,
        cache_stats_ttl=60,
        cache_config_ttl=600,
    )


@pytest.fixture
async def cache() -> CacheService:
    settings = _cache_settings()
    svc = CacheService(settings)
    svc._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    svc._sync_redis = fakeredis.FakeRedis(decode_responses=True)
    svc._enabled = True
    yield svc
    await svc.close()


@pytest.fixture
async def mapi(cache: CacheService) -> CachedMapiService:
    svc = CachedMapiService(_mapi_settings(), cache, _cache_settings())
    yield svc
    await svc.close()


@pytest.fixture
def hcp_mock():
    with respx.mock(assert_all_mocked=False, assert_all_called=False) as mock:
        yield mock


# ── Cache miss → real request → cache populated ───────────────────────


async def test_get_cache_miss_then_hit(
    cache: CacheService, mapi: CachedMapiService, hcp_mock,
):
    route = hcp_mock.get(f"{HCP_BASE}/tenants").respond(
        200, json={"name": ["t1", "t2"]}
    )

    # First call — miss, hits HCP
    resp1 = await mapi.get("/tenants")
    assert resp1.status_code == 200
    assert resp1.json() == {"name": ["t1", "t2"]}
    assert route.call_count == 1

    # Second call — hit, no HCP request
    resp2 = await mapi.get("/tenants")
    assert resp2.status_code == 200
    assert resp2.json() == {"name": ["t1", "t2"]}
    assert route.call_count == 1  # Still 1


# ── Write invalidation ────────────────────────────────────────────────


async def test_put_invalidates_cache(
    cache: CacheService, mapi: CachedMapiService, hcp_mock,
):
    get_route = hcp_mock.get(f"{HCP_BASE}/tenants/t1/namespaces").respond(
        200, json={"name": ["ns1"]}
    )
    put_route = hcp_mock.put(f"{HCP_BASE}/tenants/t1/namespaces/ns1").respond(200)

    # Populate cache
    await mapi.get("/tenants/t1/namespaces")
    assert get_route.call_count == 1

    # Second GET — cache hit, no HCP call
    await mapi.get("/tenants/t1/namespaces")
    assert get_route.call_count == 1  # Still 1

    # Write invalidates
    await mapi.put("/tenants/t1/namespaces/ns1", body={"some": "data"})
    assert put_route.call_count == 1

    # Next GET should miss cache — hits HCP again
    resp = await mapi.get("/tenants/t1/namespaces")
    assert resp.status_code == 200
    assert get_route.call_count == 2  # Now 2 — cache was invalidated


# ── No-cache paths ────────────────────────────────────────────────────


async def test_no_cache_paths(
    cache: CacheService, mapi: CachedMapiService, hcp_mock,
):
    route = hcp_mock.get(f"{HCP_BASE}/logs").respond(200, json={"logs": []})

    await mapi.get("/logs")
    await mapi.get("/logs")
    # Both should hit HCP — /logs is never cached
    assert route.call_count == 2


# ── TTL selection ─────────────────────────────────────────────────────


async def test_ttl_selection(mapi: CachedMapiService):
    assert mapi._select_ttl("/tenants/t1/statistics") == 60  # stats
    assert mapi._select_ttl("/tenants/t1/consoleSecurity") == 600  # config
    assert mapi._select_ttl("/tenants/t1/namespaces") == 300  # default


# ── Cache key includes sorted query params ────────────────────────────


async def test_cache_key_includes_query(mapi: CachedMapiService):
    key1 = mapi._cache_key("/tenants", {"verbose": "true", "offset": "0"})
    key2 = mapi._cache_key("/tenants", {"offset": "0", "verbose": "true"})
    assert key1 == key2  # Sorted, so order doesn't matter
    assert "offset=0" in key1
    assert "verbose=true" in key1


# ── Non-200 responses are not cached ──────────────────────────────────


async def test_error_responses_not_cached(
    cache: CacheService, mapi: CachedMapiService, hcp_mock,
):
    route = hcp_mock.get(f"{HCP_BASE}/tenants/t1").respond(
        404, json={"error": "not found"}
    )

    await mapi.get("/tenants/t1")
    await mapi.get("/tenants/t1")
    # Both should hit HCP — 404 should not be cached
    assert route.call_count == 2


# ── Cache disabled: works without caching ─────────────────────────────


async def test_works_without_cache(hcp_mock):
    """When cache is disabled, CachedMapiService still works normally."""
    cache_settings = CacheSettings(redis_url="", cache_key_prefix="test")
    cache = CacheService(cache_settings)
    await cache.connect()
    assert not cache.enabled

    mapi = CachedMapiService(_mapi_settings(), cache, cache_settings)
    route = hcp_mock.get(f"{HCP_BASE}/tenants").respond(200, json={"name": ["t1"]})

    resp = await mapi.get("/tenants")
    assert resp.json() == {"name": ["t1"]}
    assert route.call_count == 1

    await mapi.close()
    await cache.close()
