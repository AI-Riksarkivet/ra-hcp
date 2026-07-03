# rahcp

Async Python **SDK & CLI** for the Hitachi Content Platform (HCP) Unified API — S3-compatible object storage, IIIF image ingestion, and Transkribus exports, with resumable, parallel bulk transfers.

Everything ships in one package. Data never flows through an API server: the SDK uses **presigned URLs** for direct, parallel, crash-resumable transfers.

## Install

```bash
pip install rahcp                 # client, CLI, IIIF, Transkribus, tracker
pip install "rahcp[validate]"     # + pre-upload image validation (Pillow)
pip install "rahcp[etl]"          # + NATS JetStream pipelines
pip install "rahcp[alto]"         # + Transkribus PAGE->ALTO conversion (ocrd)
pip install "rahcp[postgres]"     # + Postgres transfer-tracker backend
pip install "rahcp[all]"          # everything
```

## Quick start

### Python

```python
import asyncio
from pathlib import Path
from rahcp import HCPClient

async def main():
    # reads HCP_ENDPOINT / HCP_USERNAME / HCP_PASSWORD / HCP_TENANT
    async with HCPClient.from_env() as client:
        await client.s3.upload("my-bucket", "data/file.jpg", Path("file.jpg"))
        objects = await client.s3.list_objects("my-bucket", prefix="data/")
        print(objects)

asyncio.run(main())
```

### CLI

```bash
rahcp s3 upload-all my-bucket ./scans --workers 20 --include '*.jpg'
rahcp iiif download-batches batches.txt -o ./images/ --workers 10
rahcp transkribus upload 1944790 my-bucket --prefix medieval/ --archive-dir /data
rahcp ns list my-tenant
```

## What's inside `rahcp`

| Module | Purpose |
|--------|---------|
| `rahcp_client` | Async HCP client — auth, S3, MAPI, presigned URLs, bulk up/download |
| `rahcp_tracker` | Resumable transfer state tracking (SQLite; Postgres via `[postgres]`) |
| `rahcp_iiif` | Parallel IIIF image downloader with resumable tracking |
| `rahcp_transkribus` | Transkribus collection exporter (PAGE/ALTO XML + images) |
| `rahcp_validate` | Pre-upload image validation (`[validate]`) |
| `rahcp.cli` | The `rahcp` command-line interface |

Import names are stable: `from rahcp_client import HCPClient`, `from rahcp_iiif import download_batch`, `from rahcp_transkribus import export_collection`.

## Links

- **Documentation:** https://ai-riksarkivet.github.io/hcp/
- **Source:** https://github.com/AI-Riksarkivet/ra-hcp

Licensed under Apache-2.0.
