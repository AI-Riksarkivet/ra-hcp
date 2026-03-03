"""Tests for S3 bucket CRUD endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

from botocore.exceptions import ClientError
from httpx import AsyncClient


async def test_list_buckets_empty(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.list_buckets.return_value = {"Buckets": []}
    resp = await client.get("/api/v1/buckets", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == {"buckets": []}


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
        ]
    }
    resp = await client.get("/api/v1/buckets", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["buckets"]) == 2
    # FastAPI serializes using aliases (Name, CreationDate)
    assert body["buckets"][0]["Name"] == "bucket-1"
    assert body["buckets"][1]["Name"] == "bucket-2"


async def test_create_bucket_success(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    resp = await client.post(
        "/api/v1/buckets",
        headers=auth_headers,
        json={"bucket": "new-bucket"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "created"
    assert resp.json()["bucket"] == "new-bucket"
    mock_s3_service.create_bucket.assert_called_once_with("new-bucket")


async def test_create_bucket_already_exists(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.create_bucket.side_effect = ClientError(
        error_response={
            "Error": {"Code": "BucketAlreadyOwnedByYou", "Message": "Bucket exists"},
            "ResponseMetadata": {"HTTPStatusCode": 409},
        },
        operation_name="CreateBucket",
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
    mock_s3_service.head_bucket.side_effect = ClientError(
        error_response={
            "Error": {"Code": "NoSuchBucket", "Message": "Not found"},
            "ResponseMetadata": {"HTTPStatusCode": 404},
        },
        operation_name="HeadBucket",
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
    mock_s3_service.delete_bucket.side_effect = ClientError(
        error_response={
            "Error": {"Code": "BucketNotEmpty", "Message": "Not empty"},
            "ResponseMetadata": {"HTTPStatusCode": 409},
        },
        operation_name="DeleteBucket",
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


async def test_put_bucket_versioning(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    resp = await client.put(
        "/api/v1/buckets/my-bucket/versioning",
        headers=auth_headers,
        json={"status": "Enabled"},
    )
    assert resp.status_code == 200
    assert resp.json()["versioning"] == "Enabled"
    mock_s3_service.put_bucket_versioning.assert_called_once_with(
        "my-bucket", "Enabled"
    )


async def test_get_bucket_acl(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    mock_s3_service.get_bucket_acl.return_value = {
        "Owner": {"ID": "owner-id"},
        "Grants": [
            {"Grantee": {"Type": "CanonicalUser"}, "Permission": "FULL_CONTROL"}
        ],
    }
    resp = await client.get("/api/v1/buckets/my-bucket/acl", headers=auth_headers)
    assert resp.status_code == 200
    body = resp.json()
    assert body["owner"]["ID"] == "owner-id"
    assert len(body["grants"]) == 1


async def test_put_bucket_acl(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    acl_body = {"Owner": {"ID": "owner-id"}, "Grants": []}
    resp = await client.put(
        "/api/v1/buckets/my-bucket/acl",
        headers=auth_headers,
        json=acl_body,
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "updated"
