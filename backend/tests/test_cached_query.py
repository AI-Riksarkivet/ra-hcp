"""Unit tests for CachedQueryService."""

from __future__ import annotations

from collections.abc import AsyncGenerator

import fakeredis
import pytest
import respx

from app.core.config import CacheSettings, MapiSettings
from app.schemas.query import ObjectQuery, OperationQuery
from app.services.cache_service import CacheService
from app.services.cached_query import CachedQueryService

QUERY_URL = "https://mock.hcp.example.com/query"


def _settings() -> MapiSettings:
    return MapiSettings(
        hcp_host="mock.hcp.example.com",
        hcp_domain="hcp.example.com",
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
        cache_query_object_ttl=60,
        cache_query_operation_ttl=120,
    )


@pytest.fixture
async def cache() -> AsyncGenerator[CacheService, None]:
    settings = _cache_settings()
    svc = CacheService(settings)
    svc._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    svc._sync_redis = fakeredis.FakeRedis(decode_responses=True)
    svc._enabled = True
    yield svc
    await svc.close()


@pytest.fixture
async def query_svc(cache: CacheService) -> AsyncGenerator[CachedQueryService, None]:
    svc = CachedQueryService(_settings(), cache, _cache_settings())
    yield svc
    await svc.close()


@pytest.fixture
def query_mock():
    with respx.mock(assert_all_mocked=False, assert_all_called=False) as mock:
        yield mock


_OBJ_RESPONSE = {
    "status": {"totalResults": 2, "results": 2, "code": "COMPLETE"},
    "resultSet": [
        {
            "urlName": "/docs/a.pdf",
            "operation": "CREATED",
            "changeTimeMilliseconds": "1706745600000",
            "version": "0",
        },
        {
            "urlName": "/docs/b.pdf",
            "operation": "CREATED",
            "changeTimeMilliseconds": "1707350400000",
            "version": "0",
        },
    ],
}

_OP_RESPONSE = {
    "status": {"totalResults": 1, "results": 1, "code": "COMPLETE"},
    "resultSet": [
        {
            "urlName": "/docs/a.pdf",
            "operation": "DELETED",
            "changeTimeMilliseconds": "1710460800000",
            "version": "0",
        },
    ],
}


# ── Object query: cache miss → cache hit ──────────────────────────────


async def test_object_query_cache_miss_then_hit(
    query_svc: CachedQueryService, query_mock
):
    route = query_mock.post(QUERY_URL).respond(200, json=_OBJ_RESPONSE)

    # First call — miss, hits HCP
    r1 = await query_svc.object_query(
        "mock",
        ObjectQuery(query="*:*", count=5),
        username="testuser",
        password="testpass",
    )
    assert r1.status.total_results == 2
    assert route.call_count == 1

    # Second call — hit, no HCP request
    r2 = await query_svc.object_query(
        "mock",
        ObjectQuery(query="*:*", count=5),
        username="testuser",
        password="testpass",
    )
    assert r2.status.total_results == 2
    assert route.call_count == 1  # Still 1


# ── Operation query: cache miss → cache hit ───────────────────────────


async def test_operation_query_cache_miss_then_hit(
    query_svc: CachedQueryService, query_mock
):
    route = query_mock.post(QUERY_URL).respond(200, json=_OP_RESPONSE)

    r1 = await query_svc.operation_query(
        "mock", OperationQuery(count=10), username="testuser", password="testpass"
    )
    assert r1.status.total_results == 1
    assert route.call_count == 1

    r2 = await query_svc.operation_query(
        "mock", OperationQuery(count=10), username="testuser", password="testpass"
    )
    assert r2.status.total_results == 1
    assert route.call_count == 1  # Still 1


# ── Different params create separate cache entries ────────────────────


async def test_different_params_miss_cache(query_svc: CachedQueryService, query_mock):
    route = query_mock.post(QUERY_URL).respond(200, json=_OBJ_RESPONSE)

    await query_svc.object_query(
        "mock",
        ObjectQuery(query="*:*", count=5),
        username="testuser",
        password="testpass",
    )
    assert route.call_count == 1

    # Different count → different cache key → miss
    await query_svc.object_query(
        "mock",
        ObjectQuery(query="*:*", count=10),
        username="testuser",
        password="testpass",
    )
    assert route.call_count == 2


# ── Cache disabled: works without caching ─────────────────────────────


async def test_works_without_cache(query_mock):
    cache_settings = CacheSettings(redis_url="", cache_key_prefix="test")
    cache = CacheService(cache_settings)
    await cache.connect()
    assert not cache.enabled

    svc = CachedQueryService(_settings(), cache, cache_settings)
    route = query_mock.post(QUERY_URL).respond(200, json=_OBJ_RESPONSE)

    r1 = await svc.object_query(
        "mock", ObjectQuery(query="*:*"), username="testuser", password="testpass"
    )
    assert r1.status.total_results == 2

    # Without cache, second call should also hit HCP
    r2 = await svc.object_query(
        "mock", ObjectQuery(query="*:*"), username="testuser", password="testpass"
    )
    assert r2.status.total_results == 2
    assert route.call_count == 2

    await svc.close()
    await cache.close()
