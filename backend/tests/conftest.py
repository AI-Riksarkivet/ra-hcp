"""Shared test fixtures for the HCP Unified API test suite."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from unittest.mock import MagicMock, patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_mapi_service,
    get_mapi_settings,
    get_query_service,
    get_s3_service,
)
import fakeredis

from app.core.config import AuthSettings, CacheSettings, MapiSettings, S3Settings
from app.core.security import create_access_token
from app.main import app
from app.services.cache_service import CacheService
from app.services.mapi_service import AuthenticatedMapiService, MapiService
from app.services.query_service import AuthenticatedQueryService, QueryService
from app.services.storage.protocol import StorageProtocol

# Base URL for MAPI mock routes (must match mapi_settings fixture)
HCP_BASE = "https://test.hcp.example.com:9090/mapi"


# ── Settings fixtures ─────────────────────────────────────────────────


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
def s3_settings() -> S3Settings:
    return S3Settings(
        hcp_username="testuser",
        hcp_password="testpass",
        hcp_verify_ssl=False,
        s3_endpoint_url="https://s3.test.example.com",
        s3_region="us-east-1",
    )


@pytest.fixture
def cache_settings() -> CacheSettings:
    return CacheSettings(
        redis_url="redis://localhost",
        cache_key_prefix="test",
        cache_default_ttl=300,
        cache_stats_ttl=60,
        cache_config_ttl=600,
        cache_s3_list_ttl=120,
        cache_s3_meta_ttl=300,
        cache_query_object_ttl=60,
        cache_query_operation_ttl=120,
    )


@pytest.fixture
def auth_settings() -> AuthSettings:
    return AuthSettings(
        api_secret_key="test-secret-key-for-unit-tests-min32b",
        api_token_expire_minutes=60,
    )


# ── Cache service (fakeredis-backed) ─────────────────────────────────


@pytest.fixture
async def cache(cache_settings: CacheSettings) -> AsyncGenerator[CacheService, None]:
    """CacheService backed by fakeredis — no real Redis needed."""
    svc = CacheService(cache_settings)
    svc._redis = fakeredis.aioredis.FakeRedis(decode_responses=True)
    svc._sync_redis = fakeredis.FakeRedis(decode_responses=True)
    svc._enabled = True
    yield svc
    await svc.close()


# ── Service mocks ────────────────────────────────────────────────────


@pytest.fixture
def mock_s3_service() -> MagicMock:
    """A fully mocked StorageProtocol (boto3 doesn't use httpx)."""
    mock = MagicMock(spec=StorageProtocol)
    mock.list_buckets.return_value = {"Buckets": []}
    mock.create_bucket.return_value = {}
    mock.head_bucket.return_value = {}
    mock.delete_bucket.return_value = {}
    mock.list_objects.return_value = {
        "Contents": [],
        "IsTruncated": False,
        "KeyCount": 0,
    }
    mock.put_object.return_value = None
    mock.get_object.return_value = {
        "Body": MagicMock(iter_chunks=lambda: iter([b"data"])),
        "ContentType": "application/octet-stream",
        "ContentLength": 4,
        "ETag": '"abc123"',
    }
    mock.head_object.return_value = {
        "ContentLength": 100,
        "ContentType": "text/plain",
        "ETag": '"abc123"',
        "LastModified": "2024-01-01T00:00:00Z",
    }
    mock.delete_object.return_value = {}
    mock.copy_object.return_value = {}
    mock.delete_objects.return_value = {"Deleted": [], "Errors": []}
    mock.get_bucket_versioning.return_value = {"Status": "Enabled"}
    mock.put_bucket_versioning.return_value = {}
    mock.get_bucket_acl.return_value = {"Owner": {}, "Grants": []}
    mock.put_bucket_acl.return_value = {}
    mock.get_object_acl.return_value = {"Owner": {}, "Grants": []}
    mock.put_object_acl.return_value = {}
    mock.generate_presigned_url.return_value = (
        "https://s3.test.example.com/my-bucket/test.txt"
        "?AWSAccessKeyId=dGVzdHVzZXI%3D&Expires=9999999999&Signature=abc123"
    )
    mock.list_object_versions.return_value = {
        "Versions": [],
        "DeleteMarkers": [],
        "IsTruncated": False,
    }
    mock.create_multipart_upload.return_value = {
        "Bucket": "my-bucket",
        "Key": "test.txt",
        "UploadId": "upload-000",
    }
    mock.upload_part.return_value = {"ETag": '"mock-etag"'}
    mock.complete_multipart_upload.return_value = {
        "Bucket": "my-bucket",
        "Key": "test.txt",
        "ETag": '"final-etag"',
    }
    mock.abort_multipart_upload.return_value = {}
    mock.list_parts.return_value = {"Parts": [], "IsTruncated": False}
    mock.get_bucket_cors.return_value = {"CORSRules": []}
    mock.put_bucket_cors.return_value = {}
    mock.delete_bucket_cors.return_value = {}
    mock.list_multipart_uploads.return_value = {
        "Uploads": [],
        "IsTruncated": False,
    }
    return mock


@pytest.fixture
def hcp_mock():
    """respx mock context for intercepting HCP MAPI HTTP calls.

    Non-matching requests (e.g. test client via ASGITransport) pass through.
    """
    with respx.mock(assert_all_mocked=False, assert_all_called=False) as mock:
        yield mock


# ── Auth helper ──────────────────────────────────────────────────────


@pytest.fixture
def auth_token(auth_settings: AuthSettings) -> str:
    """A valid JWT token for test requests."""
    return create_access_token("testuser", "testpass", settings=auth_settings)


@pytest.fixture
def auth_headers(auth_token: str) -> dict[str, str]:
    """Authorization headers with valid Bearer token."""
    return {"Authorization": f"Bearer {auth_token}"}


# ── Test client ──────────────────────────────────────────────────────


@pytest.fixture
async def client(
    mock_s3_service: MagicMock,
    mapi_settings: MapiSettings,
    auth_settings: AuthSettings,
    hcp_mock,
) -> AsyncGenerator[AsyncClient, None]:
    """Async test client with mocked S3 and respx-backed MapiService.

    The hcp_mock fixture activates respx.mock so that:
      - MapiService httpx calls are intercepted by respx routes
      - Test client ASGITransport requests pass through (assert_all_mocked=False)
    """
    mapi_svc = MapiService(mapi_settings)
    query_svc = QueryService(mapi_settings)

    auth_mapi = AuthenticatedMapiService(mapi_svc, "testuser", "testpass")
    auth_query = AuthenticatedQueryService(query_svc, "testuser", "testpass")

    async def _override_s3():
        yield mock_s3_service

    async def _override_mapi():
        yield auth_mapi

    async def _override_query():
        yield auth_query

    def _override_mapi_settings():
        return mapi_settings

    app.dependency_overrides[get_s3_service] = _override_s3
    app.dependency_overrides[get_mapi_service] = _override_mapi
    app.dependency_overrides[get_query_service] = _override_query
    app.dependency_overrides[get_mapi_settings] = _override_mapi_settings

    # Provide app.state so non-overridden code (e.g. health) works
    app.state.cache = None
    app.state.mapi = mapi_svc
    app.state.query = query_svc
    app.state.s3_cache = {}

    with patch("app.core.security._get_auth_settings", return_value=auth_settings):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    await query_svc.close()
    await mapi_svc.close()
    app.dependency_overrides.clear()
