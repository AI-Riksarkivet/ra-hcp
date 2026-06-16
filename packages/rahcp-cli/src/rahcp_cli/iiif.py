"""IIIF CLI subcommands — download images from Riksarkivet IIIF endpoints."""

from __future__ import annotations

import asyncio
from pathlib import Path

import typer

from rahcp_cli._client import make_client
from rahcp_cli._output import console
from rahcp_cli._run import run
from rahcp_tracker import TrackerProtocol, TransferStatus

app = typer.Typer(help="IIIF image download operations", no_args_is_help=True)


# ── Helpers ────────────────────────────────────────────────────────


def _resolve_iiif_tracker(
    ctx: typer.Context,
    tracker_db: str | None,
    *,
    prefix: str | None = None,
) -> tuple[TrackerProtocol, Path | str]:
    """Create a tracker for IIIF downloads.

    Accepts a file path or a postgresql:// DSN via --tracker-db. Uses a single
    DB for all IIIF downloads (like .upload-tracker.db for S3). Keys include
    the batch ID so there are no collisions.
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
        default_name = ".iiif-download.db"
        if effective_prefix:
            db_path = tracker_dir / f"{effective_prefix}.iiif-download.db"
        else:
            db_path = tracker_dir / default_name

    db_path.parent.mkdir(parents=True, exist_ok=True)
    return create_tracker(db_path, flush_every=flush_every), db_path


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


def _print_progress(stats) -> None:
    """Display periodic IIIF download progress."""
    console.print(
        f"  [{stats.done}] {stats.ok} downloaded, {stats.skipped} skipped,"
        f" {stats.errors} errors — {stats.mb_per_sec:.1f} MB/s",
        highlight=False,
    )


def _print_error(key: str, exc: Exception) -> None:
    """Display a single download error."""
    console.print(f"  [red]{key}[/red] — {str(exc)[:120]}")


def _print_summary(stats, db_path: Path | str, *, verb: str = "Downloaded") -> None:
    """Display final transfer summary."""
    parts = [f"{verb} {stats.ok} images"]
    if stats.skipped:
        parts.append(f"skipped {stats.skipped} existing")
    if stats.errors:
        parts.append(f"[red]{stats.errors} errors[/red]")
    mb = stats.total_bytes / 1024 / 1024
    console.print(
        f"\n[bold]Done.[/bold] {', '.join(parts)} — {mb:,.0f} MB in {stats.elapsed:.0f}s"
    )
    if stats.errors:
        console.print("  Rerun to retry failed images (tracker skips completed ones)")
    console.print(f"  Tracker: [bold]{db_path}[/bold]")


# ── Commands ───────────────────────────────────────────────────────


@app.command("download")
def download(
    ctx: typer.Context,
    batch_id: str = typer.Argument(..., help="Volume/batch ID (e.g. C0074667)"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
    workers: int = typer.Option(0, "--workers", "-w", help="Concurrent downloads"),
    query_params: str = typer.Option(
        None,
        "--query-params",
        "-q",
        help="IIIF params (e.g. 'full/,1200/0/default.jpg')",
    ),
    iiif_url: str = typer.Option(
        None, "--iiif-url", envvar="IIIF_URL", help="IIIF server base URL"
    ),
    referer: str = typer.Option(
        None,
        "--referer",
        envvar="IIIF_REFERER",
        help="Referer header for servers that require one (e.g. https://sok.riksarkivet.se/)",
    ),
    max_images: int = typer.Option(
        None, "--max-images", "-n", help="Limit number of images"
    ),
    validate: bool = typer.Option(
        False, "--validate", help="Validate each image after download"
    ),
    tracker_db: str | None = typer.Option(
        None,
        "--tracker-db",
        envvar="RAHCP_TRACKER_DB",
        help="Tracker DB: file path or postgresql:// DSN",
    ),
    tracker_prefix: str | None = typer.Option(
        None,
        "--tracker-prefix",
        help="Prefix for tracker DB name (e.g. 'familysearch' → familysearch.iiif-download.db)",
    ),
) -> None:
    """Download all images from a single IIIF batch."""

    async def _run() -> None:
        from rahcp_iiif import download_batch

        dest = Path(output_dir)
        effective_url = iiif_url or ctx.obj.get(
            "iiif_url", "https://iiifintern-ai.ra.se"
        )
        effective_params = query_params or ctx.obj.get(
            "iiif_query_params", "full/max/0/default.jpg"
        )
        effective_timeout = ctx.obj.get("iiif_timeout", 60.0)
        effective_workers = workers or ctx.obj.get("iiif_workers", 4)
        effective_referer = referer or ctx.obj.get("iiif_referer")
        headers = {"Referer": effective_referer} if effective_referer else None
        validate_fn = _get_validator() if validate else None

        tracker, db_path = _resolve_iiif_tracker(ctx, tracker_db, prefix=tracker_prefix)

        done_count = len(await asyncio.to_thread(tracker.done_keys))
        console.print(f"Tracker: {db_path} — {done_count} already done")
        flags = []
        if validate:
            flags.append("validate")
        if max_images:
            flags.append(f"max={max_images}")
        flag_str = f" [{', '.join(flags)}]" if flags else ""
        console.print(
            f"Downloading batch [bold]{batch_id}[/bold] → {dest}/"
            f" ({effective_workers} workers){flag_str}"
        )
        console.print(f"  IIIF: {effective_url}  params: {effective_params}")

        stats = await download_batch(
            batch_id,
            dest,
            tracker,
            base_url=effective_url,
            query_params=effective_params,
            timeout=effective_timeout,
            headers=headers,
            workers=effective_workers,
            max_images=max_images,
            validate_file=validate_fn,
            on_progress=_print_progress,
            on_error=_print_error,
            progress_interval=ctx.obj.get("bulk_progress_interval", 5.0),
        )

        tracker.close()
        _print_summary(stats, db_path)

    run(_run())


@app.command("download-batches")
def download_batches(
    ctx: typer.Context,
    job_file: str = typer.Argument(..., help="Text file with batch IDs (one per line)"),
    output_dir: str = typer.Option(".", "--output", "-o", help="Output directory"),
    workers: int = typer.Option(0, "--workers", "-w", help="Concurrent downloads"),
    query_params: str = typer.Option(
        None,
        "--query-params",
        "-q",
        help="IIIF params (e.g. 'full/,1200/0/default.jpg')",
    ),
    iiif_url: str = typer.Option(
        None, "--iiif-url", envvar="IIIF_URL", help="IIIF server base URL"
    ),
    referer: str = typer.Option(
        None,
        "--referer",
        envvar="IIIF_REFERER",
        help="Referer header for servers that require one (e.g. https://sok.riksarkivet.se/)",
    ),
    max_images: int = typer.Option(
        None, "--max-images", "-n", help="Limit images per batch"
    ),
    validate: bool = typer.Option(
        False, "--validate", help="Validate each image after download"
    ),
    tracker_db: str | None = typer.Option(
        None,
        "--tracker-db",
        envvar="RAHCP_TRACKER_DB",
        help="Tracker DB: file path or postgresql:// DSN",
    ),
    tracker_prefix: str | None = typer.Option(
        None,
        "--tracker-prefix",
        help="Prefix for tracker DB name (e.g. 'familysearch' → familysearch.iiif-download.db)",
    ),
) -> None:
    """Download images from multiple IIIF batches listed in a text file."""

    async def _run() -> None:
        from rahcp_iiif import download_batches as _download_batches

        job_path = Path(job_file)
        if not job_path.exists():
            console.print(f"[red]File not found: {job_path}[/red]")
            raise SystemExit(1)

        batch_ids = [
            line.strip()
            for line in job_path.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        if not batch_ids:
            console.print("[red]No batch IDs found in file[/red]")
            raise SystemExit(1)

        dest = Path(output_dir)
        effective_url = iiif_url or ctx.obj.get(
            "iiif_url", "https://iiifintern-ai.ra.se"
        )
        effective_params = query_params or ctx.obj.get(
            "iiif_query_params", "full/max/0/default.jpg"
        )
        effective_timeout = ctx.obj.get("iiif_timeout", 60.0)
        effective_workers = workers or ctx.obj.get("iiif_workers", 4)
        effective_referer = referer or ctx.obj.get("iiif_referer")
        headers = {"Referer": effective_referer} if effective_referer else None
        validate_fn = _get_validator() if validate else None

        tracker, db_path = _resolve_iiif_tracker(ctx, tracker_db, prefix=tracker_prefix)

        done_count = len(await asyncio.to_thread(tracker.done_keys))
        console.print(f"Tracker: {db_path} — {done_count} already done")
        console.print(
            f"Downloading {len(batch_ids)} batches from [bold]{job_path.name}[/bold]"
            f" → {dest}/ ({effective_workers} workers)"
        )
        console.print(f"  IIIF: {effective_url}  params: {effective_params}")

        stats = await _download_batches(
            batch_ids,
            dest,
            tracker,
            base_url=effective_url,
            query_params=effective_params,
            timeout=effective_timeout,
            headers=headers,
            workers=effective_workers,
            max_images=max_images,
            validate_file=validate_fn,
            on_progress=_print_progress,
            on_error=_print_error,
            progress_interval=ctx.obj.get("bulk_progress_interval", 5.0),
        )

        tracker.close()
        _print_summary(stats, db_path)

    run(_run())


@app.command("verify")
def verify(
    ctx: typer.Context,
    job_file: str = typer.Argument(..., help="Text file with batch IDs (one per line)"),
    iiif_url: str = typer.Option(
        None, "--iiif-url", envvar="IIIF_URL", help="IIIF server base URL"
    ),
    referer: str = typer.Option(
        None,
        "--referer",
        envvar="IIIF_REFERER",
        help="Referer header for servers that require one",
    ),
    workers: int = typer.Option(
        16, "--workers", "-w", help="Concurrent manifest fetches"
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
    write_deficient: str | None = typer.Option(
        None,
        "--write-deficient",
        help="Write deficient batch IDs (one per line) to this file for re-running",
    ),
) -> None:
    """Reconcile downloaded images against live manifests; flag short/missing batches.

    Re-fetches each batch's manifest and compares its image count to the tracker.
    Exits non-zero if any batch is short or missing, so it is usable as a gate.
    """

    async def _run() -> None:
        from rahcp_iiif import verify_batches

        job_path = Path(job_file)
        if not job_path.exists():
            console.print(f"[red]File not found: {job_path}[/red]")
            raise SystemExit(1)

        batch_ids = [
            line.strip()
            for line in job_path.read_text().splitlines()
            if line.strip() and not line.startswith("#")
        ]
        if not batch_ids:
            console.print("[red]No batch IDs found in file[/red]")
            raise SystemExit(1)

        effective_url = iiif_url or ctx.obj.get(
            "iiif_url", "https://iiifintern-ai.ra.se"
        )
        effective_timeout = ctx.obj.get("iiif_timeout", 60.0)
        effective_referer = referer or ctx.obj.get("iiif_referer")
        headers = {"Referer": effective_referer} if effective_referer else None

        tracker, db_path = _resolve_iiif_tracker(ctx, tracker_db, prefix=tracker_prefix)
        done_keys = await asyncio.to_thread(tracker.done_keys)
        tracker.close()

        console.print(
            f"Verifying {len(batch_ids)} batches against [bold]{effective_url}[/bold]"
            f" (tracker: {db_path})"
        )
        report = await verify_batches(
            batch_ids,
            done_keys,
            base_url=effective_url,
            timeout=effective_timeout,
            headers=headers,
            workers=workers,
        )

        console.print(
            f"\n[bold]Verify:[/bold] {len(report.complete)} complete,"
            f" [red]{len(report.short)} short[/red],"
            f" [red]{len(report.missing)} missing[/red],"
            f" {len(report.fetch_errors)} fetch-error"
        )
        for r in sorted(report.deficient, key=lambda x: -x.missing_count):
            console.print(
                f"  [red]{r.batch_id}[/red]  expected {r.expected}, got {r.got}"
                f"  (missing {r.missing_count})"
            )
        if report.fetch_errors:
            errs = ", ".join(r.batch_id for r in report.fetch_errors)
            console.print(f"  [yellow]fetch-error (recheck):[/yellow] {errs}")

        if report.deficient:
            console.print(
                f"\n[bold red]{report.total_missing_images} images missing across"
                f" {len(report.deficient)} batches.[/bold red]"
            )
            if write_deficient:
                Path(write_deficient).write_text(
                    "\n".join(r.batch_id for r in report.deficient) + "\n"
                )
                console.print(
                    f"  Deficient batch IDs written to [bold]{write_deficient}[/bold]"
                )
            raise SystemExit(1)

        console.print("[green]All batches complete.[/green]")

    run(_run())


@app.command("upload")
def upload(
    ctx: typer.Context,
    bucket: str = typer.Argument(..., help="Target S3 bucket"),
    batch_ids: list[str] | None = typer.Argument(
        None, help="Batch IDs to stream (e.g. C0074667). Omit when using --job-file."
    ),
    prefix: str = typer.Option(
        "", "--prefix", "-p", help="Key prefix prepended to '<batch>/<image>'"
    ),
    job_file: str | None = typer.Option(
        None, "--job-file", "-f", help="Text file with batch IDs (one per line)"
    ),
    workers: int = typer.Option(
        0, "--workers", "-w", help="Concurrent download+upload workers"
    ),
    skip_existing: bool = typer.Option(
        True,
        "--skip-existing/--overwrite",
        help="Skip images already present in the bucket (HEAD check before download)",
    ),
    validate: bool = typer.Option(
        False, "--validate", help="Validate each image's bytes before upload"
    ),
    verify: bool = typer.Option(
        False, "--verify", help="Verify each upload by checking remote size after"
    ),
    query_params: str = typer.Option(
        None,
        "--query-params",
        "-q",
        help="IIIF params (e.g. 'full/,1200/0/default.jpg')",
    ),
    iiif_url: str = typer.Option(
        None, "--iiif-url", envvar="IIIF_URL", help="IIIF server base URL"
    ),
    referer: str = typer.Option(
        None,
        "--referer",
        envvar="IIIF_REFERER",
        help="Referer header for servers that require one (e.g. https://sok.riksarkivet.se/)",
    ),
    max_images: int = typer.Option(
        None, "--max-images", "-n", help="Limit images per batch"
    ),
    tracker_db: str | None = typer.Option(
        None,
        "--tracker-db",
        envvar="RAHCP_TRACKER_DB",
        help="Tracker DB: file path or postgresql:// DSN",
    ),
    tracker_prefix: str | None = typer.Option(
        None,
        "--tracker-prefix",
        help="Prefix for tracker DB name (e.g. 'familysearch' → familysearch.iiif-download.db)",
    ),
) -> None:
    """Stream IIIF images straight to S3 — download and upload in one pass (no local disk).

    Bytes are fetched on the fly and pushed through the shared bulk transfer
    engine, so this skips images already in the bucket (--skip-existing), can
    validate bytes before upload (--validate) and verify size after (--verify) —
    the same guarantees as `s3 upload-all`, without staging anything to disk.
    """

    async def _run() -> None:
        import httpx

        from rahcp_client import BulkStreamConfig, bulk_stream_upload
        from rahcp_iiif.manifest import (
            build_image_url,
            fetch_with_retry,
            file_extension,
            get_image_ids,
        )

        ids: list[str] = list(batch_ids or [])
        if job_file:
            job_path = Path(job_file)
            if not job_path.exists():
                console.print(f"[red]File not found: {job_path}[/red]")
                raise SystemExit(1)
            ids += [
                line.strip()
                for line in job_path.read_text().splitlines()
                if line.strip() and not line.startswith("#")
            ]
        if not ids:
            console.print(
                "[red]No batch IDs given — pass batch IDs as arguments or use --job-file[/red]"
            )
            raise SystemExit(1)

        effective_url = iiif_url or ctx.obj.get(
            "iiif_url", "https://iiifintern-ai.ra.se"
        )
        effective_params = query_params or ctx.obj.get(
            "iiif_query_params", "full/max/0/default.jpg"
        )
        effective_timeout = ctx.obj.get("iiif_timeout", 60.0)
        effective_workers = workers or ctx.obj.get("iiif_workers", 8)
        effective_referer = referer or ctx.obj.get("iiif_referer")
        headers = {"Referer": effective_referer} if effective_referer else None
        ext = file_extension(effective_params)
        validate_fn = _get_bytes_validator() if validate else None

        tracker, db_path = _resolve_iiif_tracker(ctx, tracker_db, prefix=tracker_prefix)
        done_count = len(await asyncio.to_thread(tracker.done_keys))
        console.print(f"Tracker: {db_path} — {done_count} already done")

        async with make_client(ctx) as client:
            # 1. Enumerate manifests -> (s3_key, image_url) items (cheap: strings).
            console.print(f"Fetching {len(ids)} manifest(s) from {effective_url} …")
            sem = asyncio.Semaphore(max(4, effective_workers))

            async def _enumerate(batch_id: str) -> list[tuple[str, str]]:
                sentinel_key = f"{prefix}{batch_id}/__manifest__"
                async with sem:
                    try:
                        image_ids = await get_image_ids(
                            batch_id,
                            base_url=effective_url,
                            timeout=effective_timeout,
                            headers=headers,
                        )
                    except Exception as exc:
                        console.print(
                            f"  [red]manifest {batch_id} failed: {str(exc)[:100]}[/red]"
                        )
                        await asyncio.to_thread(
                            tracker.mark,
                            sentinel_key,
                            0,
                            TransferStatus.error,
                            error=f"manifest: {str(exc)[:300]}",
                        )
                        return []
                await asyncio.to_thread(tracker.delete, sentinel_key)
                if max_images:
                    image_ids = image_ids[:max_images]
                return [
                    (
                        f"{prefix}{batch_id}/{image_id}{ext}",
                        build_image_url(
                            image_id,
                            base_url=effective_url,
                            query_params=effective_params,
                        ),
                    )
                    for image_id in image_ids
                ]

            per_batch = await asyncio.gather(*[_enumerate(b) for b in ids])
            items = [item for sub in per_batch for item in sub]
            if not items:
                tracker.close()
                console.print("[red]No images found in the given batches[/red]")
                raise SystemExit(1)

            flags = [
                label
                for label, on in (
                    ("skip-existing", skip_existing),
                    ("validate", validate),
                    ("verify", verify),
                )
                if on
            ]
            flag_str = f" [{', '.join(flags)}]" if flags else ""
            console.print(
                f"Streaming {len(items)} images from {len(ids)} batch(es)"
                f" → s3://{bucket}/{prefix} ({effective_workers} workers){flag_str}"
            )

            # 2. fetch = retrying IIIF download over a shared pooled client.
            async with httpx.AsyncClient(
                timeout=effective_timeout, headers=headers
            ) as iiif_http:

                async def fetch(url: str) -> bytes:
                    resp = await fetch_with_retry(iiif_http, url)
                    return resp.content

                stats = await bulk_stream_upload(
                    BulkStreamConfig(
                        client=client,
                        bucket=bucket,
                        tracker=tracker,
                        workers=effective_workers,
                        queue_depth=ctx.obj.get("bulk_queue_depth", 8),
                        skip_existing=skip_existing,
                        validate_bytes=validate_fn,
                        verify_upload=verify,
                        presign_batch_size=ctx.obj.get("bulk_presign_batch_size", 200),
                        on_progress=_print_progress,
                        on_error=_print_error,
                        progress_interval=ctx.obj.get("bulk_progress_interval", 5.0),
                    ),
                    items,
                    fetch,
                )

        tracker.close()
        _print_summary(stats, db_path, verb="Uploaded")

    run(_run())
