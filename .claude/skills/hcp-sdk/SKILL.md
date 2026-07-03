---
name: hcp-sdk
description: >
  Build workflows with the rahcp Python SDK & CLI: upload/download HCP S3 objects,
  bulk transfers, IIIF image downloads, Transkribus exports, transfer tracking,
  namespace admin. Triggers: rahcp, HCP, IIIF, Transkribus, presigned URL, bulk
  upload, bulk download, transfer tracker, S3 objects.
---

# rahcp SDK

Async Python SDK & CLI for the Hitachi Content Platform (HCP) Unified API — S3
object storage, IIIF image downloads, and Transkribus exports, with resumable
parallel bulk transfers.

## Install — one package

`rahcp` bundles everything; there are no separate `rahcp-*` packages. Heavy deps
are extras.

```bash
pip install rahcp                 # client, CLI, IIIF, Transkribus, tracker
pip install "rahcp[validate]"     # image validation (Pillow)
pip install "rahcp[etl]"          # NATS JetStream (rahcp_etl)
pip install "rahcp[alto]"         # Transkribus PAGE->ALTO (ocrd)
pip install "rahcp[postgres]"     # Postgres tracker backend
pip install "rahcp[all]"          # everything
```

Import names are stable: `from rahcp_client import HCPClient`,
`from rahcp_iiif import download_batch`, `from rahcp_transkribus import export_collection`.

## Mental model — read before writing code

- **Presigned URLs, not proxying.** Every transfer is `POST /presign` → signed URL
  → direct PUT/GET to HCP S3; data never flows through the API server. Files
  ≥ 100 MB use multipart automatically.
- **Everything is resumable.** All bulk ops take a `tracker`; completed keys are
  skipped instantly on re-run. Persist the tracker DB across runs.
- **HCP has no overwrite-in-place.** A PUT over an existing key returns `409`;
  `ConflictPolicy.overwrite` and `--check-updates` delete-then-PUT. moto and the
  mock server allow PUT-overwrite, so they do NOT reproduce the 409 — test
  overwrite against real HCP.

## Quickstart

```python
import asyncio
from pathlib import Path
from rahcp import HCPClient  # reads HCP_ENDPOINT / HCP_USERNAME / HCP_PASSWORD / HCP_TENANT

async def main():
    async with HCPClient.from_env() as client:
        await client.s3.upload("my-bucket", "data/file.jpg", Path("file.jpg"))
        print(await client.s3.list_objects("my-bucket", prefix="data/"))

asyncio.run(main())
```

```bash
rahcp s3 upload-all my-bucket ./scans --workers 20 --include '*.jpg' --validate
```

## CLI config gotcha — the top cause of AuthenticationError

Config lives at `~/.rahcp/config.yaml`. For a project-local config you MUST pass
`--config` or every command 401s (it silently reads the default path):

```bash
rahcp --config .rahcp/config.yaml s3 ls
```

## Task references

| Task | Reference |
|------|-----------|
| S3 upload/download, list/copy/delete, presign, staging, conflict policy | [references/s3.md](references/s3.md) |
| IIIF image downloads + `query_params` + IIIF→HCP | [references/iiif.md](references/iiif.md) |
| Transkribus export/upload, scheduled sync, `--check-updates` | [references/transkribus.md](references/transkribus.md) |
| Tracker API, namespaces, auth, validation, errors, full config | [references/reference.md](references/reference.md) |
| Debug logs, perf tuning, long transfers, tracker inspection | [references/troubleshooting.md](references/troubleshooting.md) |
