---
name: hcp-sdk
description: >
  Use when building workflows with the rahcp Python SDK — downloading images
  from IIIF, uploading to HCP S3, bulk transfers, namespace management,
  transfer tracking, or writing CLI scripts. Triggers: rahcp, HCP, IIIF,
  presigned URL, bulk upload, bulk download, transfer tracker, S3 objects.
---

# rahcp SDK

Async Python SDK for HCP (Hitachi Content Platform) S3 storage and IIIF image downloads.

## Install

Everything ships in **one package**, `rahcp` — there are no separate `rahcp-*`
packages to install. Optional/heavy deps are extras:

```
pip install rahcp                 # client, CLI, IIIF, Transkribus, tracker
pip install "rahcp[validate]"     # + image validation (Pillow)
pip install "rahcp[etl]"          # + NATS JetStream ETL
pip install "rahcp[alto]"         # + Transkribus PAGE->ALTO (ocrd)
pip install "rahcp[postgres]"     # + Postgres tracker backend
pip install "rahcp[all]"          # everything
```

Import names are unchanged (the modules are bundled under their own top-level
names), so `from rahcp_client import ...` and `from rahcp_transkribus import ...`
work straight after `pip install rahcp`:

| Module | What it does |
|--------|-------------|
| `rahcp_client` | Async HCP API client (auth, S3, MAPI, presigned URLs, bulk transfers) |
| `rahcp_tracker` | Resumable transfer tracking with SQLite (pluggable via Protocol) |
| `rahcp_iiif` | IIIF manifest parsing + parallel image downloads |
| `rahcp_transkribus` | Export PAGE/ALTO XML + images from Transkribus collections |
| `rahcp.cli` | CLI: `rahcp s3`, `rahcp iiif`, `rahcp transkribus`, `rahcp ns`, `rahcp auth` |
| `rahcp_validate` | JPEG/TIFF/PNG validation (extra: `rahcp[validate]`) |
| `rahcp_etl` | NATS JetStream pipelines (extra: `rahcp[etl]`) |

## How data flows

Data never flows through the API server. The SDK uses **presigned URLs** for all transfers:

```
Your code → POST /presign → signed URL → PUT/GET directly to HCP S3
```

Files >= 100 MB automatically use multipart upload (parallel parts).

## Upload files to HCP

```python
import asyncio
from pathlib import Path
from rahcp_client import HCPClient, BulkUploadConfig, bulk_upload
from rahcp_tracker import SqliteTracker

async def main():
    tracker = SqliteTracker(Path("upload.db"))
    async with HCPClient.from_env() as client:
        # Single file
        etag = await client.s3.upload("my-bucket", "data/file.jpg", Path("file.jpg"))

        # Entire directory (resumable, parallel)
        stats = await bulk_upload(BulkUploadConfig(
            client=client,
            bucket="my-bucket",
            source_dir=Path("./scans"),
            tracker=tracker,
            workers=20,
            include=["*.jpg"],
        ))
        print(f"{stats.ok} uploaded, {stats.skipped} skipped, {stats.errors} errors")
    tracker.close()

asyncio.run(main())
```

CLI:
```bash
rahcp s3 upload my-bucket data/file.jpg ./file.jpg
rahcp s3 upload-all my-bucket ./scans --workers 20 --include '*.jpg' --validate
```

## Download from HCP

```python
# Single file
size = await client.s3.download("bucket", "key", Path("dest.jpg"))
data = await client.s3.download_bytes("bucket", "key")

# Bulk (resumable, parallel)
from rahcp_client import BulkDownloadConfig, bulk_download
stats = await bulk_download(BulkDownloadConfig(
    client=client, bucket="bucket", dest_dir=Path("./output"),
    tracker=tracker, workers=10,
))
```

CLI:
```bash
rahcp s3 download my-bucket data/file.jpg -o ./file.jpg
rahcp s3 download-all my-bucket -o ./output --workers 10
```

## Download images from IIIF

Downloads images from Riksarkivet IIIF endpoints (or any IIIF server).

