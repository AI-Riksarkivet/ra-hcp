"""Tests for S3 bucket endpoints.

Business logic tests for: force-delete (empty → retry → MAPI reconfigure),
version deletion pagination, error aggregation. Serialization-only tests
are deliberately omitted — they test FastAPI, not our code.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from httpx import AsyncClient

from app.api.v1.endpoints.s3.buckets import _format_delete_errors
from app.services.storage.errors import StorageError, StorageOperationNotSupported


def test_format_delete_errors_caps_and_formats():
    errs = [
        {"Key": f"k{i}", "Code": "AccessDenied", "Message": "denied"} for i in range(10)
    ]
    out = _format_delete_errors(errs, limit=3)
    assert out == [f"k{i}: AccessDenied denied" for i in range(3)]
    # A non-positive limit (cap already reached) yields nothing.
    assert _format_delete_errors(errs, limit=0) == []


# ── Force-delete business logic ───────────────────────────────────


async def test_force_delete_empties_bucket_then_deletes(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """force=true must empty all objects/versions before deleting."""
    # Bucket has 2 objects and no versions
    mock_s3_service.list_object_versions.return_value = {
        "Versions": [],
        "DeleteMarkers": [],
        "IsTruncated": False,
    }
    mock_s3_service.list_objects.return_value = {
        "Contents": [{"Key": "a.txt"}, {"Key": "b.txt"}],
        "IsTruncated": False,
    }
    mock_s3_service.delete_objects.return_value = {"Errors": []}

    resp = await client.delete(
        "/api/v1/buckets/my-bucket?force=true", headers=auth_headers
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    # Must have called delete_objects with the 2 keys
    mock_s3_service.delete_objects.assert_called_once_with(
        "my-bucket", ["a.txt", "b.txt"]
    )
    # Must have called delete_bucket after emptying
    mock_s3_service.delete_bucket.assert_called()


async def test_force_delete_paginates_versions(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Version deletion paginates through all markers and BATCHES each page."""
    empty_versions = {"Versions": [], "DeleteMarkers": [], "IsTruncated": False}
    mock_s3_service.list_object_versions.side_effect = [
        # First call to _delete_all_versions — 2 pages
        {
            "Versions": [{"Key": "f1.txt", "VersionId": "v1"}],
            "DeleteMarkers": [{"Key": "f2.txt", "VersionId": "dm1"}],
            "IsTruncated": True,
            "NextKeyMarker": "f2.txt",
            "NextVersionIdMarker": "dm1",
        },
        {
            "Versions": [{"Key": "f3.txt", "VersionId": "v2"}],
            "DeleteMarkers": [],
            "IsTruncated": False,
        },
        # Second call to _delete_all_versions (cleanup pass) — empty
        empty_versions,
    ]
    mock_s3_service.delete_object_versions.return_value = {"Errors": []}
    mock_s3_service.list_objects.return_value = {
        "Contents": [],
        "IsTruncated": False,
    }

    resp = await client.delete(
        "/api/v1/buckets/my-bucket?force=true", headers=auth_headers
    )
    assert resp.status_code == 200
    # ONE batched delete per non-empty page — never one DeleteObject per version.
    assert mock_s3_service.delete_object.call_count == 0
    assert mock_s3_service.delete_object_versions.call_count == 2
    mock_s3_service.delete_object_versions.assert_any_call(
        "my-bucket", [("f1.txt", "v1"), ("f2.txt", "dm1")]
    )
    mock_s3_service.delete_object_versions.assert_any_call(
        "my-bucket", [("f3.txt", "v2")]
    )


async def test_force_delete_batches_versions_and_reports_errors(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """All versions on a page go in a single batch; per-key errors are non-fatal."""
    empty_versions = {"Versions": [], "DeleteMarkers": [], "IsTruncated": False}
    mock_s3_service.list_object_versions.side_effect = [
        {
            "Versions": [{"Key": f"f{i}.txt", "VersionId": f"v{i}"} for i in range(7)],
            "DeleteMarkers": [],
            "IsTruncated": False,
        },
        empty_versions,  # cleanup pass
    ]
    mock_s3_service.delete_object_versions.return_value = {
        "Errors": [
            {"Key": f"f{i}.txt", "Code": "AccessDenied", "Message": "denied"}
            for i in range(7)
        ]
    }
    mock_s3_service.list_objects.return_value = {
        "Contents": [],
        "IsTruncated": False,
    }

    resp = await client.delete(
        "/api/v1/buckets/my-bucket?force=true", headers=auth_headers
    )
    assert resp.status_code == 200
    # All 7 versions deleted in ONE batch call (not 7 calls); errors non-fatal.
    mock_s3_service.delete_object_versions.assert_called_once_with(
        "my-bucket", [(f"f{i}.txt", f"v{i}") for i in range(7)]
    )


async def test_delete_bucket_not_empty_without_force(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """Without force=true, BucketNotEmpty propagates as 409."""
    mock_s3_service.delete_bucket.side_effect = StorageError(
        "BucketNotEmpty", "Not empty", 409
    )
    resp = await client.delete("/api/v1/buckets/full-bucket", headers=auth_headers)
    assert resp.status_code == 409


# ── CORS not supported ────────────────────────────────────────────


async def test_cors_not_supported_returns_501(
    client: AsyncClient, auth_headers: dict, mock_s3_service: MagicMock
):
    """StorageOperationNotSupported translates to 501."""
    mock_s3_service.get_bucket_cors.side_effect = StorageOperationNotSupported(
        "get_bucket_cors", "minio"
    )
    resp = await client.get("/api/v1/buckets/my-bucket/cors", headers=auth_headers)
    assert resp.status_code == 501
