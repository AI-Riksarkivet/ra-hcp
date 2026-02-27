"""Shared test fixtures for the HCP Unified API test suite."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
import respx
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import (
    get_mapi_service,
    get_mapi_settings,
    get_s3_service,
    reset_instances,
)
from app.core.config import AuthSettings, MapiSettings, S3Settings
from app.core.security import create_access_token
from app.main import app
from app.services.mapi_service import MapiService
from app.services.s3_service import S3Service

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
def auth_settings() -> AuthSettings:
    return AuthSettings(
        api_secret_key="test-secret-key-for-unit-tests-min32b",
        api_token_expire_minutes=60,
    )


# ── Service mocks ────────────────────────────────────────────────────


@pytest.fixture
def mock_s3_service() -> MagicMock:
    """A fully mocked S3Service (boto3 doesn't use httpx)."""
    mock = MagicMock(spec=S3Service)
    mock.list_buckets.return_value = {"Buckets": []}
    mock.create_bucket.return_value = {}
    mock.head_bucket.return_value = {}
    mock.delete_bucket.return_value = {}
    mock.list_objects.return_value = {"Contents": [], "IsTruncated": False, "KeyCount": 0}
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
    return create_access_token("testuser", settings=auth_settings)


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
) -> AsyncClient:
    """Async test client with mocked S3 and respx-backed MapiService.

    The hcp_mock fixture activates respx.mock so that:
      - MapiService httpx calls are intercepted by respx routes
      - Test client ASGITransport requests pass through (assert_all_mocked=False)
    """
    mapi_svc = MapiService(mapi_settings)

    async def _override_s3():
        yield mock_s3_service

    async def _override_mapi():
        yield mapi_svc

    def _override_mapi_settings():
        return mapi_settings

    app.dependency_overrides[get_s3_service] = _override_s3
    app.dependency_overrides[get_mapi_service] = _override_mapi
    app.dependency_overrides[get_mapi_settings] = _override_mapi_settings

    with patch("app.core.security._get_auth_settings", return_value=auth_settings):
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    await mapi_svc.close()
    app.dependency_overrides.clear()
    reset_instances()