```python
from rahcp_tracker import SqliteTracker
from rahcp_iiif import download_batch, download_batches

tracker = SqliteTracker(Path(".iiif-download.db"))

# Single batch (e.g. volume C0074667)
stats = await download_batch("C0074667", Path("./images"), tracker, workers=10)

# Multiple batches
stats = await download_batches(
    ["C0074667", "C0074865", "A0065852"],
    Path("./images"), tracker,
    workers=10,
    query_params="full/,1200/0/default.jpg",  # custom resolution
)
tracker.close()
```

CLI:
```bash
# Single batch
rahcp iiif download C0074667 -o ./images/ --workers 10

# Multiple batches from a job file (one batch ID per line)
rahcp iiif download-batches batches.txt -o ./images/ --workers 10 --validate

# Custom IIIF params (scale to 1200px height)
rahcp iiif download C0074667 -o ./images/ -q "full/,1200/0/default.jpg"
```

### IIIF query_params reference

| Value | Description |
|-------|-------------|
| `full/max/0/default.jpg` | Full resolution (default) |
| `full/,1200/0/default.jpg` | Scale to 1200px height |
| `full/800,/0/default.jpg` | Scale to 800px width |
| `full/200,200/0/default.jpg` | Fixed 200x200 thumbnail |

## Common workflow: IIIF download then HCP upload

```bash
# Step 1: Download from IIIF (creates iiif-batches.db tracker)
rahcp iiif download-batches batches.txt -o ./images/ --validate --workers 10

# Step 2: Upload to HCP (creates .upload-tracker.db tracker)
rahcp s3 upload-all images-batch ./images/ --validate --workers 20
```

IIIF downloads use `.rahcp/.iiif-download.db`, S3 uploads use `.rahcp/.upload-tracker.db`. Both are independently resumable.

Use `--tracker-prefix` to keep separate DBs per dataset (SQLite only):
```bash
rahcp s3 upload-all bucket ./andraarkiv --tracker-prefix andraarkiv
# → .rahcp/andraarkiv.upload-tracker.db

rahcp iiif download-batches job.txt --tracker-prefix familysearch
# → .rahcp/familysearch.iiif-download.db
```

Or set globally in config: `bulk_tracker_prefix: andraarkiv`

## Export from Transkribus

Export ground-truth PAGE/ALTO XML + page images from a Transkribus collection.
Same tracker-based resumability as IIIF; export to a local dir or stream straight
into a bucket.

```python
import asyncio
from pathlib import Path
from rahcp_tracker import SqliteTracker
from rahcp_transkribus import TranskribusClient, export_collection

async def main():
    tracker = SqliteTracker(Path(".transkribus-export.db"))
    async with TranskribusClient("me@example.se", "password") as client:
        stats = await export_collection(
            client, 1944790, Path("./export"), tracker,
            status="GT", fmt="page", include_images=True, workers=8,
        )
    print(f"{stats.ok} exported, {stats.skipped} skipped, {stats.errors} errors")
    tracker.close()

asyncio.run(main())
```

Output keys are relative (`{collection}/{docId}_{title}/{page|alto|images}/{name}`)
so they double as local paths and S3 keys. `fmt="alto"` converts PAGE→ALTO on the
fly (needs the `alto` extra: `page-to-alto`).

CLI:
```bash
# Export to disk
rahcp transkribus export 1944790 -o ./export -U me@example.se -P secret

# Stream straight to a bucket, choosing a conflict policy for existing keys
rahcp transkribus upload 1944790 my-bucket --prefix medieval/ --on-conflict skip
```

### Scheduled sync (export + upload in one pass)

`rahcp transkribus upload` is a single idempotent job for any scheduler (cron,
Argo `CronWorkflow`, k8s `CronJob`). `--archive-dir` tees a local copy while
streaming to the bucket, so **one run does both the export and the upload**:

```bash
rahcp transkribus upload 1944790 my-bucket --prefix medieval/ \
  --archive-dir /data/transkribus \   # local copy of every file (the "export")
  --validate --verify \               # byte-check + size-verify
  --on-conflict skip                  # keep what's already in the bucket
# Transkribus → s3://my-bucket/medieval/…  AND  → /data/transkribus/…
```

Guarantees for repeated runs: **idempotent** (tracker skips done files — nothing
uploaded twice; re-runs converge), **validated/verified**, **fails loud**
(`--fail-on-error`, default on, exits non-zero so the scheduler marks the run
failed; `--no-fail-on-error` forces 0). Exit codes: `0`=all done, `1`=failed
(re-run resumes), `130`=interrupted. A plain re-run picks up **new** pages/docs
and retries failures. **Persist the tracker DB** (and `--archive-dir`) across runs
(mounted volume, or a `postgresql://` DSN) so resume works run to run.

