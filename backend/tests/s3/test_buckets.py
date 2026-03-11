"""Tests for S3 bucket CRUD endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from httpx import AsyncClient

from app.services.storage.errors import StorageError


async def test_list_buckets_empty(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.list_buckets.return_value = {"Buckets": []}
    resp = await client.get("/api/v1/buckets", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"buckets": [], "owner": None}


async def test_list_buckets_with_data(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.list_buckets.return_value = {
        "Buckets": [
            {
                "Name": "bucket-1",
                "CreationDate": datetime(2024, 1, 1, tzinfo=timezone.utc),
            },
            {
                "Name": "bucket-2",
                "CreationDate": datetime(2024, 6, 15, tzinfo=timezone.utc),
            },
        ],
        "Owner": {"DisplayName": "testuser", "ID": "user123"},
    }
    resp = await client.get("/api/v1/buckets", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["buckets"]) == 2
    assert body["buckets"][0]["Name"] == "bucket-1"
    assert body["buckets"][1]["Name"] == "bucket-2"
    assert body["owner"]["DisplayName"] == "testuser"
    assert body["owner"]["ID"] == "user123"


async def test_create_bucket_success(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    resp = await client.post(
        "/api/v1/buckets",
        headers=auth_headers,
        json={"bucket": "new-bucket"},
    )
    assert resp.status_code == 201
    assert resp.json()["status"] == "created"
    assert resp.json()["bucket"] == "new-bucket"
    mock_s3_service.create_bucket.assert_called_once_with("new-bucket")


async def test_create_bucket_already_exists(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.create_bucket.side_effect = StorageError(
        "BucketAlreadyOwnedByYou", "Bucket exists", 409
    )
    resp = await client.post(
        "/api/v1/buckets",
        headers=auth_headers,
        json={"bucket": "existing-bucket"},
    )
    assert resp.status_code == 409


async def test_head_bucket_exists(client: AsyncClient, auth_headers: dict):
    resp = await client.head("/api/v1/buckets/my-bucket", headers=auth_headers)
    assert resp.status_code == 200


async def test_head_bucket_not_found(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.head_bucket.side_effect = StorageError(
        "NoSuchBucket", "Not found", 404
    )
    resp = await client.head("/api/v1/buckets/missing-bucket", headers=auth_headers)
    assert resp.status_code == 404


async def test_delete_bucket_success(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    resp = await client.delete("/api/v1/buckets/my-bucket", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    mock_s3_service.delete_bucket.assert_called_once_with("my-bucket")


async def test_delete_bucket_not_empty(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.delete_bucket.side_effect = StorageError(
        "BucketNotEmpty", "Not empty", 409
    )
    resp = await client.delete("/api/v1/buckets/full-bucket", headers=auth_headers)
    assert resp.status_code == 409


async def test_get_bucket_versioning(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.get_bucket_versioning.return_value = {
        "Status": "Enabled",
        "MFADelete": "Disabled",
    }
    resp = await client.get(
        "/api/v1/buckets/my-bucket/versioning", headers=auth_headers
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "Enabled"
    assert body["mfa_delete"] == "Disabled"
