"""Transkribus CLI subcommands — export ground-truth collections to disk or a bucket."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from rahcp.cli._client import make_client
from rahcp.cli._output import console
from rahcp.cli._run import run
from rahcp_tracker import TrackerProtocol

app = typer.Typer(help="Transkribus collection export operations", no_args_is_help=True)

_CONFLICT_CHOICES = ("overwrite", "skip", "error")


# ── Helpers ────────────────────────────────────────────────────────


def _resolve_transkribus_tracker(
    ctx: typer.Context,
    tracker_db: str | None,
    *,
    prefix: str | None = None,
) -> tuple[TrackerProtocol, Path | str]:
    """Create a tracker for Transkribus exports.

    Accepts a file path or a postgresql:// DSN via --tracker-db. One DB serves
    a whole export; keys embed collection/document/page so there are no
    collisions across documents.
    """
    from rahcp_tracker import create_tracker, redact_dsn

    flush_every = ctx.obj.get("bulk_tracker_flush_every", 500)
    if tracker_db and "://" in tracker_db:
        return create_tracker(tracker_db, flush_every=flush_every), redact_dsn(
            tracker_db
        )

    if tracker_db:
        db_path = Path(tracker_db)
    else:
        config_dir = ctx.obj.get("config_dir", "")
        tracker_dir = Path(config_dir) if config_dir else Path.home() / ".rahcp"
        tracker_dir.mkdir(parents=True, exist_ok=True)
        effective_prefix = prefix or ctx.obj.get("bulk_tracker_prefix", "")
        if effective_prefix:
            db_path = tracker_dir / f"{effective_prefix}.transkribus-export.db"
        else:
            db_path = tracker_dir / ".transkribus-export.db"

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_tracker(db_path, flush_every=flush_every), db_path


def _make_transkribus_client(
    ctx: typer.Context,
    *,
    url: str | None,
    username: str | None,
    password: str | None,
):
    """Build a TranskribusClient from flags/env/profile, validating credentials."""
    from rahcp_transkribus import TranskribusClient

    effective_url = url or ctx.obj.get(
        "transkribus_url", "https://transkribus.eu/TrpServer/rest"
    )
    effective_user = username or ctx.obj.get("transkribus_username", "")
    effective_pw = password or ctx.obj.get("transkribus_password", "")
    if not effective_user or not effective_pw:
        console.print(
            "[red]Transkribus credentials required.[/red]\n"
            "  Pass --username/--password, set TRANSKRIBUS_USERNAME/TRANSKRIBUS_PASSWORD,\n"
            "  or add transkribus_username/transkribus_password to your profile."
        )
        raise SystemExit(1)
    return TranskribusClient(
        effective_user,
        effective_pw,
        base_url=effective_url,
        timeout=ctx.obj.get("transkribus_timeout", 60.0),
    )


def _resolve_format(fmt: str):
    """Validate the --format value and ensure the ALTO toolchain when needed."""
    from rahcp_transkribus import ExportFormat
    from rahcp_transkribus.alto import alto_available

    try:
        export_fmt = ExportFormat(fmt)
    except ValueError:
        console.print(f"[red]Invalid --format '{fmt}' (use: page, alto)[/red]")
        raise SystemExit(1)
    if export_fmt is ExportFormat.alto and not alto_available():
        console.print(
            "[red]--format alto requires the page-to-alto tool.[/red]\n"
            "  Install with: uv pip install 'rahcp-transkribus[alto]'"
        )
        raise SystemExit(1)
    return export_fmt


def _get_validator():
    """Load the file validator from rahcp-validate, or exit if not installed."""
    try:
        from rahcp_validate.images import validate_by_extension
    except ImportError:
        console.print(
            "[red]--validate requires rahcp-validate.[/red]\n"
            "  Install with: uv pip install 'rahcp-cli[validate]'"
        )
        raise SystemExit(1)
    return validate_by_extension


def _get_bytes_validator():
    """Load the in-memory (bytes) validator from rahcp-validate, or exit if absent."""
    try:
        from rahcp_validate import validate_bytes_by_extension
    except ImportError:
        console.print(
            "[red]--validate requires rahcp-validate.[/red]\n"
            "  Install with: uv pip install 'rahcp-cli[validate]'"
        )
        raise SystemExit(1)
    return validate_bytes_by_extension


def _resolve_version_db(
    db_path: "Path | str",
    version_db: str | None,
    *,
    check_updates: bool,
) -> Path | None:
    """Resolve the change-detection version DB path, or None if disabled.

    Explicit --version-db wins. Otherwise it's derived from the tracker path
    (``<tracker>.versions.db``); a postgresql:// tracker DSN has no path to
    derive from, so --version-db is required there.
    """
    if not check_updates:
        return None
    if version_db:
        return Path(version_db)
    if isinstance(db_path, Path):
        return db_path.with_name(db_path.name + ".versions.db")
    console.print(
        "[red]--check-updates with a DSN tracker needs an explicit --version-db path.[/red]"
    )
    raise SystemExit(1)


def _parse_doc_ids(doc_ids: str | None) -> list[int] | None:
    """Parse a comma-separated document-ID filter into a list of ints."""
    if not doc_ids:
        return None
    try:
        return [int(part) for part in doc_ids.split(",") if part.strip()]
    except ValueError:
        console.print(
            f"[red]Invalid --doc-ids '{doc_ids}' (comma-separated ints)[/red]"
        )
        raise SystemExit(1)


def _print_progress(stats) -> None:
    """Display periodic export progress."""
    console.print(
        f"  [{stats.done}] {stats.ok} done, {stats.skipped} skipped,"
        f" {stats.errors} errors — {stats.mb_per_sec:.1f} MB/s",
        highlight=False,
    )


def _print_error(key: str, exc: Exception) -> None:
    """Display a single item error."""
    console.print(f"  [red]{key}[/red] — {str(exc)[:120]}")


def _print_summary(stats, db_path: Path | str, *, verb: str = "Exported") -> None:
    """Display the final export summary."""
    parts = [f"{verb} {stats.ok} files"]
    if stats.skipped:
        parts.append(f"skipped {stats.skipped} existing")
    if stats.errors:
        parts.append(f"[red]{stats.errors} errors[/red]")
    mb = stats.total_bytes / 1024 / 1024
    console.print(
        f"\n[bold]Done.[/bold] {', '.join(parts)} — {mb:,.0f} MB in {stats.elapsed:.0f}s"
    )
    if stats.errors:
        console.print("  Rerun to retry failed items (tracker skips completed ones)")
    console.print(f"  Tracker: [bold]{db_path}[/bold]")


# ── Commands ───────────────────────────────────────────────────────


@app.command("export")
def export(
    ctx: typer.Context,
    collection_id: int = typer.Argument(..., help="Transkribus collection ID"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
    status: str = typer.Option(
        "GT", "--status", "-s", help="Transcript status filter (e.g. GT, FINAL)"
    ),
    fmt: str = typer.Option(
        "page", "--format", "-f", help="Output format: page or alto"
    ),
    images: bool = typer.Option(
        True, "--images/--no-images", help="Also export page images"
    ),
    doc_ids: str | None = typer.Option(
        None, "--doc-ids", help="Restrict to these document IDs (comma-separated)"
    ),
    workers: int = typer.Option(0, "--workers", "-w", help="Concurrent workers"),
    validate: bool = typer.Option(
        False, "--validate", help="Validate each image after download"
    ),
    transkribus_url: str = typer.Option(
        None, "--transkribus-url", envvar="TRANSKRIBUS_URL", help="TRP REST base URL"
    ),
    username: str = typer.Option(
        None,
        "--username",
        "-U",
        envvar="TRANSKRIBUS_USERNAME",
        help="Transkribus login",
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-P",
        envvar="TRANSKRIBUS_PASSWORD",
        help="Transkribus password",
    ),
    tracker_db: str | None = typer.Option(
        None,
        "--tracker-db",
        envvar="RAHCP_TRACKER_DB",
        help="Tracker DB: file path or postgresql:// DSN",
    ),
    tracker_prefix: str | None = typer.Option(
        None, "--tracker-prefix", help="Prefix for tracker DB name"
    ),
    check_updates: bool = typer.Option(
        False,
        "--check-updates",
        help="Re-fetch transcripts corrected in Transkribus since last sync (tsId change)",
    ),
    version_db: str | None = typer.Option(
        None,
        "--version-db",
        help="Change-detection state DB (default: <tracker-db>.versions.db)",
    ),
    fail_on_error: bool = typer.Option(
        True,
        "--fail-on-error/--no-fail-on-error",
        help="Exit non-zero if any item failed (cron-friendly; re-run resumes)",
    ),
) -> None:
    """Export a Transkribus collection (PAGE/ALTO XML + images) to a local directory."""

    async def _run() -> None:
        from rahcp_transkribus import export_collection

        export_fmt = _resolve_format(fmt)
        validate_fn = _get_validator() if validate else None
        doc_id_list = _parse_doc_ids(doc_ids)
        effective_workers = workers or ctx.obj.get("transkribus_workers", 8)
        dest = Path(output_dir)

        tracker, db_path = _resolve_transkribus_tracker(
            ctx, tracker_db, prefix=tracker_prefix
        )
        vdb = _resolve_version_db(db_path, version_db, check_updates=check_updates)
        done_count = len(await asyncio.to_thread(tracker.done_keys))
        console.print(f"Tracker: {db_path} — {done_count} already done")

        flags = [f"status={status}", f"format={export_fmt}"]
        if not images:
            flags.append("no-images")
        if validate:
            flags.append("validate")
        if check_updates:
            flags.append("check-updates")
        console.print(
            f"Exporting collection [bold]{collection_id}[/bold] → {dest}/"
            f" ({effective_workers} workers) [{', '.join(flags)}]"
        )

        client = _make_transkribus_client(
            ctx, url=transkribus_url, username=username, password=password
        )
        async with client:
            stats = await export_collection(
                client,
                collection_id,
                dest,
                tracker,
                status=status,
                fmt=export_fmt,
                include_images=images,
                doc_ids=doc_id_list,
                workers=effective_workers,
                validate_file=validate_fn,
                version_db=vdb,
                on_progress=_print_progress,
                on_error=_print_error,
                progress_interval=ctx.obj.get("bulk_progress_interval", 5.0),
            )

        tracker.close()
        _print_summary(stats, db_path)

        if fail_on_error and stats.errors:
            raise SystemExit(1)

    run(_run())


@app.command("upload")
def upload(
    ctx: typer.Context,
    collection_id: int = typer.Argument(..., help="Transkribus collection ID"),
    bucket: str = typer.Argument(..., help="Target S3 bucket"),
    prefix: str = typer.Option(
        "", "--prefix", "-p", help="Key prefix prepended to the export keys"
    ),
    status: str = typer.Option(
        "GT", "--status", "-s", help="Transcript status filter (e.g. GT, FINAL)"
    ),
    fmt: str = typer.Option(
        "page", "--format", "-f", help="Output format: page or alto"
    ),
    images: bool = typer.Option(
        True, "--images/--no-images", help="Also upload page images"
    ),
    doc_ids: str | None = typer.Option(
        None, "--doc-ids", help="Restrict to these document IDs (comma-separated)"
    ),
    on_conflict: str = typer.Option(
        "skip",
        "--on-conflict",
        help="When a key already exists in the bucket: overwrite | skip | error",
    ),
    archive_dir: str | None = typer.Option(
        None,
        "--archive-dir",
        help="Also write each file to this local directory (keeps a copy while streaming)",
    ),
    workers: int = typer.Option(0, "--workers", "-w", help="Concurrent workers"),
    validate: bool = typer.Option(
        False, "--validate", help="Validate each image's bytes before upload"
    ),
    verify: bool = typer.Option(
        False, "--verify", help="Verify each upload by checking remote size after"
    ),
    fail_on_error: bool = typer.Option(
        True,
        "--fail-on-error/--no-fail-on-error",
        help="Exit non-zero if any item failed (cron-friendly; re-run resumes)",
    ),
    transkribus_url: str = typer.Option(
        None, "--transkribus-url", envvar="TRANSKRIBUS_URL", help="TRP REST base URL"
    ),
    username: str = typer.Option(
        None,
        "--username",
        "-U",
        envvar="TRANSKRIBUS_USERNAME",
        help="Transkribus login",
    ),
    password: str = typer.Option(
        None,
        "--password",
        "-P",
        envvar="TRANSKRIBUS_PASSWORD",
        help="Transkribus password",
    ),
    tracker_db: str | None = typer.Option(
        None,
        "--tracker-db",
        envvar="RAHCP_TRACKER_DB",
        help="Tracker DB: file path or postgresql:// DSN",
    ),
    tracker_prefix: str | None = typer.Option(
        None, "--tracker-prefix", help="Prefix for tracker DB name"
    ),
    check_updates: bool = typer.Option(
        False,
        "--check-updates",
        help="Re-upload transcripts corrected in Transkribus since last sync (implies overwrite)",
    ),
    version_db: str | None = typer.Option(
        None,
        "--version-db",
        help="Change-detection state DB (default: <tracker-db>.versions.db)",
    ),
) -> None:
    """Stream a Transkribus collection straight to an HCP bucket, resumably.

    Transcripts (and, unless --no-images, page images) are fetched from
    Transkribus and pushed through the shared bulk transfer engine in one pass.
    Built for unattended/cron use: the transfer tracker makes it idempotent
    (a re-run skips everything already done), --validate/--verify guard content,
    --on-conflict decides what happens for keys already in the bucket
    (overwrite | skip | error), and --fail-on-error (default) exits non-zero if
    anything failed so a cron can alert. Pass --archive-dir to also keep a local
    copy of every file as it streams, so one run does both the export and the
    bucket upload.
    """

    async def _run() -> None:
        from rahcp_client import BulkStreamConfig, ConflictPolicy, bulk_stream_upload
        from rahcp_transkribus import (
            TranscriptVersionStore,
            fetch_item_bytes,
            plan_collection_export,
            refresh_stale_transcripts,
            transcript_versions,
        )

        export_fmt = _resolve_format(fmt)
        if on_conflict not in _CONFLICT_CHOICES:
            console.print(
                f"[red]Invalid --on-conflict '{on_conflict}'"
                f" (use: {', '.join(_CONFLICT_CHOICES)})[/red]"
            )
            raise SystemExit(1)
        policy = ConflictPolicy(on_conflict)
        doc_id_list = _parse_doc_ids(doc_ids)
        effective_workers = workers or ctx.obj.get("transkribus_workers", 8)
        validate_fn = _get_bytes_validator() if validate else None
        archive_root = Path(archive_dir) if archive_dir else None

        tracker, db_path = _resolve_transkribus_tracker(
            ctx, tracker_db, prefix=tracker_prefix
        )
        vdb = _resolve_version_db(db_path, version_db, check_updates=check_updates)
        if vdb is not None and policy is not ConflictPolicy.overwrite:
            # A changed transcript already has an (old) object in the bucket, so it
            # must be replaced — skip/error would leave the stale copy in place.
            console.print(
                "[dim]--check-updates re-uploads changed transcripts; using"
                " --on-conflict overwrite[/dim]"
            )
            policy = ConflictPolicy.overwrite
        done_count = len(await asyncio.to_thread(tracker.done_keys))
        console.print(f"Tracker: {db_path} — {done_count} already done")

        client = _make_transkribus_client(
            ctx, url=transkribus_url, username=username, password=password
        )
        async with client:
            console.print(
                f"Planning export of collection [bold]{collection_id}[/bold]"
                f" (status={status}, format={export_fmt}) …"
            )
            items = await plan_collection_export(
                client,
                collection_id,
                status=status,
                fmt=export_fmt,
                include_images=images,
                doc_ids=doc_id_list,
            )
            if not items:
                tracker.close()
                console.print("[red]No exportable items found in the collection[/red]")
                raise SystemExit(1)

            store = TranscriptVersionStore(vdb) if vdb is not None else None
            if store is not None:
                stale = await refresh_stale_transcripts(
                    items, tracker, store, set(), prefix=prefix
                )
                if stale:
                    console.print(
                        f"Change detection: [bold]{len(stale)}[/bold]"
                        " transcript(s) changed since last sync — re-uploading"
                    )

            items_by_id = {item.key: item for item in items}
            stream_items = [
                (f"{prefix}{item.key}" if prefix else item.key, item.key)
                for item in items
            ]

            flags = [f"on-conflict={policy}"]
            if validate:
                flags.append("validate")
            if verify:
                flags.append("verify")
            if check_updates:
                flags.append("check-updates")
            if archive_root is not None:
                flags.append(f"archive={archive_root}")
            console.print(
                f"Streaming {len(stream_items)} files → s3://{bucket}/{prefix}"
                f" ({effective_workers} workers) [{', '.join(flags)}]"
            )

            async def fetch(fetch_id: str) -> bytes:
                item = items_by_id[fetch_id]
                data = await fetch_item_bytes(client, item)
                # Tee to a local archive in the same pass — the "export" copy.
                if archive_root is not None:
                    dest = archive_root / item.key
                    await asyncio.to_thread(
                        dest.parent.mkdir, parents=True, exist_ok=True
                    )
                    await asyncio.to_thread(dest.write_bytes, data)
                return data

            async with make_client(ctx) as hcp_client:
                stats = await bulk_stream_upload(
                    BulkStreamConfig(
                        client=hcp_client,
                        bucket=bucket,
                        tracker=tracker,
                        workers=effective_workers,
                        queue_depth=ctx.obj.get("bulk_queue_depth", 8),
                        on_conflict=policy,
                        validate_bytes=validate_fn,
                        verify_upload=verify,
                        presign_batch_size=ctx.obj.get("bulk_presign_batch_size", 200),
                        on_progress=_print_progress,
                        on_error=_print_error,
                        progress_interval=ctx.obj.get("bulk_progress_interval", 5.0),
                    ),
                    stream_items,
                    fetch,
                )

            if store is not None:
                final_done = await asyncio.to_thread(tracker.done_keys)
                await asyncio.to_thread(
                    store.set_many,
                    transcript_versions(items, final_done, prefix=prefix),
                )
                store.close()

        tracker.close()
        _print_summary(stats, db_path, verb="Uploaded")

        if fail_on_error and stats.errors:
            raise SystemExit(1)

    run(_run())