### Catching corrected transcripts — `--check-updates`

A transcript re-corrected in Transkribus gets a new `tsId` but keeps the same
object key, so a plain re-run skips it. `--check-updates` remembers each
transcript's synced `tsId` (sidecar DB `<tracker-db>.versions.db`, or
`--version-db`) and re-uploads **only** the changed ones (implies overwrite):

```bash
rahcp transkribus upload 1944790 my-bucket --prefix medieval/ --check-updates
```

**HCP overwrite gotcha (fixed in the engine):** HCP has no overwrite-in-place — a
PUT over an existing key returns `409`. `ConflictPolicy.overwrite` (and
`--check-updates`) therefore **delete then re-PUT** so overwrite genuinely
replaces the object. Note: moto and the backend `mock_server` allow PUT-overwrite
(in-memory), so they do NOT reproduce HCP's 409 — test overwrite paths against a
real HCP bucket or the delete-then-put unit tests, not the mock.

### Bucket conflict policy (overwrite / skip / error)

`bulk_upload` / `bulk_stream_upload` now take `on_conflict: ConflictPolicy` for
keys that already exist in the destination bucket:

```python
from rahcp_client import BulkStreamConfig, ConflictPolicy, bulk_stream_upload

BulkStreamConfig(..., on_conflict=ConflictPolicy.skip)       # keep remote, count skipped (default)
BulkStreamConfig(..., on_conflict=ConflictPolicy.overwrite)  # replace remote, no pre-flight HEAD
BulkStreamConfig(..., on_conflict=ConflictPolicy.error)      # record a conflict error for the item
```

`on_conflict` supersedes the legacy `skip_existing` bool; when `on_conflict` is
`None`, `skip_existing=True`→skip and `False`→overwrite (unchanged back-compat).
The `rahcp transkribus upload` / `rahcp iiif upload` CLIs surface this as
`--on-conflict overwrite|skip|error`.

## Transfer tracker

All bulk operations use a tracker for crash-safe resume. Completed files are skipped instantly on re-run.

```python
from rahcp_tracker import SqliteTracker, TransferStatus

tracker = SqliteTracker(Path("job.db"))

# Mark files manually
tracker.mark("file.jpg", 12345, TransferStatus.done, etag='"abc"', validated=True)
tracker.mark("bad.jpg", 0, TransferStatus.error, "corrupt file")

# Query state
done = tracker.done_keys()        # set[str]
errors = tracker.error_entries()  # list[(key, size)]
summary = tracker.summary()       # {"pending": 0, "done": 500, "error": 3}

tracker.close()
```

The tracker uses `TrackerProtocol` — any backend implementing 8 methods works. Default is SQLite with WAL mode.

## S3 operations

```python
async with HCPClient.from_env() as client:
    # List
    buckets = await client.s3.list_buckets()
    objects = await client.s3.list_objects("bucket", prefix="data/", max_keys=100)

    # Metadata
    meta = await client.s3.head("bucket", "key")  # returns HTTP headers dict

    # Copy / delete
    await client.s3.copy("dest-bucket", "dest-key", "src-bucket", "src-key")
    await client.s3.delete("bucket", "key")
    await client.s3.delete_bulk("bucket", ["key1", "key2"])

    # Presigned URLs (for sharing / browser uploads)
    url = await client.s3.presign_get("bucket", "key", expires=3600)
    url = await client.s3.presign_put("bucket", "key", expires=3600)
```

### Staging pattern (atomic batch writes)

```python
# Upload to staging prefix
for f in files:
    await client.s3.upload("bucket", f"staging/batch-1/{f.name}", f)

# Atomic commit: copy staging → final, delete staging
count = await client.s3.commit_staging("bucket", "staging/batch-1/", "final/batch-1/")

# On failure: clean up
await client.s3.cleanup_staging("bucket", "staging/batch-1/")
```

## Namespace management

