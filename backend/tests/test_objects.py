"""Tests for S3 object CRUD endpoints."""

from __future__ import annotations

import io
from datetime import datetime, timezone
from unittest.mock import MagicMock

from botocore.exceptions import ClientError
from httpx import AsyncClient


async def test_list_objects_empty(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
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


async def test_list_objects_with_data(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    mock_s3_service.list_objects.return_value = {
        "Contents": [
            {"Key": "file1.txt", "Size": 100, "LastModified": datetime(2024, 1, 1, tzinfo=timezone.utc), "ETag": '"abc"'},
            {"Key": "file2.txt", "Size": 200, "LastModified": datetime(2024, 2, 1, tzinfo=timezone.utc), "ETag": '"def"'},
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


async def test_list_objects_with_prefix(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
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
    mock_s3_service.list_objects.assert_called_once_with("my-bucket", "logs/", 1000, None)


async def test_list_objects_bucket_not_found(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    mock_s3_service.list_objects.side_effect = ClientError(
        error_response={
            "Error": {"Code": "NoSuchBucket", "Message": "Not found"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        },
        operation_name="ListObjectsV2",
    )
    resp = await client.get("/api/v1/buckets/missing/objects", headers=auth_headers)
    assert resp.status_code == 404


async def test_upload_object(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    resp = await client.post(
        "/api/v1/buckets/my-bucket/objects/test.txt",
        headers=auth_headers,
        files={"file": ("test.txt", b"hello world", "text/plain")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["bucket"] == "my-bucket"
    assert body["key"] == "test.txt"
    assert body["status"] == "uploaded"
    mock_s3_service.put_object.assert_called_once()


async def test_download_object(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    mock_s3_service.get_object.return_value = {
        "Body": MagicMock(iter_chunks=lambda: iter([b"file content"])),
        "ContentType": "text/plain",
        "ContentLength": 12,
        "ETag": '"etag123"',
    }
    resp = await client.get("/api/v1/buckets/my-bucket/objects/test.txt", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.content == b"file content"


async def test_download_object_not_found(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    mock_s3_service.get_object.side_effect = ClientError(
        error_response={
            "Error": {"Code": "NoSuchKey", "Message": "Not found"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        },
        operation_name="GetObject",
    )
    resp = await client.get("/api/v1/buckets/my-bucket/objects/missing.txt", headers=auth_headers)
    assert resp.status_code == 404


async def test_head_object(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    mock_s3_service.head_object.return_value = {
        "ContentLength": 1024,
        "ContentType": "application/pdf",
        "ETag": '"hash123"',
        "LastModified": datetime(2024, 3, 15, tzinfo=timezone.utc),
    }
    resp = await client.head("/api/v1/buckets/my-bucket/objects/doc.pdf", headers=auth_headers)
    assert resp.status_code == 200


async def test_delete_object(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    resp = await client.delete("/api/v1/buckets/my-bucket/objects/test.txt", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "deleted"
    assert body["key"] == "test.txt"


async def test_copy_object(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    resp = await client.post(
        "/api/v1/buckets/dst-bucket/objects/dst-key/copy",
        headers=auth_headers,
        json={"source_bucket": "src-bucket", "source_key": "src-key"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "copied"
    mock_s3_service.copy_object.assert_called_once_with("src-bucket", "src-key", "dst-bucket", "dst-key")


async def test_delete_objects_bulk(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
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


async def test_get_object_acl(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    mock_s3_service.get_object_acl.return_value = {
        "Owner": {"ID": "owner-123"},
        "Grants": [],
    }
    resp = await client.get("/api/v1/buckets/my-bucket/objects/test.txt/acl", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["owner"]["ID"] == "owner-123"
    assert body["grants"] == []


async def test_put_object_acl(client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock):
    resp = await client.put(
        "/api/v1/buckets/my-bucket/objects/test.txt/acl",
        headers=auth_headers,
        json={"Owner": {"ID": "owner"}, "Grants": []},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"
