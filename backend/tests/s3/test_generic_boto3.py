"""Tests for GenericBoto3Storage adapter (mocked boto3)."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from botocore.exceptions import ClientError

from app.core.config import StorageSettings
from app.services.storage.adapters.generic_boto3 import GenericBoto3Storage
from app.services.storage.errors import StorageError, StorageOperationNotSupported


@pytest.fixture
def storage_settings() -> StorageSettings:
    return StorageSettings(
        storage_backend="minio",
        s3_endpoint_url="http://localhost:9000",
        s3_region="us-east-1",
        s3_verify_ssl=False,
        s3_addressing_style="path",
        s3_access_key="minioadmin",
        s3_secret_key="minioadmin123",
    )


@pytest.fixture
def mock_boto_client() -> MagicMock:
    return MagicMock()


@pytest.fixture
def service(
    storage_settings: StorageSettings, mock_boto_client: MagicMock
) -> GenericBoto3Storage:
    with patch("app.services.storage.adapters.generic_boto3.boto3") as mock_boto3:
        mock_boto3.client.return_value = mock_boto_client
        svc = GenericBoto3Storage(storage_settings)
    return svc


# ── Bucket operations ───────────────────────────────────────────────


def test_list_buckets(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    mock_boto_client.list_buckets.return_value = {"Buckets": [{"Name": "b1"}]}
    result = service.list_buckets()
    assert result["Buckets"][0]["Name"] == "b1"
    mock_boto_client.list_buckets.assert_called_once()


def test_create_bucket(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    service.create_bucket("new-bucket")
    mock_boto_client.create_bucket.assert_called_once_with(Bucket="new-bucket")


def test_head_bucket(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    service.head_bucket("my-bucket")
    mock_boto_client.head_bucket.assert_called_once_with(Bucket="my-bucket")


def test_delete_bucket(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    service.delete_bucket("old-bucket")
    mock_boto_client.delete_bucket.assert_called_once_with(Bucket="old-bucket")


# ── Object operations ──────────────────────────────────────────────


def test_list_objects_basic(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    mock_boto_client.list_objects_v2.return_value = {"Contents": []}
    service.list_objects("bucket")
    mock_boto_client.list_objects_v2.assert_called_once_with(
        Bucket="bucket", MaxKeys=1000, FetchOwner=True
    )


def test_list_objects_with_prefix(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    mock_boto_client.list_objects_v2.return_value = {"Contents": []}
    service.list_objects("bucket", prefix="logs/", max_keys=10)
    mock_boto_client.list_objects_v2.assert_called_once_with(
        Bucket="bucket", MaxKeys=10, Prefix="logs/", FetchOwner=True
    )


def test_put_object(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    body = MagicMock()
    service.put_object("bucket", "key.txt", body)
    mock_boto_client.upload_fileobj.assert_called_once()
    call_args = mock_boto_client.upload_fileobj.call_args
    assert call_args.args[0] is body
    assert call_args.args[1] == "bucket"
    assert call_args.args[2] == "key.txt"


def test_get_object(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    mock_boto_client.get_object.return_value = {"Body": b"data"}
    result = service.get_object("bucket", "key.txt")
    assert result["Body"] == b"data"
    mock_boto_client.get_object.assert_called_once_with(Bucket="bucket", Key="key.txt")


def test_get_object_with_version_id(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    mock_boto_client.get_object.return_value = {"Body": b"data"}
    service.get_object("bucket", "key.txt", version_id="v1")
    mock_boto_client.get_object.assert_called_once_with(
        Bucket="bucket", Key="key.txt", VersionId="v1"
    )


def test_head_object(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    mock_boto_client.head_object.return_value = {"ContentLength": 100}
    result = service.head_object("bucket", "key.txt")
    assert result["ContentLength"] == 100


def test_delete_object(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    service.delete_object("bucket", "key.txt")
    mock_boto_client.delete_object.assert_called_once_with(
        Bucket="bucket", Key="key.txt"
    )


def test_delete_object_with_version_id(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    service.delete_object("bucket", "key.txt", version_id="v1")
    mock_boto_client.delete_object.assert_called_once_with(
        Bucket="bucket", Key="key.txt", VersionId="v1"
    )


def test_copy_object(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    service.copy_object("src-bucket", "src-key", "dst-bucket", "dst-key")
    mock_boto_client.copy_object.assert_called_once_with(
        CopySource={"Bucket": "src-bucket", "Key": "src-key"},
        Bucket="dst-bucket",
        Key="dst-key",
    )


# ── Native batch delete ─────────────────────────────────────────────


def test_delete_objects_native_batch(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    """GenericBoto3Storage uses native delete_objects (not individual deletes)."""
    mock_boto_client.delete_objects.return_value = {"Deleted": []}
    result = service.delete_objects("bucket", ["f1.txt", "f2.txt"])
    assert result == {}
    mock_boto_client.delete_objects.assert_called_once_with(
        Bucket="bucket",
        Delete={
            "Objects": [{"Key": "f1.txt"}, {"Key": "f2.txt"}],
            "Quiet": True,
        },
    )


def test_delete_objects_with_errors(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    mock_boto_client.delete_objects.return_value = {
        "Errors": [{"Key": "f1.txt", "Code": "AccessDenied", "Message": "no access"}]
    }
    result = service.delete_objects("bucket", ["f1.txt"])
    assert len(result["Errors"]) == 1
    assert result["Errors"][0]["Key"] == "f1.txt"


# ── ACL methods raise NotSupported ───────────────────────────────────


def test_get_bucket_acl_raises(service: GenericBoto3Storage):
    with pytest.raises(StorageOperationNotSupported):
        service.get_bucket_acl("bucket")


def test_put_bucket_acl_raises(service: GenericBoto3Storage):
    with pytest.raises(StorageOperationNotSupported):
        service.put_bucket_acl("bucket", {})


def test_get_object_acl_raises(service: GenericBoto3Storage):
    with pytest.raises(StorageOperationNotSupported):
        service.get_object_acl("bucket", "key")


def test_put_object_acl_raises(service: GenericBoto3Storage):
    with pytest.raises(StorageOperationNotSupported):
        service.put_object_acl("bucket", "key", {})


# ── Versioning ──────────────────────────────────────────────────────


def test_get_bucket_versioning(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    mock_boto_client.get_bucket_versioning.return_value = {"Status": "Enabled"}
    result = service.get_bucket_versioning("bucket")
    assert result["Status"] == "Enabled"


def test_put_bucket_versioning(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    service.put_bucket_versioning("bucket", "Suspended")
    mock_boto_client.put_bucket_versioning.assert_called_once_with(
        Bucket="bucket", VersioningConfiguration={"Status": "Suspended"}
    )


# ── Object versions ─────────────────────────────────────────────────


def test_list_object_versions(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    mock_boto_client.list_object_versions.return_value = {
        "Versions": [],
        "DeleteMarkers": [],
    }
    result = service.list_object_versions("bucket")
    assert "Versions" in result


# ── Presigned URLs ───────────────────────────────────────────────────


def test_generate_presigned_url(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    mock_boto_client.generate_presigned_url.return_value = "https://example.com/presign"
    result = service.generate_presigned_url("bucket", "key")
    assert result == "https://example.com/presign"
    mock_boto_client.generate_presigned_url.assert_called_once_with(
        "get_object",
        Params={"Bucket": "bucket", "Key": "key"},
        ExpiresIn=3600,
    )


# ── Multipart uploads ───────────────────────────────────────────────


def test_create_multipart_upload(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    mock_boto_client.create_multipart_upload.return_value = {"UploadId": "u1"}
    result = service.create_multipart_upload("bucket", "key")
    assert result["UploadId"] == "u1"


def test_upload_part(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    body = MagicMock()
    mock_boto_client.upload_part.return_value = {"ETag": '"etag"'}
    result = service.upload_part("bucket", "key", "u1", 1, body)
    assert result["ETag"] == '"etag"'


def test_complete_multipart_upload(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    parts = [{"PartNumber": 1, "ETag": '"etag"'}]
    mock_boto_client.complete_multipart_upload.return_value = {"ETag": '"final"'}
    result = service.complete_multipart_upload("bucket", "key", "u1", parts)
    assert result["ETag"] == '"final"'


def test_abort_multipart_upload(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    service.abort_multipart_upload("bucket", "key", "u1")
    mock_boto_client.abort_multipart_upload.assert_called_once_with(
        Bucket="bucket", Key="key", UploadId="u1"
    )


def test_list_parts(service: GenericBoto3Storage, mock_boto_client: MagicMock):
    mock_boto_client.list_parts.return_value = {"Parts": []}
    result = service.list_parts("bucket", "key", "u1")
    assert result["Parts"] == []


# ── Error wrapping ───────────────────────────────────────────────────


def test_client_error_wraps_to_storage_error(
    service: GenericBoto3Storage, mock_boto_client: MagicMock
):
    mock_boto_client.list_buckets.side_effect = ClientError(
        error_response={
            "Error": {"Code": "AccessDenied", "Message": "forbidden"},
            "ResponseMetadata": {"HTTPStatusCode": 403},
        },
        operation_name="ListBuckets",
    )
    with pytest.raises(StorageError) as exc_info:
        service.list_buckets()
    assert exc_info.value.code == "AccessDenied"
    assert exc_info.value.http_status == 403


# ── with_credentials factory ─────────────────────────────────────────


def test_with_credentials(storage_settings: StorageSettings):
    with patch("app.services.storage.adapters.generic_boto3.boto3") as mock_boto3:
        mock_boto3.client.return_value = MagicMock()
        svc = GenericBoto3Storage.with_credentials(
            storage_settings,
            "mykey",
            "mysecret",
            endpoint_url="http://custom:9000",
        )
    assert svc.settings is storage_settings
