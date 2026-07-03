# IIIF image downloads (`rahcp_iiif`)

Downloads images from Riksarkivet IIIF endpoints (or any IIIF server), parallel and
resumable via a tracker.

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

```bash
rahcp iiif download C0074667 -o ./images/ --workers 10
rahcp iiif download-batches batches.txt -o ./images/ --workers 10 --validate   # one batch ID per line
rahcp iiif download C0074667 -o ./images/ -q "full/,1200/0/default.jpg"        # scale to 1200px height
```

## `query_params` reference

| Value | Description |
|-------|-------------|
| `full/max/0/default.jpg` | Full resolution (default) |
| `full/,1200/0/default.jpg` | Scale to 1200px height |
| `full/800,/0/default.jpg` | Scale to 800px width |
| `full/200,200/0/default.jpg` | Fixed 200x200 thumbnail |

## IIIF → HCP in two passes

```bash
rahcp iiif download-batches batches.txt -o ./images/ --validate --workers 10  # -> .rahcp/.iiif-download.db
rahcp s3 upload-all images-batch ./images/ --validate --workers 20            # -> .rahcp/.upload-tracker.db
```

Both trackers are independent and resumable. Use `--tracker-prefix` to keep separate
DBs per dataset (SQLite only), or set `bulk_tracker_prefix` in config:

```bash
rahcp s3 upload-all bucket ./andraarkiv --tracker-prefix andraarkiv          # -> .rahcp/andraarkiv.upload-tracker.db
rahcp iiif download-batches job.txt --tracker-prefix familysearch            # -> .rahcp/familysearch.iiif-download.db
```

Some IIIF servers 403 without a `Referer` — set `iiif_referer` in config.
