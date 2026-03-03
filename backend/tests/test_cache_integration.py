"""Integration tests for Redis caching through the full API stack.

These tests wire up CachedMapiService through FastAPI's DI system
with fakeredis, then make real HTTP requests to verify caching works
end-to-end:
  HTTP request → FastAPI router → DI → CachedMapiService → HCP mock → cache
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import fakeredis
import httpx
import pytest
import respx
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_cache_settings,
    get_mapi_service,
    get_mapi_settings,
    get_s3_service,
    reset_instances,
    set_cache_instance,
)
from app.core.config import AuthSettings, CacheSettings, MapiSettings
from app.core.security import create_access_token
from app.main import app
from app.services.cache_service import CacheService
from app.services.cached_mapi import CachedMapiService
from app.services.s3_service import S3Service

HCP_BASE = "https://test.hcp.example.com:9090/mapi"


# ── Fixtures ──────────────────────────────────────────────────────────


@pytest.fixture
def mapi_settings() -> MapiSettings:
    return MapiSettings(
        hcp_host="test.hcp.example.com",
        hcp_port=9090,
        hcp_username="testuser",
        hcp_password="testpass",
        hcp_auth_type="hcp",
        hcp_verify_ssl=False,
        hcp_timeout=30,
    )


@pytest.fixture
def cache_settings() -> CacheSettings:
    return CacheSettings(
        redis_url="redis://fake",
        cache_key_prefix="test",
        cache_default_ttl=300,
        cache_stats_ttl=60,
        cache_config_ttl=600,
        cache_s3_list_ttl=120,
        cache_s3_meta_ttl=300,
    )


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings(
        api_secret_key="test-secret-key-for-unit-tests-min32b",
        api_token_expire_minutes=60,
    )


@pytest.fixture
def auth_headers(auth_settings: AuthSettings) -> dict[str, str]:
    token = create_access_token("testuser", settings=auth_settings)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def cache_service(cache_settings: CacheSettings) -> CacheService:
    """CacheService backed by fakeredis — no real Redis needed."""
    svc = CacheService(cache_settings)
    svc._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    svc._sync_redis = fakeredis.FakeRedis(decode_responses=True)
    svc._enabled = True
    yield svc
    await svc.close()


@pytest.fixture
def mock_s3_service() -> MagicMock:
    mock = MagicMock(spec=S3Service)
    mock.list_buckets.return_value = {
        "Buckets": [{"Name": "bucket-1"}, {"Name": "bucket-2"}],
    }
    mock.head_bucket.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock.list_objects.return_value = {
        "Contents": [{"Key": "file.txt", "Size": 100}],
        "IsTruncated": False,
        "KeyCount": 1,
    }
    mock.head_object.return_value = {
        "ContentLength": 100,
        "ContentType": "text/plain",
        "ETag": '"abc123"',
        "LastModified": "2024-01-01T00:00:00Z",
    }
    return mock


@pytest.fixture
def hcp_mock():
    with respx.mock(assert_all_mocked=False, assert_all_called=False) as mock:
        yield mock


@pytest.fixture
async def cached_client(
    mapi_settings: MapiSettings,
    cache_settings: CacheSettings,
    cache_service: CacheService,
    mock_s3_service: MagicMock,
    auth_settings: AuthSettings,
    hcp_mock,
) -> AsyncClient:
    """Test client with CachedMapiService wired through DI.

    Unlike the default ``client`` fixture (which injects plain MapiService),
    this one injects CachedMapiService backed by fakeredis so we can
    verify caching behavior through the full API stack.
    """
    cached_mapi = CachedMapiService(mapi_settings, cache_service, cache_settings)

    async def _override_mapi():
        yield cached_mapi

    async def _override_s3():
        yield mock_s3_service

    def _override_mapi_settings():
        return mapi_settings

    def _override_cache_settings():
        return cache_settings

    app.dependency_overrides[get_mapi_service] = _override_mapi
    app.dependency_overrides[get_s3_service] = _override_s3
    app.dependency_overrides[get_mapi_settings] = _override_mapi_settings
    app.dependency_overrides[get_cache_settings] = _override_cache_settings

    set_cache_instance(cache_service)

    with patch("app.core.security._get_auth_settings", return_value=auth_settings):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    await cached_mapi.close()
    app.dependency_overrides.clear()
    reset_instances()


# ── MAPI caching: cache hit on repeated GET ───────────────────────────


async def test_mapi_get_cached_on_second_request(
    cached_client: AsyncClient,
    auth_headers: dict,
    hcp_mock: respx.Router,
):
    """GET /tenants hits HCP once; second call returns from cache."""
    route = hcp_mock.get(f"{HCP_BASE}/tenants").mock(
        return_value=httpx.Response(200, json={"name": ["t1", "t2"]})
    )

    resp1 = await cached_client.get("/api/v1/mapi/tenants", headers=auth_headers)
    assert resp1.status_code == 200
    assert resp1.json()["name"] == ["t1", "t2"]
    assert route.call_count == 1

    resp2 = await cached_client.get("/api/v1/mapi/tenants", headers=auth_headers)
    assert resp2.status_code == 200
    assert resp2.json()["name"] == ["t1", "t2"]
    assert route.call_count == 1  # Still 1 — served from cache


# ── MAPI caching: write invalidates cached GET ────────────────────────


async def test_mapi_post_invalidates_cached_get(
    cached_client: AsyncClient,
    auth_headers: dict,
    hcp_mock: respx.Router,
):
    """POST (modify) invalidates cached GET for the parent collection."""
    get_route = hcp_mock.get(f"{HCP_BASE}/tenants/t1/namespaces").mock(
        return_value=httpx.Response(200, json={"name": ["ns1"]})
    )
    # POST /tenants/{t}/namespaces/{ns} = modify namespace (HCP MAPI convention)
    hcp_mock.post(f"{HCP_BASE}/tenants/t1/namespaces/ns1").mock(
        return_value=httpx.Response(200)
    )

    # Populate cache
    resp = await cached_client.get(
        "/api/v1/mapi/tenants/t1/namespaces", headers=auth_headers
    )
    assert resp.status_code == 200
    assert get_route.call_count == 1

    # Confirm cached
    await cached_client.get("/api/v1/mapi/tenants/t1/namespaces", headers=auth_headers)
    assert get_route.call_count == 1

    # POST modify — invalidates cache
    await cached_client.post(
        "/api/v1/mapi/tenants/t1/namespaces/ns1",
        headers=auth_headers,
        json={"hardQuota": "5 GB"},
    )

    # GET now misses cache, hits HCP again
    await cached_client.get("/api/v1/mapi/tenants/t1/namespaces", headers=auth_headers)
    assert get_route.call_count == 2


# ── MAPI caching: modify tenant invalidates tenant listing ────────────


async def test_mapi_modify_tenant_invalidates_listing(
    cached_client: AsyncClient,
    auth_headers: dict,
    hcp_mock: respx.Router,
):
    """POST /tenants/{name} (modify) invalidates cached tenant listing."""
    get_route = hcp_mock.get(f"{HCP_BASE}/tenants").mock(
        return_value=httpx.Response(200, json={"name": ["t1"]})
    )
    hcp_mock.post(f"{HCP_BASE}/tenants/t1").mock(return_value=httpx.Response(200))

    # Cache the tenant list
    await cached_client.get("/api/v1/mapi/tenants", headers=auth_headers)
    assert get_route.call_count == 1

    # Confirm cached
    await cached_client.get("/api/v1/mapi/tenants", headers=auth_headers)
    assert get_route.call_count == 1

    # Modify tenant — invalidates parent listing (/tenants*)
    await cached_client.post(
        "/api/v1/mapi/tenants/t1",
        headers=auth_headers,
        json={"snmpLoggingEnabled": True},
    )

    # Listing should miss cache now
    await cached_client.get("/api/v1/mapi/tenants", headers=auth_headers)
    assert get_route.call_count == 2


# ── MAPI caching: error responses NOT cached ─────────────────────────


async def test_mapi_error_not_cached(
    cached_client: AsyncClient,
    auth_headers: dict,
    hcp_mock: respx.Router,
):
    """4xx/5xx from HCP should NOT be cached."""
    route = hcp_mock.get(f"{HCP_BASE}/tenants/missing").mock(
        return_value=httpx.Response(404)
    )

    await cached_client.get("/api/v1/mapi/tenants/missing", headers=auth_headers)
    await cached_client.get("/api/v1/mapi/tenants/missing", headers=auth_headers)
    assert route.call_count == 2


# ── MAPI caching: no-cache paths always hit HCP ──────────────────────


async def test_mapi_no_cache_paths(
    cached_client: AsyncClient,
    auth_headers: dict,
    hcp_mock: respx.Router,
):
    """/logs, /healthCheck, /support paths should never be cached."""
    route = hcp_mock.get(f"{HCP_BASE}/logs").mock(
        return_value=httpx.Response(200, json={"status": "ready"})
    )

    await cached_client.get("/api/v1/mapi/logs", headers=auth_headers)
    await cached_client.get("/api/v1/mapi/logs", headers=auth_headers)
    assert route.call_count == 2


# ── MAPI caching: different query params = different cache entries ────


async def test_mapi_query_params_cached_separately(
    cached_client: AsyncClient,
    auth_headers: dict,
    hcp_mock: respx.Router,
):
    """Requests with different query params hit HCP separately."""
    route = hcp_mock.get(f"{HCP_BASE}/tenants").mock(
        return_value=httpx.Response(200, json={"name": ["t1"]})
    )

    await cached_client.get("/api/v1/mapi/tenants?verbose=true", headers=auth_headers)
    assert route.call_count == 1

    # Different query params — cache miss
    await cached_client.get("/api/v1/mapi/tenants", headers=auth_headers)
    assert route.call_count == 2

    # Repeat both — both cached now
    await cached_client.get("/api/v1/mapi/tenants?verbose=true", headers=auth_headers)
    await cached_client.get("/api/v1/mapi/tenants", headers=auth_headers)
    assert route.call_count == 2


# ── MAPI caching: nested resource cached independently ────────────────


async def test_mapi_nested_resources_cached_independently(
    cached_client: AsyncClient,
    auth_headers: dict,
    hcp_mock: respx.Router,
):
    """Tenant and namespace listings are cached separately."""
    tenant_route = hcp_mock.get(f"{HCP_BASE}/tenants").mock(
        return_value=httpx.Response(200, json={"name": ["t1"]})
    )
    ns_route = hcp_mock.get(f"{HCP_BASE}/tenants/t1/namespaces").mock(
        return_value=httpx.Response(200, json={"name": ["ns1"]})
    )

    # Cache both
    await cached_client.get("/api/v1/mapi/tenants", headers=auth_headers)
    await cached_client.get("/api/v1/mapi/tenants/t1/namespaces", headers=auth_headers)
    assert tenant_route.call_count == 1
    assert ns_route.call_count == 1

    # Both cached
    await cached_client.get("/api/v1/mapi/tenants", headers=auth_headers)
    await cached_client.get("/api/v1/mapi/tenants/t1/namespaces", headers=auth_headers)
    assert tenant_route.call_count == 1
    assert ns_route.call_count == 1


# ── S3: endpoints still work with caching infrastructure ──────────────


async def test_s3_list_buckets_works_with_cache(
    cached_client: AsyncClient,
    auth_headers: dict,
):
    """S3 endpoints function correctly with caching infrastructure active."""
    resp = await cached_client.get("/api/v1/buckets", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()["buckets"]) == 2


async def test_s3_head_bucket_works_with_cache(
    cached_client: AsyncClient,
    auth_headers: dict,
    mock_s3_service: MagicMock,
):
    resp = await cached_client.head("/api/v1/buckets/test-bucket", headers=auth_headers)
    assert resp.status_code == 200
    mock_s3_service.head_bucket.assert_called_once_with("test-bucket")
