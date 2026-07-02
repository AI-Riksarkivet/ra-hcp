"""Tests for bulk upload/download engine."""

from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest

from rahcp_client.bulk import (
    BulkDownloadConfig,
    BulkUploadConfig,
    ConflictPolicy,
    TransferStats,
    bulk_download,
    bulk_upload,
)
from rahcp_client.bulk.helpers import mark_error
from rahcp_tracker import TransferStatus, TransferTracker

pytestmark = pytest.mark.asyncio


def _make_client():
    """Create a mock HCPClient with S3 operations."""
    from rahcp_client.bulk.protocol import TransferSettings

    client = MagicMock()
    client.s3 = MagicMock()
    client.s3.upload = AsyncMock(return_value='"abc123"')
    client.s3.download = AsyncMock(return_value=100)
    client.s3.head = AsyncMock(side_effect=Exception("not found"))
    client.s3.list_objects = AsyncMock()
    client.transfer_settings = TransferSettings(
        verify_ssl=False, timeout=30.0, multipart_threshold=100 * 1024 * 1024
    )
    return client


# ── Upload ──────────────────────────────────────────────────────────


async def test_bulk_upload_basic(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "a.txt").write_bytes(b"hello")
    (src / "b.txt").write_bytes(b"world")

    client = _make_client()
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="test-bucket",
            source_dir=src,
            tracker=tracker,
            workers=2,
        )
    )

    assert stats.ok == 2
    assert stats.errors == 0
    assert client.s3.upload.call_count == 2
    assert "a.txt" in tracker.done_keys()
    assert "b.txt" in tracker.done_keys()
    tracker.close()


async def test_bulk_upload_skips_done_keys(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "already.txt").write_bytes(b"done")
    (src / "new.txt").write_bytes(b"fresh")

    client = _make_client()
    tracker = TransferTracker(tmp_path / "tracker.db")
    tracker.mark("already.txt", 4, TransferStatus.done)
    tracker.flush()

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="test-bucket",
            source_dir=src,
            tracker=tracker,
            workers=2,
            skip_existing=False,
        )
    )

    assert stats.ok == 1
    # Done keys are filtered in the producer — never reach workers
    assert client.s3.upload.call_count == 1
    tracker.close()


async def test_bulk_upload_records_errors(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "fail.txt").write_bytes(b"data")

    client = _make_client()
    client.s3.upload = AsyncMock(side_effect=Exception("network error"))
    tracker = TransferTracker(tmp_path / "tracker.db")
    errors_seen = []

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="test-bucket",
            source_dir=src,
            tracker=tracker,
            workers=1,
            on_error=lambda key, exc: errors_seen.append(key),
        )
    )

    assert stats.errors == 1
    assert stats.ok == 0
    assert len(tracker.error_entries()) == 1
    assert errors_seen == ["fail.txt"]
    tracker.close()


async def test_bulk_upload_with_prefix(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"data")

    client = _make_client()
    tracker = TransferTracker(tmp_path / "tracker.db")

    await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="test-bucket",
            source_dir=src,
            tracker=tracker,
            prefix="uploads/",
            workers=1,
        )
    )

    call_args = client.s3.upload.call_args
    assert call_args[0][1] == "uploads/file.txt"
    tracker.close()


# ── Download ────────────────────────────────────────────────────────


async def test_bulk_download_basic(tmp_path: Path):
    dest = tmp_path / "dest"
    client = _make_client()
    client.s3.list_objects = AsyncMock(
        return_value={
            "objects": [
                {"Key": "a.txt", "Size": 5},
                {"Key": "b.txt", "Size": 3},
            ],
            "is_truncated": False,
        }
    )

    async def fake_download(bucket, key, tmp_path):
        tmp_path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path.write_bytes(b"x" * 5)
        return 5

    client.s3.download = AsyncMock(side_effect=fake_download)
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_download(
        BulkDownloadConfig(
            client=client,
            bucket="test-bucket",
            dest_dir=dest,
            tracker=tracker,
            workers=2,
        )
    )

    assert stats.ok == 2
    assert stats.errors == 0
    assert (dest / "a.txt").exists()
    assert (dest / "b.txt").exists()
    tracker.close()


async def test_bulk_download_skips_existing(tmp_path: Path):
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "exists.txt").write_bytes(b"hello")

    client = _make_client()
    client.s3.list_objects = AsyncMock(
        return_value={
            "objects": [{"Key": "exists.txt", "Size": 5}],
            "is_truncated": False,
        }
    )
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_download(
        BulkDownloadConfig(
            client=client,
            bucket="test-bucket",
            dest_dir=dest,
            tracker=tracker,
            workers=1,
        )
    )

    assert stats.ok == 0
    assert stats.skipped == 1
    assert client.s3.download.call_count == 0
    tracker.close()


