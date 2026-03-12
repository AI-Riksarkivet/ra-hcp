"""Integration tests exercising Boto3Operations against moto S3 mock.

These tests verify real boto3 call paths (not MagicMock) against an
in-memory S3 backend provided by moto.
"""

from __future__ import annotations

import io

import boto3
import pytest
from boto3.s3.transfer import TransferConfig
from moto import mock_aws

from app.services.storage.adapters._boto3_ops import Boto3Operations
from app.services.storage.errors import StorageError

pytestmark = pytest.mark.moto

BUCKET = "test-bucket"
REGION = "us-east-1"


@pytest.fixture
def s3_ops():
    """Boto3Operations backed by moto with a pre-created bucket."""
    with mock_aws():
        client = boto3.client("s3", region_name=REGION)
        client.create_bucket(Bucket=BUCKET)
        transfer_config = TransferConfig(
            multipart_threshold=8 * 1024 * 1024,
            multipart_chunksize=8 * 1024 * 1024,
        )
        yield Boto3Operations(client, transfer_config)


def test_put_and_get_object(s3_ops: Boto3Operations):
    """Upload an object and retrieve it."""
    s3_ops.put_object(BUCKET, "hello.txt", io.BytesIO(b"Hello, world!"))
    result = s3_ops.get_object(BUCKET, "hello.txt")
    body = result["Body"].read()
    assert body == b"Hello, world!"


def test_head_object(s3_ops: Boto3Operations):
    """HEAD returns correct ContentLength."""
    data = b"some data here"
    s3_ops.put_object(BUCKET, "sized.txt", io.BytesIO(data))
    result = s3_ops.head_object(BUCKET, "sized.txt")
    assert result["ContentLength"] == len(data)


def test_list_objects_with_prefix(s3_ops: Boto3Operations):
    """Prefix filtering returns only matching keys."""
    s3_ops.put_object(BUCKET, "docs/a.txt", io.BytesIO(b"a"))
    s3_ops.put_object(BUCKET, "docs/b.txt", io.BytesIO(b"b"))
    s3_ops.put_object(BUCKET, "images/c.png", io.BytesIO(b"c"))

    result = s3_ops.list_objects(BUCKET, prefix="docs/")
    keys = [obj["Key"] for obj in result.get("Contents", [])]
    assert "docs/a.txt" in keys
    assert "docs/b.txt" in keys
    assert "images/c.png" not in keys


def test_delete_object(s3_ops: Boto3Operations):
    """Deleted object raises NoSuchKey on GET."""
    s3_ops.put_object(BUCKET, "temp.txt", io.BytesIO(b"temp"))
    s3_ops.delete_object(BUCKET, "temp.txt")

    with pytest.raises(StorageError) as exc_info:
        s3_ops.get_object(BUCKET, "temp.txt")
    assert exc_info.value.code == "NoSuchKey"


def test_copy_object(s3_ops: Boto3Operations):
    """Copied object has the same content as the source."""
    s3_ops.put_object(BUCKET, "original.txt", io.BytesIO(b"original content"))
    s3_ops.copy_object(BUCKET, "original.txt", BUCKET, "copy.txt")

    result = s3_ops.get_object(BUCKET, "copy.txt")
    assert result["Body"].read() == b"original content"


def test_create_and_complete_multipart(s3_ops: Boto3Operations):
    """Full multipart flow: create → upload 2 parts → complete → verify."""
    init = s3_ops.create_multipart_upload(BUCKET, "multi.bin")
    upload_id = init["UploadId"]

    part1 = s3_ops.upload_part(
        BUCKET, "multi.bin", upload_id, 1, io.BytesIO(b"A" * 5 * 1024 * 1024)
    )
    part2 = s3_ops.upload_part(
        BUCKET, "multi.bin", upload_id, 2, io.BytesIO(b"B" * 3 * 1024 * 1024)
    )

    s3_ops.complete_multipart_upload(
        BUCKET,
        "multi.bin",
        upload_id,
        [
            {"PartNumber": 1, "ETag": part1["ETag"]},
            {"PartNumber": 2, "ETag": part2["ETag"]},
        ],
    )

    result = s3_ops.get_object(BUCKET, "multi.bin")
    body = result["Body"].read()
    assert len(body) == 5 * 1024 * 1024 + 3 * 1024 * 1024


def test_abort_multipart(s3_ops: Boto3Operations):
    """Aborting a multipart upload invalidates the upload ID."""
    init = s3_ops.create_multipart_upload(BUCKET, "aborted.bin")
    upload_id = init["UploadId"]
    s3_ops.upload_part(BUCKET, "aborted.bin", upload_id, 1, io.BytesIO(b"data"))
    s3_ops.abort_multipart_upload(BUCKET, "aborted.bin", upload_id)

    with pytest.raises(StorageError) as exc_info:
        s3_ops.list_parts(BUCKET, "aborted.bin", upload_id)
    assert exc_info.value.code == "NoSuchUpload"


def test_list_parts(s3_ops: Boto3Operations):
    """Listing parts returns correct count and ETags."""
    init = s3_ops.create_multipart_upload(BUCKET, "parts.bin")
    upload_id = init["UploadId"]

    etags = []
    for i in range(1, 4):
        result = s3_ops.upload_part(
            BUCKET, "parts.bin", upload_id, i, io.BytesIO(f"part-{i}".encode())
        )
        etags.append(result["ETag"])

    parts_resp = s3_ops.list_parts(BUCKET, "parts.bin", upload_id)
    parts = parts_resp["Parts"]
    assert len(parts) == 3
    assert [p["ETag"] for p in parts] == etags

    # Clean up
    s3_ops.abort_multipart_upload(BUCKET, "parts.bin", upload_id)


def test_generate_presigned_url(s3_ops: Boto3Operations):
    """Presigned URL contains expected query parameters."""
    s3_ops.put_object(BUCKET, "signed.txt", io.BytesIO(b"data"))
    url = s3_ops.generate_presigned_url(BUCKET, "signed.txt", expires_in=300)
    assert "signed.txt" in url
    assert "Expires" in url or "X-Amz-Expires" in url


def test_generate_presigned_url_upload_part(s3_ops: Boto3Operations):
    """extra_params (UploadId, PartNumber) appear in the presigned URL."""
    url = s3_ops.generate_presigned_url(
        BUCKET,
        "multi.bin",
        expires_in=600,
        method="upload_part",
        extra_params={"UploadId": "test-upload-id", "PartNumber": 3},
    )
    assert "test-upload-id" in url or "UploadId" in url
    assert "partNumber" in url or "PartNumber" in url


def test_nosuchbucket_raises_storage_error(s3_ops: Boto3Operations):
    """Operations on a non-existent bucket raise StorageError with 404."""
    with pytest.raises(StorageError) as exc_info:
        s3_ops.head_bucket("no-such-bucket-xyz")
    assert exc_info.value.http_status in (404, 400)
