"""Unit tests for CachedS3Service."""

from __future__ import annotations

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest
import fakeredis

from app.core.config import CacheSettings, S3Settings
from app.services.cache_service import CacheService
from app.services.cached_s3 import CachedS3Service


def _s3_settings() -> S3Settings:
    return S3Settings(
        hcp_username="testuser",
        hcp_password="testpass",
        hcp_verify_ssl=False,
        s3_endpoint_url="https://s3.test.example.com",
        s3_region="us-east-1",
    )


def _cache_settings() -> CacheSettings:
    return CacheSettings(
        redis_url="redis://localhost",
        cache_key_prefix="test",
        cache_s3_list_ttl=120,
        cache_s3_meta_ttl=300,
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
def mock_boto_client():
    """Patch boto3.client so S3Service.__init__ doesn't connect."""
    with patch("boto3.client") as m:
        mock_client = MagicMock()
        m.return_value = mock_client
        yield mock_client


@pytest.fixture
def s3(cache: CacheService, mock_boto_client: MagicMock) -> CachedS3Service:
    return CachedS3Service(_s3_settings(), cache, _cache_settings())


# ── list_buckets caching ──────────────────────────────────────────────


def test_list_buckets_cached(s3: CachedS3Service, mock_boto_client: MagicMock):
    mock_boto_client.list_buckets.return_value = {"Buckets": [{"Name": "b1"}]}

    # First call — miss
    result = s3.list_buckets()
    assert result == {"Buckets": [{"Name": "b1"}]}
    assert mock_boto_client.list_buckets.call_count == 1

    # Second call — hit
    result2 = s3.list_buckets()
    assert result2 == {"Buckets": [{"Name": "b1"}]}
    assert mock_boto_client.list_buckets.call_count == 1  # Still 1


# ── head_bucket caching ──────────────────────────────────────────────


def test_head_bucket_cached(s3: CachedS3Service, mock_boto_client: MagicMock):
    mock_boto_client.head_bucket.return_value = {
        "ResponseMetadata": {"HTTPStatusCode": 200}
    }

    s3.head_bucket("mybucket")
    s3.head_bucket("mybucket")
    assert mock_boto_client.head_bucket.call_count == 1


# ── list_objects first page cached, continuation not ──────────────────


def test_list_objects_first_page_cached(
    s3: CachedS3Service, mock_boto_client: MagicMock
):
    mock_boto_client.list_objects_v2.return_value = {
        "Contents": [{"Key": "a.txt"}],
        "IsTruncated": False,
        "KeyCount": 1,
    }

    s3.list_objects("bucket1", prefix="docs/")
    s3.list_objects("bucket1", prefix="docs/")
    assert mock_boto_client.list_objects_v2.call_count == 1


def test_list_objects_continuation_not_cached(
    s3: CachedS3Service, mock_boto_client: MagicMock
):
    mock_boto_client.list_objects_v2.return_value = {
        "Contents": [],
        "IsTruncated": False,
        "KeyCount": 0,
    }

    s3.list_objects("b", continuation_token="tok1")
    s3.list_objects("b", continuation_token="tok1")
    assert mock_boto_client.list_objects_v2.call_count == 2


# ── head_object caching ──────────────────────────────────────────────


def test_head_object_cached(s3: CachedS3Service, mock_boto_client: MagicMock):
    mock_boto_client.head_object.return_value = {"ContentLength": 42}

    s3.head_object("bucket", "key.txt")
    result = s3.head_object("bucket", "key.txt")
    assert result == {"ContentLength": 42}
    assert mock_boto_client.head_object.call_count == 1


# ── get_object is never cached ────────────────────────────────────────


def test_get_object_not_cached(s3: CachedS3Service, mock_boto_client: MagicMock):
    mock_boto_client.get_object.return_value = {"Body": b"data"}

    s3.get_object("bucket", "key.txt")
    s3.get_object("bucket", "key.txt")
    assert mock_boto_client.get_object.call_count == 2


# ── ACL caching ───────────────────────────────────────────────────────


def test_bucket_acl_cached(s3: CachedS3Service, mock_boto_client: MagicMock):
    mock_boto_client.get_bucket_acl.return_value = {"Owner": {}, "Grants": []}

    s3.get_bucket_acl("bucket")
    s3.get_bucket_acl("bucket")
    assert mock_boto_client.get_bucket_acl.call_count == 1


def test_object_acl_cached(s3: CachedS3Service, mock_boto_client: MagicMock):
    mock_boto_client.get_object_acl.return_value = {"Owner": {}, "Grants": []}

    s3.get_object_acl("bucket", "key")
    s3.get_object_acl("bucket", "key")
    assert mock_boto_client.get_object_acl.call_count == 1


# ── versioning caching ───────────────────────────────────────────────


def test_versioning_cached(s3: CachedS3Service, mock_boto_client: MagicMock):
    mock_boto_client.get_bucket_versioning.return_value = {"Status": "Enabled"}

    s3.get_bucket_versioning("bucket")
    s3.get_bucket_versioning("bucket")
    assert mock_boto_client.get_bucket_versioning.call_count == 1


# ── Write invalidation ───────────────────────────────────────────────


def test_create_bucket_invalidates(
    s3: CachedS3Service, mock_boto_client: MagicMock, cache: CacheService
):
    mock_boto_client.list_buckets.return_value = {"Buckets": []}
    mock_boto_client.create_bucket.return_value = {}

    # Populate cache
    s3.list_buckets()
    assert mock_boto_client.list_buckets.call_count == 1

    # Create invalidates list_buckets
    s3.create_bucket("new-bucket")

    # Next list_buckets should miss
    s3.list_buckets()
    assert mock_boto_client.list_buckets.call_count == 2


def test_delete_object_invalidates(
    s3: CachedS3Service, mock_boto_client: MagicMock, cache: CacheService
):
    mock_boto_client.head_object.return_value = {"ContentLength": 10}
    mock_boto_client.delete_object.return_value = {}

    # Populate cache
    s3.head_object("bucket", "file.txt")
    assert mock_boto_client.head_object.call_count == 1

    # Delete invalidates head_object
    s3.delete_object("bucket", "file.txt")

    # Next head_object should miss
    s3.head_object("bucket", "file.txt")
    assert mock_boto_client.head_object.call_count == 2


def test_put_object_invalidates(
    s3: CachedS3Service, mock_boto_client: MagicMock, cache: CacheService
):
    mock_boto_client.list_objects_v2.return_value = {
        "Contents": [],
        "IsTruncated": False,
        "KeyCount": 0,
    }

    # Populate cache
    s3.list_objects("bucket")
    assert mock_boto_client.list_objects_v2.call_count == 1

    # Put object invalidates list_objects
    s3.put_object("bucket", "new.txt", BytesIO(b"data"))

    # Next list_objects should miss
    s3.list_objects("bucket")
    assert mock_boto_client.list_objects_v2.call_count == 2


def test_put_versioning_invalidates(
    s3: CachedS3Service, mock_boto_client: MagicMock, cache: CacheService
):
    mock_boto_client.get_bucket_versioning.return_value = {"Status": "Enabled"}
    mock_boto_client.put_bucket_versioning.return_value = {}

    s3.get_bucket_versioning("bucket")
    assert mock_boto_client.get_bucket_versioning.call_count == 1

    s3.put_bucket_versioning("bucket", "Suspended")

    s3.get_bucket_versioning("bucket")
    assert mock_boto_client.get_bucket_versioning.call_count == 2


def test_put_bucket_acl_invalidates(
    s3: CachedS3Service, mock_boto_client: MagicMock, cache: CacheService
):
    mock_boto_client.get_bucket_acl.return_value = {"Owner": {}, "Grants": []}
    mock_boto_client.put_bucket_acl.return_value = {}

    s3.get_bucket_acl("bucket")
    assert mock_boto_client.get_bucket_acl.call_count == 1

    s3.put_bucket_acl("bucket", {"Owner": {}, "Grants": []})

    s3.get_bucket_acl("bucket")
    assert mock_boto_client.get_bucket_acl.call_count == 2


def test_put_object_acl_invalidates(
    s3: CachedS3Service, mock_boto_client: MagicMock, cache: CacheService
):
    mock_boto_client.get_object_acl.return_value = {"Owner": {}, "Grants": []}
    mock_boto_client.put_object_acl.return_value = {}

    s3.get_object_acl("bucket", "key")
    assert mock_boto_client.get_object_acl.call_count == 1

    s3.put_object_acl("bucket", "key", {"Owner": {}, "Grants": []})

    s3.get_object_acl("bucket", "key")
    assert mock_boto_client.get_object_acl.call_count == 2


def test_copy_object_invalidates_dst(
    s3: CachedS3Service, mock_boto_client: MagicMock, cache: CacheService
):
    mock_boto_client.list_objects_v2.return_value = {
        "Contents": [],
        "IsTruncated": False,
        "KeyCount": 0,
    }
    mock_boto_client.copy_object.return_value = {}

    s3.list_objects("dst-bucket")
    assert mock_boto_client.list_objects_v2.call_count == 1

    s3.copy_object("src-bucket", "src.txt", "dst-bucket", "dst.txt")

    s3.list_objects("dst-bucket")
    assert mock_boto_client.list_objects_v2.call_count == 2


def test_delete_objects_invalidates(
    s3: CachedS3Service, mock_boto_client: MagicMock, cache: CacheService
):
    mock_boto_client.head_object.return_value = {"ContentLength": 10}
    mock_boto_client.delete_objects.return_value = {"Deleted": [], "Errors": []}

    s3.head_object("bucket", "a.txt")
    s3.head_object("bucket", "b.txt")
    assert mock_boto_client.head_object.call_count == 2

    s3.delete_objects("bucket", ["a.txt", "b.txt"])

    # Both should miss cache now
    s3.head_object("bucket", "a.txt")
    s3.head_object("bucket", "b.txt")
    assert mock_boto_client.head_object.call_count == 4
