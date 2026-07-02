"""Unit tests for the change-detection decision logic and version store."""

from __future__ import annotations

from pathlib import Path

from rahcp_transkribus import (
    ExportItem,
    ItemKind,
    TranscriptVersionStore,
    compute_stale_keys,
    transcript_versions,
)


def _transcript(key: str, ts_id: int) -> ExportItem:
    return ExportItem(
        key=key, url="u", kind=ItemKind.transcript, doc_id=1, page_nr=1, ts_id=ts_id
    )


def _image(key: str) -> ExportItem:
    return ExportItem(key=key, url="u", kind=ItemKind.image, doc_id=1, page_nr=1)


# ── Version store ───────────────────────────────────────────────────


def test_version_store_roundtrip_and_upsert(tmp_path: Path):
    store = TranscriptVersionStore(tmp_path / "v.db")
    store.set_many({"a.xml": "1", "b.xml": "2"})
    assert store.get_all() == {"a.xml": "1", "b.xml": "2"}
    # Upsert: last write wins per key.
    store.set_many({"a.xml": "9"})
    assert store.get_all() == {"a.xml": "9", "b.xml": "2"}
    store.close()


def test_version_store_persists_across_reopen(tmp_path: Path):
    db = tmp_path / "v.db"
    with TranscriptVersionStore(db) as store:
        store.set_many({"k.xml": "5"})
    with TranscriptVersionStore(db) as reopened:
        assert reopened.get_all() == {"k.xml": "5"}


# ── compute_stale_keys ──────────────────────────────────────────────


def test_changed_tsid_is_stale():
    items = [_transcript("t.xml", ts_id=1002)]
    assert compute_stale_keys(items, {"t.xml": "1001"}) == {"t.xml"}


def test_unchanged_tsid_is_not_stale():
    items = [_transcript("t.xml", ts_id=1001)]
    assert compute_stale_keys(items, {"t.xml": "1001"}) == set()


def test_new_transcript_never_synced_is_not_stale():
    # No prior version → it's just "new", handled by normal done-keys logic.
    items = [_transcript("t.xml", ts_id=1001)]
    assert compute_stale_keys(items, {}) == set()


def test_image_is_never_stale_even_if_key_present():
    items = [_image("i.jpg")]
    assert compute_stale_keys(items, {"i.jpg": "whatever"}) == set()


def test_stale_keys_honor_prefix():
    items = [_transcript("t.xml", ts_id=2)]
    assert compute_stale_keys(items, {"ark/t.xml": "1"}, prefix="ark/") == {"ark/t.xml"}


# ── transcript_versions ─────────────────────────────────────────────


def test_records_only_done_transcripts_with_prefix():
    items = [
        _transcript("a.xml", ts_id=1),
        _transcript("b.xml", ts_id=2),  # not done → not recorded
        _image("c.jpg"),  # image → never recorded
    ]
    done = {"p/a.xml", "p/c.jpg"}
    assert transcript_versions(items, done, prefix="p/") == {"p/a.xml": "1"}
