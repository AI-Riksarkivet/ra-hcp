"""Completeness verification for IIIF batches.

Re-derives each batch's expected image count from its *live* manifest and
compares it to what the tracker recorded as done. Re-checking against the
manifest (the source of truth) is what catches a batch that was silently
under-counted by a partial/flaky manifest response at download time — a stored
count cannot, because a bad run would have persisted the wrong number.
"""

from __future__ import annotations

import asyncio
import logging
from enum import StrEnum

from pydantic import BaseModel

from rahcp_iiif.config import IIIF_TIMEOUT, IIIF_URL
from rahcp_iiif.manifest import get_image_ids

log = logging.getLogger(__name__)


class BatchState(StrEnum):
    """Outcome of reconciling one batch against its manifest."""

    complete = "complete"
    short = "short"  # some images present, but fewer than the manifest lists
    missing = "missing"  # nothing downloaded, yet the manifest has images
    fetch_error = "fetch_error"  # manifest could not be fetched/parsed


class BatchResult(BaseModel):
    """Reconciliation result for a single batch."""

    batch_id: str
    expected: int | None  # None when the manifest could not be fetched
    got: int
    state: BatchState

    @property
    def missing_count(self) -> int:
        if self.expected is None:
            return 0
        return max(0, self.expected - self.got)


class VerifyReport(BaseModel):
    """Aggregated reconciliation across a set of batches."""

    results: list[BatchResult]

    def _by(self, state: BatchState) -> list[BatchResult]:
        return [r for r in self.results if r.state is state]

    @property
    def complete(self) -> list[BatchResult]:
        return self._by(BatchState.complete)

    @property
    def short(self) -> list[BatchResult]:
        return self._by(BatchState.short)

    @property
    def missing(self) -> list[BatchResult]:
        return self._by(BatchState.missing)

    @property
    def fetch_errors(self) -> list[BatchResult]:
        return self._by(BatchState.fetch_error)

    @property
    def deficient(self) -> list[BatchResult]:
        """Batches that should be re-downloaded (short or never downloaded)."""
        return self.short + self.missing

    @property
    def total_missing_images(self) -> int:
        return sum(r.missing_count for r in self.deficient)


async def verify_batches(
    batch_ids: list[str],
    done_keys: set[str],
    *,
    base_url: str = IIIF_URL,
    timeout: float = IIIF_TIMEOUT,
    headers: dict[str, str] | None = None,
    workers: int = 16,
    attempts: int = 4,
) -> VerifyReport:
    """Reconcile each batch's tracked image count against its live manifest.

    Args:
        batch_ids: Batch identifiers to verify (blank entries are ignored).
        done_keys: Keys the tracker marked done (``tracker.done_keys()``); keys
            look like ``"<batch_id>/<image_id><ext>"``.
        base_url: IIIF server base URL.
        timeout: Per-manifest fetch timeout in seconds.
        headers: Extra HTTP headers (e.g. ``{"Referer": ...}``).
        workers: Maximum concurrent manifest fetches.
        attempts: Manifest-fetch attempts before classifying as ``fetch_error``.

    Returns:
        A :class:`VerifyReport` classifying every batch.
    """
    got_by_batch: dict[str, int] = {}
    for key in done_keys:
        prefix, sep, rest = key.partition("/")
        if sep and rest:
            got_by_batch[prefix] = got_by_batch.get(prefix, 0) + 1

    sem = asyncio.Semaphore(workers)

    async def check(batch_id: str) -> BatchResult:
        got = got_by_batch.get(batch_id, 0)
        async with sem:
            try:
                image_ids = await get_image_ids(
                    batch_id,
                    base_url=base_url,
                    timeout=timeout,
                    attempts=attempts,
                    headers=headers,
                )
            except Exception as exc:
                log.warning("verify: manifest fetch failed for %s — %s", batch_id, exc)
                return BatchResult(
                    batch_id=batch_id,
                    expected=None,
                    got=got,
                    state=BatchState.fetch_error,
                )

        expected = len(image_ids)
        if got == 0 and expected > 0:
            state = BatchState.missing
        elif got < expected:
            state = BatchState.short
        else:
            state = BatchState.complete
        return BatchResult(batch_id=batch_id, expected=expected, got=got, state=state)

    ids = [b.strip() for b in batch_ids if b.strip()]
    results = await asyncio.gather(*(check(b) for b in ids))
    return VerifyReport(results=list(results))
