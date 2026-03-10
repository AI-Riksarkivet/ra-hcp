"""Tests for S3 multipart upload endpoints."""

from __future__ import annotations

import io
from unittest.mock import MagicMock

from httpx import AsyncClient


async def test_create_multipart_upload(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Initiating a multipart upload returns bucket, key, and upload_id."""
    mock_s3_service.create_multipart_upload.return_value = {
        "Bucket": "my-bucket",
        "Key": "large-file.bin",
        "UploadId": "upload-123",
    }
    resp = await client.post(
        "/api/v1/buckets/my-bucket/multipart/large-file.bin",
        headers=auth_headers,
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["bucket"] == "my-bucket"
    assert body["key"] == "large-file.bin"
    assert body["upload_id"] == "upload-123"


async def test_upload_part(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Uploading a part returns part_number and etag."""
    mock_s3_service.upload_part.return_value = {"ETag": '"part-etag"'}
    resp = await client.put(
        "/api/v1/buckets/my-bucket/multipart/large-file.bin?upload_id=upload-123&part_number=1",
        headers=auth_headers,
        files={"file": ("chunk", io.BytesIO(b"part data"), "application/octet-stream")},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["part_number"] == 1
    assert body["etag"] == '"part-etag"'


async def test_complete_multipart_upload(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Completing a multipart upload assembles the object."""
    mock_s3_service.complete_multipart_upload.return_value = {
        "Bucket": "my-bucket",
        "Key": "large-file.bin",
        "ETag": '"final-etag"',
    }
    resp = await client.post(
        "/api/v1/buckets/my-bucket/multipart/large-file.bin/complete",
        headers=auth_headers,
        json={
            "upload_id": "upload-123",
            "parts": [
                {"PartNumber": 1, "ETag": '"part1-etag"'},
                {"PartNumber": 2, "ETag": '"part2-etag"'},
            ],
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["bucket"] == "my-bucket"
    assert body["key"] == "large-file.bin"
    assert body["etag"] == '"final-etag"'


async def test_abort_multipart_upload(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Aborting a multipart upload returns status aborted."""
    resp = await client.post(
        "/api/v1/buckets/my-bucket/multipart/large-file.bin/abort",
        headers=auth_headers,
        json={"upload_id": "upload-123"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "aborted"


async def test_list_parts(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Listing parts returns the uploaded parts for a multipart upload."""
    mock_s3_service.list_parts.return_value = {
        "Parts": [
            {"PartNumber": 1, "ETag": '"etag1"', "Size": 5242880},
            {"PartNumber": 2, "ETag": '"etag2"', "Size": 3145728},
        ],
        "IsTruncated": False,
    }
    resp = await client.get(
        "/api/v1/buckets/my-bucket/multipart/large-file.bin/parts?upload_id=upload-123",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["parts"]) == 2
    assert body["parts"][0]["PartNumber"] == 1
    assert body["upload_id"] == "upload-123"
    assert body["is_truncated"] is False
