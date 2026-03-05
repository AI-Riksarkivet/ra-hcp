"""Tests for app.services.s3_service.S3Service (mocked boto3)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from app.core.config import S3Settings
from app.services.s3_service import S3Service


@pytest.fixture
def s3_settings() -> S3Settings:
    return S3Settings(
        hcp_username="testuser",
        hcp_password="testpass",
        hcp_verify_ssl=False,
        s3_endpoint_url="https://s3.test.com",
        s3_region="us-east-1",
    )


@pytest.fixture
def mock_boto_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(s3_settings: S3Settings, mock_boto_client: MagicMock) -> S3Service:
    with patch("app.services.s3_service.boto3") as mock_boto3:
        mock_boto3.client.return_value = mock_boto_client
        svc = S3Service(s3_settings)
    return svc


# ── Bucket operations ───────────────────────────────────────────────


def test_list_buckets(service: S3Service, mock_boto_client: MagicMock):
    mock_boto_client.list_buckets.return_value = {"Buckets": [{"Name": "b1"}]}
    result = service.list_buckets()
    assert result["Buckets"][0]["Name"] == "b1"
    mock_boto_client.list_buckets.assert_called_once()


def test_create_bucket(service: S3Service, mock_boto_client: MagicMock):
    service.create_bucket("new-bucket")
    mock_boto_client.create_bucket.assert_called_once_with(Bucket="new-bucket")


def test_head_bucket(service: S3Service, mock_boto_client: MagicMock):
    service.head_bucket("my-bucket")
    mock_boto_client.head_bucket.assert_called_once_with(Bucket="my-bucket")


def test_delete_bucket(service: S3Service, mock_boto_client: MagicMock):
    service.delete_bucket("old-bucket")
    mock_boto_client.delete_bucket.assert_called_once_with(Bucket="old-bucket")


# ── Object operations ──────────────────────────────────────────────


def test_list_objects_basic(service: S3Service, mock_boto_client: MagicMock):
    mock_boto_client.list_objects_v2.return_value = {"Contents": []}
    service.list_objects("bucket")
    mock_boto_client.list_objects_v2.assert_called_once_with(
        Bucket="bucket", MaxKeys=1000, FetchOwner=True
    )


def test_list_objects_with_prefix_and_token(
    service: S3Service, mock_boto_client: MagicMock
):
    mock_boto_client.list_objects_v2.return_value = {"Contents": []}
    service.list_objects(
        "bucket", prefix="logs/", max_keys=10, continuation_token="tok123"
    )
    mock_boto_client.list_objects_v2.assert_called_once_with(
        Bucket="bucket",
        MaxKeys=10,
        Prefix="logs/",
        ContinuationToken="tok123",
        FetchOwner=True,
    )


def test_put_object(service: S3Service, mock_boto_client: MagicMock):
    body = MagicMock()
    service.put_object("bucket", "key.txt", body)
    mock_boto_client.upload_fileobj.assert_called_once()
    call_args = mock_boto_client.upload_fileobj.call_args
    assert call_args.args[0] is body
    assert call_args.args[1] == "bucket"
    assert call_args.args[2] == "key.txt"


def test_get_object(service: S3Service, mock_boto_client: MagicMock):
    mock_boto_client.get_object.return_value = {"Body": b"data"}
    result = service.get_object("bucket", "key.txt")
    assert result["Body"] == b"data"
    mock_boto_client.get_object.assert_called_once_with(Bucket="bucket", Key="key.txt")


def test_head_object(service: S3Service, mock_boto_client: MagicMock):
    mock_boto_client.head_object.return_value = {"ContentLength": 100}
    result = service.head_object("bucket", "key.txt")
    assert result["ContentLength"] == 100


def test_delete_object(service: S3Service, mock_boto_client: MagicMock):
    service.delete_object("bucket", "key.txt")
    mock_boto_client.delete_object.assert_called_once_with(
        Bucket="bucket", Key="key.txt"
    )


def test_copy_object(service: S3Service, mock_boto_client: MagicMock):
    service.copy_object("src-bucket", "src-key", "dst-bucket", "dst-key")
    mock_boto_client.copy_object.assert_called_once_with(
        CopySource={"Bucket": "src-bucket", "Key": "src-key"},
        Bucket="dst-bucket",
        Key="dst-key",
    )


def test_delete_objects(service: S3Service, mock_boto_client: MagicMock):
    result = service.delete_objects("bucket", ["f1.txt", "f2.txt"])
    assert mock_boto_client.delete_object.call_count == 2
    assert result == {}


# ── Versioning ──────────────────────────────────────────────────────


def test_get_bucket_versioning(service: S3Service, mock_boto_client: MagicMock):
    mock_boto_client.get_bucket_versioning.return_value = {"Status": "Enabled"}
    result = service.get_bucket_versioning("bucket")
    assert result["Status"] == "Enabled"


def test_put_bucket_versioning(service: S3Service, mock_boto_client: MagicMock):
    service.put_bucket_versioning("bucket", "Suspended")
    mock_boto_client.put_bucket_versioning.assert_called_once_with(
        Bucket="bucket",
        VersioningConfiguration={"Status": "Suspended"},
    )


# ── ACLs ────────────────────────────────────────────────────────────


def test_get_bucket_acl(service: S3Service, mock_boto_client: MagicMock):
    mock_boto_client.get_bucket_acl.return_value = {"Owner": {}, "Grants": []}
    result = service.get_bucket_acl("bucket")
    assert "Owner" in result


def test_put_bucket_acl(service: S3Service, mock_boto_client: MagicMock):
    acl = {"Owner": {"ID": "owner"}, "Grants": []}
    service.put_bucket_acl("bucket", acl)
    mock_boto_client.put_bucket_acl.assert_called_once_with(
        Bucket="bucket",
        AccessControlPolicy=acl,
    )


def test_get_object_acl(service: S3Service, mock_boto_client: MagicMock):
    mock_boto_client.get_object_acl.return_value = {"Owner": {}, "Grants": []}
    service.get_object_acl("bucket", "key")
    mock_boto_client.get_object_acl.assert_called_once_with(Bucket="bucket", Key="key")


def test_put_object_acl(service: S3Service, mock_boto_client: MagicMock):
    acl = {"Owner": {"ID": "owner"}, "Grants": []}
    service.put_object_acl("bucket", "key", acl)
    mock_boto_client.put_object_acl.assert_called_once_with(
        Bucket="bucket",
        Key="key",
        AccessControlPolicy=acl,
    )
