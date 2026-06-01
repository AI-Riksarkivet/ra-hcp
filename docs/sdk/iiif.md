# rahcp-iiif

Async IIIF image downloader with resumable tracking. Downloads images from Riksarkivet IIIF endpoints in parallel, with optional validation via `rahcp-validate`.

```bash
uv pip install rahcp-iiif
# With validation:
uv pip install "rahcp-iiif[validate]"
```

## Quick start

```python
import asyncio
from pathlib import Path
from rahcp_tracker import SqliteTracker
from rahcp_iiif import download_batch, download_batches

async def main():
    tracker = SqliteTracker(Path(".iiif-download.db"))

    # Download a single batch
    stats = await download_batch(
        "C0074667",
        Path("./images"),
        tracker,
        workers=10,
    )
    print(f"Downloaded {stats.ok}, skipped {stats.skipped}, errors {stats.errors}")

    # Or download multiple batches
    stats = await download_batches(
        ["C0074667", "C0074865", "A0065852"],
        Path("./images"),
        tracker,
        workers=10,
        query_params="full/,1200/0/default.jpg",  # custom resolution
    )
    tracker.close()

asyncio.run(main())
```

## Stream directly to S3 (no local disk)

To upload IIIF images to HCP S3 **without staging them to disk**, use
`rahcp_client.bulk.bulk_stream_upload` (or the `rahcp iiif upload` CLI command).
It reuses the bulk transfer engine, so you get the **same guarantees as
`s3 upload-all`** — skip-existing, validation, verify, batched presign, resumable
tracking — while fetching each image's bytes on demand instead of writing to disk.
Only the in-flight images (≈ `workers` × image size) are ever in memory.

```python
from pathlib import Path

import httpx
from rahcp_client import BulkStreamConfig, HCPClient, bulk_stream_upload
from rahcp_iiif.manifest import build_image_url, fetch_with_retry, file_extension, get_image_ids
from rahcp_tracker import SqliteTracker
from rahcp_validate import validate_bytes_by_extension

async def stream_to_s3(batch_ids, bucket, *, base_url="https://lbiiif.riksarkivet.se"):
    tracker = SqliteTracker(Path(".iiif-upload.db"))
    ext = file_extension("full/max/0/default.jpg")

    async with HCPClient.from_env() as client, httpx.AsyncClient(timeout=60) as iiif:
        # Build (s3_key, image_url) items from each batch's manifest.
        items: list[tuple[str, str]] = []
        for batch_id in batch_ids:
            for image_id in await get_image_ids(batch_id, base_url=base_url):
                items.append(
                    (f"{batch_id}/{image_id}{ext}", build_image_url(image_id, base_url=base_url))
                )

        async def fetch(url: str) -> bytes:
            return (await fetch_with_retry(iiif, url)).content

        stats = await bulk_stream_upload(
            BulkStreamConfig(
                client=client,
                bucket=bucket,
                tracker=tracker,
                workers=20,
                skip_existing=True,                      # HEAD-skip before download
                validate_bytes=validate_bytes_by_extension,  # reject corrupt bytes
                verify_upload=True,                      # HEAD-verify size after PUT
            ),
            items,
            fetch,
        )
    tracker.close()
    return stats
```

`bulk_stream_upload(cfg, items, fetch)` takes `(s3_key, fetch_id)` pairs and an
async `fetch(fetch_id) -> bytes`. Per image it: **skip** if already in the bucket
(`skip_existing` — a HEAD check *before* downloading) → **fetch** the bytes →
**validate** them (`validate_bytes`) → **upload** via a presigned PUT →
**verify** the size (`verify_upload`) → record in the tracker. Anything not `done`
is retried on the next run. The `rahcp iiif upload` CLI command wires all of this
up for you (see below).

!!! note "Two ways to get IIIF images into S3"
    **Stream** (above / `rahcp iiif upload`) — no disk, ideal when the data is too
    large to stage locally. **Two-step** — `rahcp iiif download-batches` to disk,
    then `rahcp s3 upload-all`; useful when you also want the local copy. Both
    paths share the same engine and the same skip/validate/verify guarantees.

## Resilience

Every network fetch (the manifest and each image) is retried with exponential
backoff + jitter on transient failures — connection/timeout errors and
`408`/`425`/`429`/`5xx` responses. Terminal responses like `404` are **not**
retried. Combined with the tracker (crash-safe resume), a large job survives both
transient network blips and process restarts.

```python
stats = await download_batch(
    "C0074667", Path("./images"), tracker,
    max_attempts=4,        # attempts per fetch (1 disables retrying)
    retry_base_delay=0.5,  # base backoff seconds; also bounds the jitter
)
```

!!! tip "Terminal vs transient"
    A `404` (missing image) fails immediately and is recorded as an `error` —
    retrying it would only waste time. A `503` or a dropped connection is retried
    up to `max_attempts` before being recorded as an error.

## Manifest parsing

```python
from rahcp_iiif import get_image_ids, build_image_url

# Get all image IDs from a IIIF manifest
image_ids = await get_image_ids("C0074667")
# → ["C0074667_00001", "C0074667_00002", ...]

# Build the download URL for a specific image
url = build_image_url("C0074667_00001", query_params="full/,1200/0/default.jpg")
# → "https://iiifintern-ai.ra.se/arkis!C0074667_00001/full/,1200/0/default.jpg"
```

## Configuration

| Setting | Env var | Default | Description |
|---------|---------|---------|-------------|
| `base_url` | `IIIF_URL` | `https://iiifintern-ai.ra.se` | IIIF server base URL |
| `timeout` | `IIIF_TIMEOUT` | `60` | Request timeout in seconds |
| `query_params` | `IIIF_QUERY_PARAMS` | `full/max/0/default.jpg` | IIIF image API parameters |

The `query_params` string follows the [IIIF Image API](https://iiif.io/api/image/3.0/) format: `{region}/{size}/{rotation}/{quality}.{format}`. Common values:

| `query_params` | Description |
|----------------|-------------|
| `full/max/0/default.jpg` | Full resolution JPEG (default) |
| `full/,1200/0/default.jpg` | Scale to 1200px height |
| `full/800,/0/default.jpg` | Scale to 800px width |
| `full/200,200/0/default.jpg` | Fixed 200x200 thumbnail |

## CLI commands

See [CLI — rahcp iiif](cli.md#rahcp-iiif) for command-line usage: `rahcp iiif download` and `rahcp iiif download-batches` (download to disk), and `rahcp iiif upload` (stream IIIF → S3 in one pass via `bulk_stream_upload`, with `--skip-existing`, `--validate`, `--verify`).
