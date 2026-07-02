"""Persistent record of the last-synced Transkribus transcript version per key.

Transkribus versions transcripts server-side: re-correcting a page's ground truth
creates a new transcript version with a new ``tsId``, but the exported object key
(derived from the page filename) is unchanged. The transfer tracker keys on that
path, so it would treat the corrected transcript as already-done and skip it.

This store remembers the ``tsId`` last synced for each object key. Comparing the
current ``tsId`` (from ``tsList.transcripts[0]``) to the stored one tells a
scheduled re-run which transcripts changed and must be re-fetched — see
``rahcp_transkribus.exporter.compute_stale_keys``.
"""

from __future__ import annotations

import sqlite3
from pathlib import Path
from types import TracebackType


class TranscriptVersionStore:
    """SQLite-backed map of object key → last-synced transcript ``tsId``.

    A tiny sidecar DB (independent of the transfer tracker) so change detection
    adds no coupling to the generic tracker/bulk-transfer packages.
    """

    def __init__(self, db_path: Path) -> None:
        self._path = db_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        # check_same_thread=False: calls are serialized (plan/record boundaries,
        # never concurrent), but may arrive from an asyncio.to_thread worker.
        self._conn = sqlite3.connect(str(db_path), check_same_thread=False)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute(
            "CREATE TABLE IF NOT EXISTS transcript_versions ("
            "key TEXT PRIMARY KEY, ts_id TEXT NOT NULL)"
        )
        self._conn.commit()

    @property
    def path(self) -> Path:
        """Path to the backing SQLite file."""
        return self._path

    def get_all(self) -> dict[str, str]:
        """Return the full ``{key: ts_id}`` map of previously-synced transcripts."""
        cursor = self._conn.execute("SELECT key, ts_id FROM transcript_versions")
        return dict(cursor.fetchall())

    def set_many(self, versions: dict[str, str]) -> None:
        """Upsert ``{key: ts_id}`` (last write wins per key)."""
        if not versions:
            return
        self._conn.executemany(
            "INSERT INTO transcript_versions(key, ts_id) VALUES(?, ?) "
            "ON CONFLICT(key) DO UPDATE SET ts_id=excluded.ts_id",
            list(versions.items()),
        )
        self._conn.commit()

    def close(self) -> None:
        """Close the backing connection."""
        self._conn.close()

    def __enter__(self) -> TranscriptVersionStore:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()
