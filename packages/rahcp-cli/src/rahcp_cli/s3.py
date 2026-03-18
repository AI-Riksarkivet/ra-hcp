"""S3 subcommands."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import typer

from rahcp_cli._client import make_client
from rahcp_cli._output import console, print_json, print_table
from rahcp_cli._run import run

app = typer.Typer(help="S3 data-plane operations", no_args_is_help=True)


def _human_size(size: int | str) -> str:
    """Convert bytes to human-readable string."""
    try:
        n = int(size)
    except (ValueError, TypeError):
        return str(size)
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:,.0f} {unit}" if unit == "B" else f"{n:,.1f} {unit}"
        n /= 1024
    return f"{n:,.1f} PB"


def _short_date(dt: str) -> str:
    """Shorten ISO date to readable format."""
    if not dt:
        return ""
    return dt[:19].replace("T", " ")


@app.command("ls")
def ls(
    ctx: typer.Context,
    bucket: str = typer.Argument(None),
    prefix: str = typer.Option("", "--prefix", "-p", help="Filter by key prefix"),
    max_keys: int = typer.Option(100, "--max-keys", "-n", help="Max results per page"),
    page: str = typer.Option(None, "--page", help="Continuation token for next page"),
    delimiter: str = typer.Option(
        None, "--delimiter", "-d", help="Group by delimiter (e.g. /)"
    ),
    filter_key: str = typer.Option(
        None, "--filter", "-f", help="Filter keys containing this string"
    ),
) -> None:
    """List buckets (no args) or objects in a bucket."""

    async def _run() -> None:
        async with make_client(ctx) as client:
            if bucket is None:
                data = await client.s3.list_buckets()
                if ctx.obj["json"]:
                    print_json(data)
                else:
                    buckets = data.get("buckets") or data.get("Buckets") or []
                    print_table(buckets, title="Buckets")
            else:
                data = await client.s3.list_objects(
                    bucket,
                    prefix,
                    max_keys=max_keys,
                    continuation_token=page,
                    delimiter=delimiter,
                )
                if ctx.obj["json"]:
                    print_json(data)
                else:
                    objects = data.get("objects", [])
                    if filter_key:
                        objects = [o for o in objects if filter_key in o.get("Key", "")]
                    rows = [
                        {
                            "Key": obj.get("Key", ""),
                            "Size": _human_size(obj.get("Size", 0)),
                            "LastModified": _short_date(obj.get("LastModified", "")),
                        }
                        for obj in objects
                    ]
                    prefixes = data.get("common_prefixes", [])
                    for p in prefixes:
                        rows.insert(
                            0, {"Key": f"{p}", "Size": "-", "LastModified": "-"}
                        )
                    title = f"s3://{bucket}/{prefix}" if prefix else f"s3://{bucket}"
                    print_table(
                        rows,
                        columns=["Key", "Size", "LastModified"],
                        title=title,
                    )
                    next_token = data.get("next_continuation_token")
                    if next_token:
                        console.print(
                            f"\n[dim]More results available. Next page:[/dim]\n"
                            f"  rahcp s3 ls {bucket} --page {next_token}"
                        )

    run(_run())


@app.command()
def upload(
    ctx: typer.Context,
    bucket: str = typer.Argument(...),
    key: str = typer.Argument(...),
    file: Path = typer.Argument(..., exists=True),
) -> None:
    """Upload a local file (auto multipart if large)."""

    async def _run() -> None:
        async with make_client(ctx) as client:
            etag = await client.s3.upload(bucket, key, file)
            console.print(f"[green]Uploaded[/green] s3://{bucket}/{key} (etag: {etag})")

    run(_run())


@app.command()
def download(
    ctx: typer.Context,
    bucket: str = typer.Argument(...),
    key: str = typer.Argument(...),
    output: Path = typer.Option(None, "--output", "-o"),
) -> None:
    """Download an object via presigned URL."""
    dest = output or Path(key.split("/")[-1])

    async def _run() -> None:
        async with make_client(ctx) as client:
            size = await client.s3.download(bucket, key, dest)
            console.print(f"[green]Downloaded[/green] {dest} ({size:,} bytes)")

    run(_run())


@app.command()
def rm(
    ctx: typer.Context,
    bucket: str = typer.Argument(...),
    keys: list[str] = typer.Argument(...),
) -> None:
    """Delete one or more objects."""

    async def _run() -> None:
        async with make_client(ctx) as client:
            if len(keys) == 1:
                await client.s3.delete(bucket, keys[0])
            else:
                await client.s3.delete_bulk(bucket, keys)
            console.print(f"[green]Deleted[/green] {len(keys)} object(s)")

    run(_run())


@app.command("download-all")
def download_all(
    ctx: typer.Context,
    bucket: str = typer.Argument(...),
    prefix: str = typer.Option(
        "", "--prefix", "-p", help="Only download keys under this prefix"
    ),
    dest_dir: str = typer.Option(
        ".", "--output", "-o", help="Local destination directory"
    ),
    workers: int = typer.Option(10, "--workers", "-w", help="Concurrent downloads"),
) -> None:
    """Download all objects from a bucket to a local directory."""

    async def _run() -> None:
        dest = Path(dest_dir)
        dest.mkdir(parents=True, exist_ok=True)
        sem = asyncio.Semaphore(workers)

        async def _download_one(client: Any, key: str, size: int) -> str:
            """Returns 'ok', 'skipped', or 'error'."""
            file_path = dest / key
            file_path.parent.mkdir(parents=True, exist_ok=True)
            if file_path.exists() and file_path.stat().st_size == size:
                return "skipped"
            async with sem:
                try:
                    bytes_dl = await client.s3.download(bucket, key, file_path)
                    console.print(f"  [green]{key}[/green] ({_human_size(bytes_dl)})")
                    return "ok"
                except Exception as exc:
                    console.print(f"  [red]{key}[/red] — {exc}")
                    return "error"

        async with make_client(ctx) as client:
            total = 0
            skipped = 0
            errors = 0
            token = None
            while True:
                data = await client.s3.list_objects(
                    bucket, prefix, max_keys=1000, continuation_token=token
                )
                objects = data.get("objects", [])
                tasks = [
                    _download_one(client, obj["Key"], obj.get("Size", 0))
                    for obj in objects
                    if not (obj["Key"].endswith("/") and obj.get("Size", 0) == 0)
                ]
                if tasks:
                    results = await asyncio.gather(*tasks)
                    for r in results:
                        if r == "ok":
                            total += 1
                        elif r == "skipped":
                            skipped += 1
                        else:
                            errors += 1
                if not data.get("is_truncated"):
                    break
                token = data.get("next_continuation_token")

            parts = [f"Downloaded {total} files"]
            if skipped:
                parts.append(f"skipped {skipped} existing")
            if errors:
                parts.append(f"[red]{errors} errors[/red]")
            console.print(f"\n[bold]Done.[/bold] {', '.join(parts)} → {dest}/")

    run(_run())


@app.command("upload-all")
def upload_all(
    ctx: typer.Context,
    bucket: str = typer.Argument(...),
    source_dir: str = typer.Argument(..., help="Local directory to upload"),
    prefix: str = typer.Option("", "--prefix", "-p", help="Key prefix to prepend"),
    workers: int = typer.Option(10, "--workers", "-w", help="Concurrent uploads"),
) -> None:
    """Upload all files from a local directory to a bucket."""

    async def _run() -> None:
        src = Path(source_dir)
        if not src.is_dir():
            console.print(f"[red]Not a directory: {src}[/red]")
            raise SystemExit(1)
        sem = asyncio.Semaphore(workers)

        files = [f for f in src.rglob("*") if f.is_file()]
        if not files:
            console.print("[dim]No files found.[/dim]")
            return

        console.print(
            f"Uploading {len(files)} files from {src}/ → s3://{bucket}/{prefix}"
        )

        async def _upload_one(client: Any, file_path: Path) -> str:
            rel = file_path.relative_to(src)
            key = f"{prefix}{rel}" if prefix else str(rel)
            async with sem:
                try:
                    await client.s3.upload(bucket, key, file_path)
                    console.print(
                        f"  [green]{key}[/green] ({_human_size(file_path.stat().st_size)})"
                    )
                    return "ok"
                except Exception as exc:
                    console.print(f"  [red]{key}[/red] — {exc}")
                    return "error"

        async with make_client(ctx) as client:
            results = await asyncio.gather(*[_upload_one(client, f) for f in files])
            ok = results.count("ok")
            errs = results.count("error")
            parts = [f"Uploaded {ok} files"]
            if errs:
                parts.append(f"[red]{errs} errors[/red]")
            console.print(f"\n[bold]Done.[/bold] {', '.join(parts)}")

    run(_run())


@app.command()
def presign(
    ctx: typer.Context,
    bucket: str = typer.Argument(...),
    key: str = typer.Argument(...),
    expires: int = typer.Option(3600, "--expires"),
) -> None:
    """Get a presigned download URL."""

    async def _run() -> None:
        async with make_client(ctx) as client:
            url = await client.s3.presign_get(bucket, key, expires=expires)
            if ctx.obj["json"]:
                print_json({"url": url})
            else:
                console.print(url)

    run(_run())
