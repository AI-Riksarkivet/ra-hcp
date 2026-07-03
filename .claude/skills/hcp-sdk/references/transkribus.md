# Transkribus exports (`rahcp_transkribus`)

Export ground-truth PAGE/ALTO XML + page images from a Transkribus collection to a
local dir, or stream straight into a bucket. Same tracker-based resumability as IIIF.

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

Output keys are relative (`{collection}/{docId}_{title}/{page|alto|images}/{name}`) so
they double as local paths and S3 keys. `fmt="alto"` converts PAGE→ALTO on the fly —
needs the `alto` extra (`pip install "rahcp[alto]"`, which pulls `ocrd-page-to-alto`).

```bash
rahcp transkribus export 1944790 -o ./export -U me@example.se -P secret
rahcp transkribus upload 1944790 my-bucket --prefix medieval/ --on-conflict skip
```

## Scheduled sync (export + upload in one pass)

`rahcp transkribus upload` is a single idempotent job for any scheduler (cron, Argo
`CronWorkflow`, k8s `CronJob`). `--archive-dir` tees a local copy while streaming to the
bucket, so **one run does both the export and the upload**:

```bash
rahcp transkribus upload 1944790 my-bucket --prefix medieval/ \
  --archive-dir /data/transkribus \   # local copy of every file (the "export")
  --validate --verify \               # byte-check + size-verify
  --on-conflict skip                  # keep what's already in the bucket
```

Guarantees for repeated runs: **idempotent** (tracker skips done files; re-runs
converge), **validated/verified**, **fails loud** (`--fail-on-error`, default on, exits
non-zero so the scheduler marks the run failed; `--no-fail-on-error` forces 0). Exit
codes: `0`=all done, `1`=failed (re-run resumes), `130`=interrupted. A plain re-run
picks up **new** pages/docs and retries failures. **Persist the tracker DB** (and
`--archive-dir`) across runs (mounted volume, or a `postgresql://` DSN).

## Catching corrected transcripts — `--check-updates`

A transcript re-corrected in Transkribus gets a new `tsId` but keeps the same object
key, so a plain re-run skips it. `--check-updates` remembers each transcript's synced
`tsId` (sidecar DB `<tracker-db>.versions.db`, or `--version-db`) and re-uploads **only**
the changed ones (implies overwrite — see the HCP 409 overwrite gotcha in `SKILL.md`):

```bash
rahcp transkribus upload 1944790 my-bucket --prefix medieval/ --check-updates
```

Conflict-policy details (`skip`/`overwrite`/`error`) are in [s3.md](s3.md).
