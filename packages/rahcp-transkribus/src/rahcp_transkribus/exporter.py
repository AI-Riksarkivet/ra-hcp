"""Plan and run Transkribus collection exports (local dir or, via the CLI, a bucket).

``plan_collection_export`` walks a collection into a flat list of
:class:`ExportItem` (destination key + source URL). ``export_collection`` runs
that plan to a local directory with parallel, tracker-resumable workers. The
bucket path lives in the CLI, which feeds the same items to
``rahcp_client.bulk.bulk_stream_upload`` — this package stays HCP-agnostic.
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections.abc import Callable, Iterable
from enum import StrEnum
from pathlib import Path

from rahcp_tracker import TrackerProtocol, TransferStatus

from rahcp_transkribus.alto import page_bytes_to_alto
from rahcp_transkribus.client import TranskribusClient
from rahcp_transkribus.models import ExportItem, ExportStats, ItemKind, Page
from rahcp_transkribus.versions import TranscriptVersionStore

log = logging.getLogger(__name__)


class ExportFormat(StrEnum):
    """Transcript output format."""

    page = "page"
    alto = "alto"


class _Signal:
    """Queue sentinel distinct from the :class:`ExportItem` values workers consume."""


_DONE = _Signal()


def sanitize_filename(title: str) -> str:
    """Make a document title safe for use as a path segment."""
    cleaned = "".join(c if c.isalnum() or c in " _-" else "_" for c in title).strip()
    return cleaned or "untitled"


def _transcript_name(file_name: str | None, page_nr: int, fmt: ExportFormat) -> str:
    """Derive the transcript output filename, mirroring the medival exporter."""
    if file_name:
        base = Path(file_name).with_suffix(".xml").name
    else:
        base = f"page_{page_nr:04d}.xml"
    if fmt is ExportFormat.alto:
        base = Path(base).with_suffix(".alto.xml").name
    return base


def _plan_page(
    page: Page,
    *,
    collection_id: int,
    doc_id: int,
    slug: str,
    fmt: ExportFormat,
    include_images: bool,
    base_url: str,
) -> list[ExportItem]:
    """Build the export items for a single page (transcript + optional image)."""
    transcripts = page.ts_list.transcripts
    if not transcripts:
        log.debug("doc %d page %d has no transcript, skipping", doc_id, page.page_nr)
        return []

    transcript = transcripts[0]
    xml_name = _transcript_name(transcript.file_name, page.page_nr, fmt)
    sub = "alto" if fmt is ExportFormat.alto else "page"
    url = transcript.url or (
        f"{base_url}/collections/{collection_id}/{doc_id}/{page.page_nr}/text"
    )
    items = [
        ExportItem(
            key=f"{collection_id}/{slug}/{sub}/{xml_name}",
            url=url,
            kind=ItemKind.transcript,
            doc_id=doc_id,
            page_nr=page.page_nr,
            convert_alto=fmt is ExportFormat.alto,
            ts_id=transcript.ts_id,
        )
    ]
    if include_images and page.url:
        img_name = page.img_file_name or f"page_{page.page_nr:04d}.jpg"
        items.append(
            ExportItem(
                key=f"{collection_id}/{slug}/images/{img_name}",
                url=page.url,
                kind=ItemKind.image,
                doc_id=doc_id,
                page_nr=page.page_nr,
            )
        )
    return items


async def plan_collection_export(
    client: TranskribusClient,
    collection_id: int,
    *,
    status: str | None = "GT",
    fmt: ExportFormat = ExportFormat.page,
    skip_missing: bool = True,
    include_images: bool = True,
    doc_ids: Iterable[int] | None = None,
) -> list[ExportItem]:
    """Resolve a collection into a flat list of export items.

    Args:
        client: An entered :class:`TranskribusClient`.
        collection_id: Collection to export.
        status: Transcript status filter (e.g. ``"GT"``; ``None`` = any).
        fmt: Transcript output format (``page`` or ``alto``).
        skip_missing: Skip pages with no transcript at ``status``.
        include_images: Also export each page's image.
        doc_ids: Restrict to these document IDs (``None`` = whole collection).

    Returns:
        Export items across all matching documents. Keys are relative
        (``{collection}/{doc_slug}/{page|alto|images}/{name}``).
    """
    docs = await client.list_docs(collection_id)
    if doc_ids is not None:
        wanted = set(doc_ids)
        docs = [d for d in docs if d.doc_id in wanted]

    items: list[ExportItem] = []
    for doc in docs:
        slug = f"{doc.doc_id}_{sanitize_filename(doc.title)}"
        pages = await client.get_pages(
            collection_id,
            doc.doc_id,
            status=status,
            skip_pages_with_missing_status=skip_missing,
        )
        for page in pages:
            items.extend(
                _plan_page(
                    page,
                    collection_id=collection_id,
                    doc_id=doc.doc_id,
                    slug=slug,
                    fmt=fmt,
                    include_images=include_images,
                    base_url=client.base_url,
                )
            )
    log.info(
        "Planned %d export items for collection %d (%d docs)",
        len(items),
        collection_id,
        len(docs),
    )
    return items


async def fetch_item_bytes(client: TranskribusClient, item: ExportItem) -> bytes:
    """Fetch an item's bytes, converting PAGE→ALTO when the item requests it."""
    data = await client.fetch_bytes(item.url)
    if item.convert_alto:
        data = await asyncio.to_thread(page_bytes_to_alto, data)
    return data


