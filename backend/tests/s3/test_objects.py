"""Tests for S3 object CRUD endpoints."""

from __future__ import annotations

import asyncio
import io
import zipfile
from datetime import datetime, timezone
from unittest.mock import MagicMock

from botocore.exceptions import ClientError
from httpx import AsyncClient


async def test_list_objects_empty(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.list_objects.return_value = {
        "Contents": [],
        "IsTruncated": False,
        "KeyCount": 0,
    }
    resp = await client.get("/api/v1/buckets/my-bucket/objects", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["objects"] == []
    assert body["is_truncated"] is False
    assert body["key_count"] == 0


async def test_list_objects_with_data(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.list_objects.return_value = {
        "Contents": [
            {
                "Key": "file1.txt",
                "Size": 100,
                "LastModified": datetime(2024, 1, 1, tzinfo=timezone.utc),
                "ETag": '"abc"',
            },
            {
                "Key": "file2.txt",
                "Size": 200,
                "LastModified": datetime(2024, 2, 1, tzinfo=timezone.utc),
                "ETag": '"def"',
            },
        ],
        "IsTruncated": False,
        "KeyCount": 2,
    }
    resp = await client.get("/api/v1/buckets/my-bucket/objects", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["objects"]) == 2
    # FastAPI serializes using aliases (Key, Size)
    assert body["objects"][0]["Key"] == "file1.txt"
    assert body["objects"][0]["Size"] == 100


async def test_list_objects_with_prefix(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.list_objects.return_value = {
        "Contents": [],
        "IsTruncated": False,
        "KeyCount": 0,
    }
    resp = await client.get(
        "/api/v1/buckets/my-bucket/objects",
        headers=auth_headers,
        params={"prefix": "logs/"},
    )
    assert resp.status_code == 200
    mock_s3_service.list_objects.assert_called_once_with(
        "my-bucket", "logs/", 1000, None, None
    )


async def test_list_objects_bucket_not_found(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.list_objects.side_effect = ClientError(
        error_response={
            "Error": {"Code": "NoSuchBucket", "Message": "Not found"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        },
        operation_name="ListObjectsV2",
    )
    resp = await client.get("/api/v1/buckets/missing/objects", headers=auth_headers)
    assert resp.status_code == 404


async def test_upload_object(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    resp = await client.post(
        "/api/v1/buckets/my-bucket/objects/test.txt",
        headers=auth_headers,
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["bucket"] == "my-bucket"
    assert body["key"] == "test.txt"
    assert body["status"] == "uploaded"
    mock_s3_service.put_object.assert_called_once()


async def test_download_object(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.get_object.return_value = {
        "Body": MagicMock(iter_chunks=lambda: iter([b"file content"])),
        "ContentType": "text/plain",
        "ContentLength": 12,
        "ETag": '"etag123"',
    }
    resp = await client.get(
        "/api/v1/buckets/my-bucket/objects/test.txt", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.content == b"file content"


async def test_download_object_not_found(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.get_object.side_effect = ClientError(
        error_response={
            "Error": {"Code": "NoSuchKey", "Message": "Not found"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        },
        operation_name="GetObject",
    )
    resp = await client.get(
        "/api/v1/buckets/my-bucket/objects/missing.txt", headers=auth_headers
    )
    assert resp.status_code == 404


async def test_head_object(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.head_object.return_value = {
        "ContentLength": 1024,
        "ContentType": "application/pdf",
        "ETag": '"hash123"',
        "LastModified": datetime(2024, 3, 15, tzinfo=timezone.utc),
    }
    resp = await client.head(
        "/api/v1/buckets/my-bucket/objects/doc.pdf", headers=auth_headers
    )
    assert resp.status_code == 200


async def test_delete_object(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    resp = await client.delete(
        "/api/v1/buckets/my-bucket/objects/test.txt", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "deleted"
    assert body["key"] == "test.txt"


async def test_copy_object(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    resp = await client.post(
        "/api/v1/buckets/dst-bucket/objects/dst-key/copy",
        headers=auth_headers,
        json={"source_bucket": "src-bucket", "source_key": "src-key"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "copied"
    mock_s3_service.copy_object.assert_called_once_with(
        "src-bucket", "src-key", "dst-bucket", "dst-key"
    )


async def test_delete_objects_bulk(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.delete_objects.return_value = {"Deleted": [], "Errors": []}
    resp = await client.post(
        "/api/v1/buckets/my-bucket/objects/delete",
        headers=auth_headers,
        json={"keys": ["file1.txt", "file2.txt"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["deleted"] == 2
    assert body["errors"] == []


async def test_download_objects_bulk(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Bulk download starts a task (202), then serves a zip archive (200)."""

    def mock_get_object(bucket, key):
        body = io.BytesIO(f"content of {key}".encode())
        return {
            "Body": body,
            "ContentType": "text/plain",
            "ContentLength": body.getbuffer().nbytes,
            "ETag": '"abc"',
        }

    mock_s3_service.get_object.side_effect = mock_get_object
    resp = await client.post(
        "/api/v1/buckets/my-bucket/objects/download",
        headers=auth_headers,
        json={"keys": ["file1.txt", "file2.txt"]},
    )
    assert resp.status_code == 202
    task_id = resp.json()["task_id"]

    # Allow the background task to complete
    await asyncio.sleep(0.1)

    resp = await client.get(
        f"/api/v1/buckets/my-bucket/objects/download/{task_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.headers["content-type"] == "application/zip"

    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    assert sorted(zf.namelist()) == ["file1.txt", "file2.txt"]
    assert zf.read("file1.txt") == b"content of file1.txt"
    assert zf.read("file2.txt") == b"content of file2.txt"


async def test_download_objects_bulk_skips_missing(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Bulk download skips objects that fail to fetch."""

    def mock_get_object(bucket, key):
        if key == "missing.txt":
            raise ClientError(
                error_response={
                    "Error": {"Code": "NoSuchKey", "Message": "Not found"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                operation_name="GetObject",
            )
        body = io.BytesIO(b"data")
        return {
            "Body": body,
            "ContentType": "text/plain",
            "ContentLength": 4,
            "ETag": '"abc"',
        }

    mock_s3_service.get_object.side_effect = mock_get_object
    resp = await client.post(
        "/api/v1/buckets/my-bucket/objects/download",
        headers=auth_headers,
        json={"keys": ["good.txt", "missing.txt"]},
    )
    assert resp.status_code == 202
    task_id = resp.json()["task_id"]

    await asyncio.sleep(0.1)

    resp = await client.get(
        f"/api/v1/buckets/my-bucket/objects/download/{task_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    zf = zipfile.ZipFile(io.BytesIO(resp.content))
    assert zf.namelist() == ["good.txt"]


async def test_download_objects_bulk_empty_keys(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Bulk download rejects empty keys list."""
    resp = await client.post(
        "/api/v1/buckets/my-bucket/objects/download",
        headers=auth_headers,
        json={"keys": []},
    )
    assert resp.status_code == 400


async def test_bulk_presign_returns_urls(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.generate_presigned_url.side_effect = (
        lambda bucket, key, expires_in, *a: (
            f"https://s3.example.com/{bucket}/{key}?sig=abc"
        )
    )
    resp = await client.post(
        "/api/v1/buckets/my-bucket/objects/presign",
        headers=auth_headers,
        json={"keys": ["file1.txt", "file2.txt"], "expires_in": 7200},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["urls"]) == 2
    assert body["urls"][0]["key"] == "file1.txt"
    assert "s3.example.com" in body["urls"][0]["url"]
    assert body["expires_in"] == 7200


async def test_bulk_presign_skips_failed_keys(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    def mock_presign(bucket, key, expires_in, *a):
        if key == "missing.txt":
            raise ClientError(
                error_response={
                    "Error": {"Code": "NoSuchKey", "Message": "Not found"},
                    "ResponseMetadata": {"HTTPStatusCode": 404},
                },
                operation_name="GeneratePresignedUrl",
            )
        return f"https://s3.example.com/{bucket}/{key}?sig=abc"

    mock_s3_service.generate_presigned_url.side_effect = mock_presign
    resp = await client.post(
        "/api/v1/buckets/my-bucket/objects/presign",
        headers=auth_headers,
        json={"keys": ["good.txt", "missing.txt"]},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["urls"]) == 1
    assert body["urls"][0]["key"] == "good.txt"


async def test_bulk_presign_empty_keys(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    resp = await client.post(
        "/api/v1/buckets/my-bucket/objects/presign",
        headers=auth_headers,
        json={"keys": []},
    )
    assert resp.status_code == 422


async def test_get_object_acl(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.get_object_acl.return_value = {
        "Owner": {"ID": "owner-123"},
        "Grants": [],
    }
    resp = await client.get(
        "/api/v1/buckets/my-bucket/objects/test.txt/acl", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["owner"]["ID"] == "owner-123"
    assert body["grants"] == []


async def test_put_object_acl(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    resp = await client.put(
        "/api/v1/buckets/my-bucket/objects/test.txt/acl",
        headers=auth_headers,
        json={"Owner": {"ID": "owner"}, "Grants": []},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"
