# API & config reference

## Transfer tracker (`rahcp_tracker`)

All bulk operations use a tracker for crash-safe resume; completed files are skipped
instantly on re-run. `TrackerProtocol` — any backend implementing 8 methods works;
default is SQLite (WAL mode). Postgres backend via the `postgres` extra.

```python
from rahcp_tracker import SqliteTracker, TransferStatus

tracker = SqliteTracker(Path("job.db"))
tracker.mark("file.jpg", 12345, TransferStatus.done, etag='"abc"', validated=True)
tracker.mark("bad.jpg", 0, TransferStatus.error, "corrupt file")

done = tracker.done_keys()        # set[str]
errors = tracker.error_entries()  # list[(key, size)]
summary = tracker.summary()       # {"pending": 0, "done": 500, "error": 3}
tracker.close()
```

## Namespace management (`client.mapi`)

```python
async with HCPClient.from_env() as client:
    namespaces = await client.mapi.list_namespaces("tenant", verbose=True)
    await client.mapi.create_namespace("tenant", {"name": "new-ns", "hardQuota": "100 GB", "softQuota": 80})
    template = await client.mapi.export_namespace("tenant", "ns-name")
    await client.mapi.delete_namespace("tenant", "ns-name")
```

```bash
rahcp ns list my-tenant
rahcp ns create my-tenant --name new-ns --quota "100 GB"
rahcp ns export my-tenant ns-name -o template.json
rahcp ns import my-tenant template.json
```

## Authentication

```python
client = HCPClient.from_env()  # HCP_ENDPOINT, HCP_USERNAME, HCP_PASSWORD, HCP_TENANT
client = HCPClient(endpoint="http://localhost:8000/api/v1", username="admin", password="secret", tenant="dev-ai")

async with client:  # auto-authenticates on entry; token refreshes automatically on 401
    ...
```

## Validation (`rahcp_validate`, extra `[validate]`)

```python
from rahcp_validate.images import validate_jpg, validate_tiff, validate_by_extension

validate_jpg(Path("photo.jpg"))          # raises ValidationError if corrupt
validate_tiff(Path("scan.tiff"))         # magic bytes + Pillow decode
validate_by_extension(Path("photo.jpg")) # auto-detect (backs the --validate flag)

# As a bulk callback:
stats = await bulk_upload(BulkUploadConfig(..., validate_file=validate_by_extension))
```

## Error handling (`rahcp_client.errors`)

```python
from rahcp_client.errors import HCPError, NotFoundError, AuthenticationError

try:
    await client.s3.head("bucket", "missing-key")
except NotFoundError:
    ...
except HCPError as e:
    print(f"HCP error {e.status_code}: {e.message}")
```

| Exception | HTTP | Behavior |
|-----------|------|----------|
| `AuthenticationError` | 401, 403 | Auto re-auth once on 401, then raise |
| `NotFoundError` | 404 | Raise immediately |
| `ConflictError` | 409 | Raise immediately |
| `RetryableError` | 408, 429, 500, 503, 504 | Exponential backoff, then raise |
| `UpstreamError` | 502 | Raise immediately (no retry) |

## Configuration file

`~/.rahcp/config.yaml` (default). For a project-local config you MUST pass `--config`
(see the gotcha in `SKILL.md`). Priority: CLI flags > env (`HCP_*`, `IIIF_*`) > config > defaults.

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
    bulk_workers: 60                 # concurrent transfers (0 in CLI = use config)
    bulk_presign_batch_size: 500     # URLs presigned per API call
    bulk_chunk_size: 4194304         # 4 MB streaming chunk for large files
    bulk_stream_threshold: 104857600 # 100 MB — files below this read in one shot
    bulk_queue_depth: 16             # queue = workers x depth
    bulk_tracker_flush_every: 500    # SQLite write frequency
    bulk_tracker_prefix: ""          # prefix tracker DB names per dataset

    # IIIF settings
    iiif_url: https://iiifintern-ai.ra.se
    iiif_query_params: full/max/0/default.jpg
    iiif_workers: 4
    iiif_referer: https://sok.riksarkivet.se/  # some servers 403 without it
```