# ── Change detection (transcript versions) ─────────────────────────


def _tracker_key(item: ExportItem, prefix: str) -> str:
    return f"{prefix}{item.key}" if prefix else item.key


def compute_stale_keys(
    items: list[ExportItem],
    synced: dict[str, str],
    *,
    prefix: str = "",
) -> set[str]:
    """Return the tracker keys of transcripts whose version changed since last sync.

    A transcript is *stale* when it was synced before (``synced`` has its key) but
    its current ``ts_id`` differs — i.e. it was re-corrected in Transkribus. New
    transcripts (never synced) are not stale; the normal done-keys logic uploads
    them. Images carry no ``ts_id`` and are never stale.
    """
    stale: set[str] = set()
    for item in items:
        if item.kind is not ItemKind.transcript or item.ts_id is None:
            continue
        key = _tracker_key(item, prefix)
        previous = synced.get(key)
        if previous is not None and previous != str(item.ts_id):
            stale.add(key)
    return stale


def transcript_versions(
    items: list[ExportItem],
    done_keys: set[str],
    *,
    prefix: str = "",
) -> dict[str, str]:
    """Map ``{tracker_key: ts_id}`` for every transcript that is now ``done``.

    Used to update the version store after a run so the next run can detect the
    next round of corrections.
    """
    versions: dict[str, str] = {}
    for item in items:
        if item.kind is not ItemKind.transcript or item.ts_id is None:
            continue
        key = _tracker_key(item, prefix)
        if key in done_keys:
            versions[key] = str(item.ts_id)
    return versions


async def refresh_stale_transcripts(
    items: list[ExportItem],
    tracker: TrackerProtocol,
    store: TranscriptVersionStore,
    done_keys: set[str],
    *,
    prefix: str = "",
) -> set[str]:
    """Drop changed transcripts from the tracker so a re-run re-fetches them.

    Compares each transcript's current ``ts_id`` to the version store, deletes the
    stale keys from ``tracker`` and the in-memory ``done_keys`` set, and returns
    the stale keys. Call before running the transfer; pair with an *overwrite*
    conflict policy so the bucket object is actually replaced.
    """
    synced = await asyncio.to_thread(store.get_all)
    stale = compute_stale_keys(items, synced, prefix=prefix)
    for key in stale:
        await asyncio.to_thread(tracker.delete, key)
        done_keys.discard(key)
    if stale:
        log.info(
            "Change detection: %d transcript(s) changed since last sync", len(stale)
        )
    return stale