async def test_bulk_download_cleans_up_on_error(tmp_path: Path):
    dest = tmp_path / "dest"
    client = _make_client()
    client.s3.list_objects = AsyncMock(
        return_value={
            "objects": [{"Key": "fail.txt", "Size": 5}],
            "is_truncated": False,
        }
    )
    client.s3.download = AsyncMock(side_effect=Exception("network error"))
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_download(
        BulkDownloadConfig(
            client=client,
            bucket="test-bucket",
            dest_dir=dest,
            tracker=tracker,
            workers=1,
        )
    )

    assert stats.errors == 1
    # .tmp file should be cleaned up
    assert not (dest / "fail.txt.tmp").exists()
    assert not (dest / "fail.txt").exists()
    tracker.close()


async def test_progress_callback_called(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    for i in range(5):
        (src / f"{i}.txt").write_bytes(b"x")

    client = _make_client()
    tracker = TransferTracker(tmp_path / "tracker.db")
    progress_calls = []

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=2,
            progress_interval=0.0,
            on_progress=lambda s: progress_calls.append(s),
        )
    )

    assert stats.ok == 5
    assert len(progress_calls) > 0
    assert all(isinstance(s, TransferStats) for s in progress_calls)
    tracker.close()


# ── Filtering ───────────────────────────────────────────────────────


async def test_include_filter(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "photo.jpg").write_bytes(b"jpg")
    (src / "readme.txt").write_bytes(b"txt")
    (src / "scan.tif").write_bytes(b"tif")

    client = _make_client()
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            include=["*.jpg", "*.tif"],
        )
    )

    assert stats.ok == 2
    assert client.s3.upload.call_count == 2
    tracker.close()


async def test_exclude_filter(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "photo.jpg").write_bytes(b"jpg")
    (src / "temp.tmp").write_bytes(b"tmp")
    (src / "diff.txt").write_bytes(b"txt")

    client = _make_client()
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            exclude=["*.tmp", "*.txt"],
        )
    )

    assert stats.ok == 1
    assert client.s3.upload.call_count == 1
    tracker.close()


async def test_include_and_exclude_combined(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "a.jpg").write_bytes(b"jpg")
    (src / "b.jpg").write_bytes(b"jpg")
    (src / "thumbs.jpg").write_bytes(b"thumb")
    (src / "data.csv").write_bytes(b"csv")

    client = _make_client()
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            include=["*.jpg"],
            exclude=["thumbs*"],
        )
    )

    assert stats.ok == 2
    assert client.s3.upload.call_count == 2
    tracker.close()


# ── Verification ────────────────────────────────────────────────────


async def test_verify_upload_passes(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"hello")

    client = _make_client()
    client.s3.head = AsyncMock(return_value={"content-length": "5"})
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            skip_existing=False,
            verify_upload=True,
        )
    )

    assert stats.ok == 1
    assert stats.errors == 0
    tracker.close()


async def test_verify_upload_fails_on_size_mismatch(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"hello")

    client = _make_client()
    client.s3.head = AsyncMock(return_value={"content-length": "999"})
    tracker = TransferTracker(tmp_path / "tracker.db")
    errors_seen = []

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            skip_existing=False,
            verify_upload=True,
            on_error=lambda key, exc: errors_seen.append(key),
        )
    )

    assert stats.errors == 1
    assert stats.ok == 0
    assert "file.txt" in errors_seen
    tracker.close()


# ── Conflict policy ─────────────────────────────────────────────────


async def test_on_conflict_skip_skips_existing_key(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"hello")

    client = _make_client()
    client.s3.head = AsyncMock(return_value={"content-length": "5"})
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            on_conflict=ConflictPolicy.skip,
        )
    )

    assert stats.skipped == 1
    assert stats.ok == 0
    assert client.s3.upload.call_count == 0
    assert "file.txt" in tracker.done_keys()
    tracker.close()


async def test_on_conflict_skip_size_mismatch_still_skips(tmp_path: Path):
    """A remote key with different content is left alone under skip (warn + skip)."""
    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"hello")

    client = _make_client()
    client.s3.head = AsyncMock(return_value={"content-length": "999"})
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            on_conflict=ConflictPolicy.skip,
        )
    )

    assert stats.skipped == 1
    assert client.s3.upload.call_count == 0
    tracker.close()


