# rahcp-transkribus

Async Transkribus collection exporter. Downloads ground-truth PAGE/ALTO XML transcripts and page images from a [Transkribus](https://transkribus.eu/) collection in parallel, with resumable tracking. Export to a local directory, or stream straight into an HCP bucket.

```bash
uv pip install rahcp
# With image validation and/or PAGE->ALTO conversion:
uv pip install "rahcp[validate,alto]"
# With PAGE→ALTO conversion (pulls in ocrd-page-to-alto):
uv pip install "rahcp-transkribus[alto]"
```

## Quick start

```python
import asyncio
from pathlib import Path
from rahcp_tracker import SqliteTracker
from rahcp_transkribus import TranskribusClient, export_collection

async def main():
    tracker = SqliteTracker(Path(".transkribus-export.db"))

    async with TranskribusClient("me@example.se", "password") as client:
        stats = await export_collection(
            client,
            collection_id=1944790,
            output_dir=Path("./export"),
            tracker=tracker,
            status="GT",        # only ground-truth transcripts
            include_images=True,
            workers=8,
        )
    print(f"Exported {stats.ok}, skipped {stats.skipped}, errors {stats.errors}")
    tracker.close()

asyncio.run(main())
```

Output layout (keys are relative, so they double as local paths and S3 keys):

```
export/
  1944790/                       # collection
    1454602_1300/                # {docId}_{sanitized title}
      page/
        11581.xml                # PAGE-XML transcript
      images/
        11581.jpg                # page image
```

Use `fmt="alto"` to convert transcripts to ALTO on the fly (requires the `alto` extra); the transcript subdirectory becomes `alto/` and files are named `*.alto.xml`.

## Stream directly to an HCP bucket (no local disk)

To push a collection into HCP S3 **without staging it to disk**, plan the export
and feed the items to `rahcp_client.bulk.bulk_stream_upload` (this is exactly what
the `rahcp transkribus upload` CLI command does). Each item's bytes are fetched on
demand and pushed through the shared bulk engine, so you get the **same guarantees
as `s3 upload-all`** — batched presign, verify, resumable tracking — plus a
**conflict policy** for keys that already exist in the bucket.

```python
from pathlib import Path
from rahcp_client import BulkStreamConfig, ConflictPolicy, HCPClient, bulk_stream_upload
from rahcp_tracker import SqliteTracker
from rahcp_transkribus import TranskribusClient, fetch_item_bytes, plan_collection_export

async def stream_to_s3(collection_id, bucket, *, prefix=""):
    tracker = SqliteTracker(Path(".transkribus-upload.db"))
    async with (
        TranskribusClient("me@example.se", "password") as tk,
        HCPClient.from_env() as hcp,
    ):
        items = await plan_collection_export(tk, collection_id, status="GT")
        items_by_id = {item.key: item for item in items}
        stream_items = [(f"{prefix}{item.key}", item.key) for item in items]

        async def fetch(fetch_id: str) -> bytes:
            return await fetch_item_bytes(tk, items_by_id[fetch_id])

        stats = await bulk_stream_upload(
            BulkStreamConfig(
                client=hcp,
                bucket=bucket,
                tracker=tracker,
                workers=8,
                on_conflict=ConflictPolicy.skip,   # skip | overwrite | error
            ),
            stream_items,
            fetch,
        )
    tracker.close()
    return stats
```

### Conflict policy

When a destination key already exists in the bucket, `on_conflict` decides what happens:

| Policy | Behaviour |
|--------|-----------|
| `ConflictPolicy.skip` | Keep the remote object, count the item as **skipped**. A local/remote size mismatch is logged as a warning but still skipped. *(default; equivalent to the legacy `skip_existing=True`)* |
| `ConflictPolicy.overwrite` | Replace the remote object. HCP rejects a PUT over an existing key (`409`, no overwrite-in-place), so the engine **deletes then re-PUTs** to make overwrite genuinely work; on stores that allow overwrite the delete never fires. *(equivalent to `skip_existing=False`)* |
| `ConflictPolicy.error` | Keep the remote object and record a **conflict error** for the item (visible in the tracker's `error_details()` and the `on_error` callback). |

`on_conflict` supersedes the older `skip_existing` bool on `BulkUploadConfig`/`BulkStreamConfig`; when `on_conflict` is left `None`, `skip_existing` still applies (`True`→skip, `False`→overwrite), so existing code is unaffected.

## Scheduled sync (safe to re-run — cron / Argo / k8s CronJob)

`rahcp transkribus upload` is a single idempotent command you can point any
scheduler at (a Unix cron, an Argo `CronWorkflow`, a Kubernetes `CronJob`, …) and
run on whatever cadence you like — nightly, weekly, whatever. With `--archive-dir`
it also keeps a local copy of every file while streaming to the bucket, so **one
invocation does both the export and the bucket upload**:

```bash
rahcp transkribus upload 1944790 my-bucket \
  --prefix medieval/ \
  --archive-dir /data/transkribus \   # local copy of every file (the "export")
  --validate \                        # byte-check images before upload
  --verify \                          # HEAD-verify size after each PUT
  --on-conflict skip \                # keep what's already in the bucket
  --workers 8
# Transkribus ──▶ s3://my-bucket/medieval/…   (streamed)
#            └──▶ /data/transkribus/…          (local archive, same pass)
```

What makes it safe to run repeatedly:

- **Idempotent** — the transfer tracker records every completed key, so a re-run does only the new and previously-failed work. Point the scheduler at it and re-runs converge; nothing is uploaded twice.
- **Fails loud** — `--fail-on-error` (the default) exits **non-zero** if any item failed, so the scheduler marks the run failed (Argo step goes red, cron mailer fires) and the next run resumes it. `--no-fail-on-error` forces exit 0. Exit codes: `0` = everything uploaded (and verified), `1` = something failed, `130` = interrupted.
- **Validated & verified** — `--validate` rejects corrupt image bytes before upload; `--verify` confirms the remote size after each PUT.

By default a re-run keys on the **object path**: **new** pages/documents are
fetched and uploaded, keys already recorded `done` are skipped. A transcript
*edited in place* in Transkribus keeps the same page filename → same key, so a
plain re-run would treat it as already-done. **`--check-updates` fixes that** (see
below).

### Catching corrected transcripts (`--check-updates`)

Transkribus versions transcripts: re-correcting a page's ground truth creates a
new transcript version with a new `tsId`, but the object key is unchanged.
`--check-updates` remembers the `tsId` last synced for each key (in a small
sidecar DB next to the tracker) and, on the next run, re-fetches and re-uploads
**only** the transcripts whose `tsId` changed — leaving unchanged transcripts and
all images untouched.

```bash
rahcp transkribus upload 1944790 my-bucket --prefix medieval/ \
  --check-updates                 # re-sync corrected transcripts too
  # optional: --version-db /data/versions.db   (default: <tracker-db>.versions.db)
```

`--check-updates` implies `--on-conflict overwrite` for the changed transcripts
(the old object must be replaced). Version state only advances when the re-upload
succeeds, so a failed run is retried next time. New transcripts (never synced) are
handled by the normal skip-if-done logic — `--check-updates` only adds detection
of *changes* to already-synced transcripts. For a **shared/parallel** run against
a `postgresql://` tracker, pass an explicit `--version-db` (the sidecar is local
SQLite).

Persist the tracker DB (and the `--archive-dir`, if used) across scheduled runs —
e.g. a mounted volume in Argo/k8s — so resume works run to run. Point
`--tracker-db` at a stable path (or a `postgresql://` DSN for shared/parallel
runs) rather than an ephemeral pod filesystem.

## Resilience

Every REST call and file fetch is retried with exponential backoff + jitter on
transient failures — connection/timeout errors and `408`/`425`/`429`/`5xx`
responses. Terminal responses like `404` are **not** retried. Combined with the
tracker (crash-safe resume), a large export survives both transient network blips
and process restarts — a re-run skips everything already recorded `done`.

```python
async with TranskribusClient(
    "me@example.se", "password",
    max_attempts=4,        # attempts per request (1 disables retrying)
    retry_base_delay=0.5,  # base backoff seconds; also bounds the jitter
) as client:
    ...
```

## Client API

```python
async with TranskribusClient(user, password) as client:
    docs = await client.list_docs(collection_id)          # list[Document]
    pages = await client.get_pages(
        collection_id, doc_id, status="GT", skip_pages_with_missing_status=True,
    )                                                      # list[Page]
    xml = await client.get_transcript_text(collection_id, doc_id, page_nr)  # bytes
    data = await client.fetch_bytes(url)                   # raw bytes (image / transcript URL)
```

The client logs in on context-manager entry (obtaining a `JSESSIONID` cookie) and out on exit. `plan_collection_export(client, collection_id, ...)` resolves a whole collection into a flat list of `ExportItem` (each carries a relative `key` and the source `url`), which both `export_collection` and the streaming path consume.

## Configuration

| Setting | Env var | Default | Description |
|---------|---------|---------|-------------|
| `base_url` | `TRANSKRIBUS_URL` | `https://transkribus.eu/TrpServer/rest` | TRP REST base URL |
| `timeout` | `TRANSKRIBUS_TIMEOUT` | `60` | Request timeout in seconds |
| `verify_ssl` | `SKIP_SSL_VERIFY` | verification on | Set `SKIP_SSL_VERIFY=true` behind a TLS-intercepting proxy |

The env vars set the *defaults* for `TranskribusClient`; explicit keyword arguments always win. For the CLI, credentials and the base URL come from `--username`/`--password`/`--transkribus-url` flags, the `TRANSKRIBUS_USERNAME`/`TRANSKRIBUS_PASSWORD`/`TRANSKRIBUS_URL` env vars, or the profile's `transkribus_*` keys (in that precedence order).

## CLI commands

See [CLI — rahcp transkribus](cli.md#rahcp-transkribus) for command-line usage: `rahcp transkribus export` (export a collection to disk) and `rahcp transkribus upload` (stream a collection straight into an HCP bucket, with `--on-conflict overwrite|skip|error`).