async def export_collection(
    client: TranskribusClient,
    collection_id: int,
    output_dir: Path,
    tracker: TrackerProtocol,
    *,
    status: str | None = "GT",
    fmt: ExportFormat = ExportFormat.page,
    skip_missing: bool = True,
    include_images: bool = True,
    prefix: str = "",
    workers: int = 8,
    doc_ids: Iterable[int] | None = None,
    validate_file: Callable[[Path], None] | None = None,
    version_db: Path | None = None,
    on_progress: Callable[[ExportStats], None] | None = None,
    on_error: Callable[[str, Exception], None] | None = None,
    progress_interval: float = 5.0,
) -> ExportStats:
    """Export a Transkribus collection to a local directory, resumably.

    Files already recorded ``done`` in ``tracker`` are skipped instantly.
    Each item is fetched (transcripts optionally converted to ALTO), written
    under ``output_dir/<prefix><key>``, and marked in the tracker.

    Args:
        client: An entered :class:`TranskribusClient`.
        collection_id: Collection to export.
        output_dir: Local root directory to write into.
        tracker: Transfer tracker for resumability.
        status: Transcript status filter (e.g. ``"GT"``).
        fmt: Transcript output format (``page`` or ``alto``).
        skip_missing: Skip pages with no transcript at ``status``.
        include_images: Also export each page's image.
        prefix: Key prefix prepended to every item key.
        workers: Number of concurrent workers.
        doc_ids: Restrict to these document IDs (``None`` = whole collection).
        validate_file: Optional per-file validation callback.
        version_db: Enable change detection — a transcript re-corrected in
            Transkribus (new ``tsId``) is re-fetched even though its path is
            unchanged. State is kept in this SQLite file.
        on_progress: Optional periodic progress callback.
        on_error: Optional per-item error callback.
        progress_interval: Minimum seconds between progress callbacks.

    Returns:
        Export statistics.
    """
    items = await plan_collection_export(
        client,
        collection_id,
        status=status,
        fmt=fmt,
        skip_missing=skip_missing,
        include_images=include_images,
        doc_ids=doc_ids,
    )

    done_keys = await asyncio.to_thread(tracker.done_keys)

    store = TranscriptVersionStore(version_db) if version_db is not None else None
    if store is not None:
        await refresh_stale_transcripts(items, tracker, store, done_keys, prefix=prefix)
    t0 = time.monotonic()
    stats = ExportStats()
    last_report = time.monotonic()
    queue: asyncio.Queue[ExportItem | _Signal] = asyncio.Queue(maxsize=workers * 8)

    log.info(
        "Exporting collection %d → %s: %d items, %d already done, %d workers",
        collection_id,
        output_dir,
        len(items),
        len(done_keys),
        workers,
    )

    def _key(item: ExportItem) -> str:
        return f"{prefix}{item.key}" if prefix else item.key

    async def export_one(item: ExportItem) -> None:
        key = _key(item)
        if key in done_keys:
            stats.skipped += 1
            return

        dest = output_dir / key
        try:
            data = await fetch_item_bytes(client, item)
        except Exception as exc:
            tracker.mark(key, 0, TransferStatus.error, error=f"download: {exc!s}"[:200])
            log.warning("Export failed: %s — %s", key, exc)
            if on_error:
                on_error(key, exc)
            stats.errors += 1
            return

        file_size = len(data)
        await asyncio.to_thread(dest.parent.mkdir, parents=True, exist_ok=True)
        await asyncio.to_thread(dest.write_bytes, data)

        validated = False
        if validate_file:
            try:
                await asyncio.to_thread(validate_file, dest)
                validated = True
            except Exception as exc:
                await asyncio.to_thread(dest.unlink, True)
                tracker.mark(
                    key,
                    file_size,
                    TransferStatus.error,
                    error=f"validation: {exc!s}"[:200],
                )
                log.warning("Validation failed: %s — %s", key, exc)
                if on_error:
                    on_error(key, exc)
                stats.errors += 1
                return

        tracker.mark(key, file_size, TransferStatus.done, validated=validated)
        done_keys.add(key)
        stats.ok += 1
        stats.total_bytes += file_size

    async def worker() -> None:
        nonlocal last_report
        while True:
            item = await queue.get()
            if isinstance(item, _Signal):
                queue.task_done()
                break
            try:
                await export_one(item)
                now = time.monotonic()
                if on_progress and now - last_report >= progress_interval:
                    last_report = now
                    stats.elapsed = now - t0
                    on_progress(stats)
            finally:
                queue.task_done()

    async def produce() -> None:
        for item in items:
            await queue.put(item)
        for _ in range(workers):
            await queue.put(_DONE)

    worker_tasks = [asyncio.create_task(worker()) for _ in range(workers)]
    await produce()
    await asyncio.gather(*worker_tasks)

    await asyncio.to_thread(tracker.commit)
    stats.elapsed = time.monotonic() - t0

    if store is not None:
        await asyncio.to_thread(
            store.set_many, transcript_versions(items, done_keys, prefix=prefix)
        )
        store.close()

    accounted = stats.ok + stats.skipped
    if accounted < len(items):
        log.error(
            "collection %d export incomplete: %d/%d items present (%d errors) — rerun to resume",
            collection_id,
            accounted,
            len(items),
            stats.errors,
        )
    return stats
