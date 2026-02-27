Synchronize the Zensical documentation with the current API source code.

**GOAL:** Ensure docs/ accurately reflects the actual FastAPI endpoints, schemas, and services in backend/.

**STEPS:**

1. **Read the current API source** — scan all files in these directories:
   - `backend/app/api/v1/endpoints/` (all endpoint modules)
   - `backend/app/schemas/` (all Pydantic models)
   - `backend/app/services/` (S3Service, MapiService)
   - `backend/app/core/config.py` (environment variables)
   - `backend/app/core/security.py` (auth mechanism)
   - `backend/app/main.py` (app setup, tags, middleware)

2. **Read the current docs** — read all markdown files under `docs/`.

3. **Compare and identify drift:**
   - New endpoints not documented
   - Removed endpoints still documented
   - Changed request/response schemas (fields added, removed, renamed)
   - Changed environment variables or configuration
   - Changed authentication flow

4. **Update the docs** to match the source code:
   - `docs/getting-started/index.md` — quick start, run commands
   - `docs/getting-started/configuration.md` — environment variables table
   - `docs/api/authentication.md` — auth flow, JWT details
   - `docs/api/s3-buckets.md` — all bucket endpoints with parameters
   - `docs/api/s3-objects.md` — all object endpoints with parameters
   - `docs/api/tenants.md` — tenant management endpoints
   - `docs/api/namespaces.md` — namespace management endpoints
   - `docs/api/system.md` — system-level endpoints (replication, erasure coding, statistics, licenses, logs, network, support, health check, user/group accounts)

5. **Update navigation** — if new doc pages are needed, update `zensical.toml` nav.

**FORMAT RULES:**
- Use Zensical/MkDocs markdown (admonitions, code blocks, tables)
- Each API page should have: description, endpoint table (method, path, description), request/response parameter tables, and example usage
- Keep content concise — reference the OpenAPI docs for full details
- Use `!!! tip` or `!!! warning` admonitions for important notes

**IMPORTANT:**
- Only update docs that are actually out of date — do not rewrite pages that are already correct
- Do not remove content that is manually authored and still valid
- Report a summary of what changed when done