async def test_on_conflict_error_records_conflict(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"hello")

    client = _make_client()
    client.s3.head = AsyncMock(return_value={"content-length": "5"})
    tracker = TransferTracker(tmp_path / "tracker.db")
    errors_seen = []

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            on_conflict=ConflictPolicy.error,
            on_error=lambda key, exc: errors_seen.append(key),
        )
    )

    assert stats.errors == 1
    assert stats.ok == 0
    assert client.s3.upload.call_count == 0
    assert errors_seen == ["file.txt"]
    details = tracker.error_details()
    assert len(details) == 1
    assert (details[0][2] or "").startswith("conflict:")
    tracker.close()


async def test_overwrite_deletes_then_retries_on_409(tmp_path: Path):
    """HCP rejects PUT over an existing key with 409; overwrite must delete then re-PUT."""
    from rahcp_client.errors import ConflictError

    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"new-content")

    client = _make_client()
    # First PUT is refused (object exists), second PUT (after delete) succeeds.
    client.s3.upload = AsyncMock(
        side_effect=[ConflictError("exists", status_code=409), '"etag2"']
    )
    client.s3.delete = AsyncMock()
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            on_conflict=ConflictPolicy.overwrite,
        )
    )

    assert stats.ok == 1
    assert stats.errors == 0
    client.s3.delete.assert_awaited_once_with("b", "file.txt")
    assert client.s3.upload.await_count == 2  # rejected, then succeeded after delete
    tracker.close()


async def test_overwrite_errors_if_delete_then_retry_still_fails(tmp_path: Path):
    """If the object can't be replaced (e.g. under retention), it's a real error."""
    from rahcp_client.errors import ConflictError

    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"data")

    client = _make_client()
    client.s3.upload = AsyncMock(side_effect=ConflictError("exists", status_code=409))
    client.s3.delete = AsyncMock()
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            on_conflict=ConflictPolicy.overwrite,
        )
    )

    assert stats.errors == 1
    details = tracker.error_details()
    assert (details[0][2] or "").startswith("overwrite:")
    tracker.close()


async def test_on_conflict_overwrite_uploads_without_head(tmp_path: Path):
    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"hello")

    client = _make_client()
    client.s3.head = AsyncMock(return_value={"content-length": "5"})
    tracker = TransferTracker(tmp_path / "tracker.db")

    stats = await bulk_upload(
        BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=src,
            tracker=tracker,
            workers=1,
            on_conflict=ConflictPolicy.overwrite,
        )
    )

    assert stats.ok == 1
    assert client.s3.upload.call_count == 1
    assert client.s3.head.call_count == 0
    tracker.close()


async def test_conflict_409_during_put_follows_policy(tmp_path: Path):
    from rahcp_client.errors import ConflictError

    src = tmp_path / "source"
    src.mkdir()
    (src / "file.txt").write_bytes(b"hello")

    for policy, expect in [
        (ConflictPolicy.skip, "skipped"),
        (ConflictPolicy.error, "errors"),
        (ConflictPolicy.overwrite, "errors"),
    ]:
        client = _make_client()
        client.s3.upload = AsyncMock(
            side_effect=ConflictError("exists", status_code=409)
        )
        tracker = TransferTracker(tmp_path / f"tracker-{policy}.db")

        stats = await bulk_upload(
            BulkUploadConfig(
                client=client,
                bucket="b",
                source_dir=src,
                tracker=tracker,
                workers=1,
                on_conflict=policy,
            )
        )

        assert getattr(stats, expect) == 1, policy
        tracker.close()


async def test_legacy_skip_existing_maps_to_policy(tmp_path: Path):
    client = _make_client()
    tracker = TransferTracker(tmp_path / "tracker.db")

    def cfg(**overrides) -> BulkUploadConfig:
        return BulkUploadConfig(
            client=client,
            bucket="b",
            source_dir=tmp_path,
            tracker=tracker,
            **overrides,
        )

    assert cfg().conflict_policy() is ConflictPolicy.skip
    assert cfg(skip_existing=False).conflict_policy() is ConflictPolicy.overwrite
    # Explicit on_conflict wins over the legacy bool
    assert (
        cfg(skip_existing=False, on_conflict=ConflictPolicy.error).conflict_policy()
        is ConflictPolicy.error
    )
    tracker.close()


async def test_mark_error_phase_label_and_blank_reason_fallback(tmp_path):
    """Phase is prefixed; a blank-message exception (e.g. ReadError) falls back
    to its class name so the recorded reason is never empty."""
    tracker = TransferTracker(tmp_path / "t.db")
    mark_error(tracker, "a/b.jpg", 100, httpx.ReadError(""), None, phase="upload")
    tracker.flush()

    assert tracker.error_details() == [("a/b.jpg", 100, "upload: ReadError")]
    tracker.close()
