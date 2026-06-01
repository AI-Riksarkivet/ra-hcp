# rahcp-tracker

Standalone package for pluggable transfer state tracking. Used by both `rahcp-client` (S3 bulk transfers) and `rahcp-iiif` (IIIF downloads).

```bash
uv pip install rahcp-tracker
```

| Class | Description |
|-------|-------------|
| `TrackerProtocol` | Interface — `mark()`, `commit()`, `close()`, `summary()`, `done_keys()`, `error_entries()`, `error_details()`, `unverified_keys()`, `unvalidated_keys()` |
| `SqliteTracker` | Default SQLite implementation with WAL mode and buffered writes |
| `TransferTracker` | Backwards-compatible alias for `SqliteTracker` |
| `Transfer` | SQLModel table definition — shared across SQLite and Postgres |
| `TransferStatus` | Enum: `pending`, `done`, `error` |

```python
from rahcp_tracker import SqliteTracker, TransferStatus
tracker = SqliteTracker(Path("my-job.db"))
tracker.mark("file.jpg", 12345, TransferStatus.done, etag='"abc"', validated=True)
print(tracker.summary())  # {"pending": 0, "done": 1, "error": 0}
tracker.close()
```

The `Transfer` model in `models.py` tracks: `key`, `size`, `status`, `error`, `etag`, `validated`, `verified`, `updated_at`.

## Inspecting failures

`error_entries()` returns `(key, size)` pairs — used to drive retries.
`error_details()` additionally surfaces the recorded **reason**, which the bulk
and streaming engines prefix with the **phase** so you can tell *where* each
image failed without inferring from the message:

```python
for key, size, reason in tracker.error_details():
    print(f"{key}: {reason}")
# C0074667/..._00009.jpg: download: ReadTimeout
# C0074667/..._00012.jpg: validate: Missing JPEG EOI marker (possibly truncated)
# C0074667/..._00031.jpg: upload: 502 Bad Gateway
```

Phases: `download:` (IIIF fetch), `validate:` (corrupt/truncated bytes),
`upload:` (presigned PUT), `verify:` (post-upload size mismatch). A plain re-run
retries every non-`done` key; `--retry-errors` (CLI) retries only the failed ones.