```python
async with HCPClient.from_env() as client:
    namespaces = await client.mapi.list_namespaces("tenant", verbose=True)
    await client.mapi.create_namespace("tenant", {
        "name": "new-ns", "hardQuota": "100 GB", "softQuota": 80,
    })
    template = await client.mapi.export_namespace("tenant", "ns-name")
    await client.mapi.delete_namespace("tenant", "ns-name")
```

CLI:
```bash
rahcp ns list my-tenant
rahcp ns create my-tenant --name new-ns --quota "100 GB"
rahcp ns export my-tenant ns-name -o template.json
rahcp ns import my-tenant template.json
```

## Authentication

```python
# From environment variables (HCP_ENDPOINT, HCP_USERNAME, HCP_PASSWORD, HCP_TENANT)
client = HCPClient.from_env()

# Explicit
client = HCPClient(
    endpoint="http://localhost:8000/api/v1",
    username="admin", password="secret", tenant="dev-ai",
)

# Auto-authenticates on context manager entry
async with client:
    ...  # token refreshes automatically on 401
```

## Validation

Optional — install with `pip install "rahcp[validate]"`.

```python
from rahcp_validate.images import validate_jpg, validate_tiff, validate_by_extension

validate_jpg(Path("photo.jpg"))   # raises ValidationError if corrupt
validate_tiff(Path("scan.tiff"))  # checks magic bytes + Pillow decode

# Auto-detect by extension (used by --validate flag)
validate_by_extension(Path("photo.jpg"))
```

Pass as callback to bulk operations:
```python
stats = await bulk_upload(BulkUploadConfig(
    ..., validate_file=validate_by_extension,
))
```

## Error handling

```python
from rahcp_client.errors import HCPError, NotFoundError, AuthenticationError

try:
    await client.s3.head("bucket", "missing-key")
except NotFoundError:
    print("Not found")
except HCPError as e:
    print(f"HCP error {e.status_code}: {e.message}")
```

| Exception | HTTP status | Behavior |
|-----------|------------|----------|
| `AuthenticationError` | 401, 403 | Auto re-auth once on 401, then raise |
| `NotFoundError` | 404 | Raise immediately |
| `ConflictError` | 409 | Raise immediately |
| `RetryableError` | 408, 429, 500, 503, 504 | Exponential backoff, then raise |
| `UpstreamError` | 502 | Raise immediately (no retry) |

## Configuration

Config file at `~/.rahcp/config.yaml` (default) or `--config path` for project-local configs.

**If config is NOT at the default path, you MUST pass `--config`:**

```bash
# Default path — works without --config
rahcp s3 ls                              # reads ~/.rahcp/config.yaml

# Project-local config — MUST pass --config or commands fail with 401
rahcp --config .rahcp/config.yaml s3 ls  # reads .rahcp/config.yaml
```

This is the most common cause of `AuthenticationError` — the CLI can't find credentials because it's looking at the default path where no config exists.

```yaml
default: dev
profiles:
  dev:
    endpoint: http://localhost:8000/api/v1
    username: admin
    password: secret
    tenant: dev-ai
    verify_ssl: false

    # Bulk transfer tuning
    bulk_workers: 60                # concurrent transfers (0 in CLI = use config)
    bulk_presign_batch_size: 500    # URLs presigned per API call
    bulk_chunk_size: 4194304        # 4 MB — streaming chunk size for large files
    bulk_stream_threshold: 104857600 # 100 MB — files below this read in one shot
    bulk_queue_depth: 16            # queue = workers × depth
    bulk_tracker_flush_every: 500   # SQLite write frequency
    bulk_tracker_prefix: ""         # prefix tracker DB names per dataset

    # IIIF settings
    iiif_url: https://iiifintern-ai.ra.se
    iiif_query_params: full/max/0/default.jpg
    iiif_workers: 4
    iiif_referer: https://sok.riksarkivet.se/  # Referer header (some servers 403 without it)
```

Priority: CLI flags > env vars (`HCP_*`, `IIIF_*`) > config file > defaults.

## Debugging & troubleshooting

See [troubleshooting.md](troubleshooting.md) for:
- Debug log levels (`--log-level debug`)
- Common errors: auth failures, missing objects, validation errors, timeouts
- Tracker inspection (querying the SQLite DB)
- Performance tuning by scenario
- Post-transfer verification
- Running long transfers safely (tmux)
