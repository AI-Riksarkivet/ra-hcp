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

By default images are written to `output_dir`. Pass a `sink` callback instead to
hand each downloaded image's bytes straight to another destination — e.g. upload
to HCP S3 in the same pass, without ever touching local disk. `output_dir` may be
`None` in this mode.

```python
from rahcp_client import HCPClient
from rahcp_iiif import download_batches
from rahcp_tracker import SqliteTracker

async with HCPClient.from_env() as client:
    tracker = SqliteTracker(Path(".iiif-upload.db"))

    async def sink(key: str, data: bytes) -> None:
        # key is "{batch_id}/{image_id}{ext}"
        await client.s3.upload("my-bucket", key, data)

    stats = await download_batches(
        ["C0074667", "C0074865"], None, tracker, workers=10, sink=sink
    )
    tracker.close()
```

The tracker marks a key `done` only after **both** the download and the `sink`
succeed, so a re-run resumes any image that didn't make it all the way through.
The `rahcp iiif upload` CLI command wires this up for you (see below).

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

See [CLI — rahcp iiif](cli.md#rahcp-iiif) for command-line usage: `rahcp iiif download` and `rahcp iiif download-batches` (download to disk), and `rahcp iiif upload` (stream IIIF → S3 in one pass, using the `sink` pattern above).
