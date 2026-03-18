# Plan: `rahcp` — Lightweight CLI & Client Package

## Goal

Create a pip-installable `rahcp` package with two sub-packages:
- **`rahcp-client`** — thin async httpx wrapper over the backend REST API
- **`rahcp-cli`** — typer/rich CLI that uses `rahcp-client`

This replaces:
- The `hcp_s3.py` helper module baked into Docker images (docs/api/argo.md)
- All copy-paste curl/Python snippets in docs/api/workflows.md and error-handling.md
- Manual httpx boilerplate users write for scripts, Argo pods, migration tools

The backend stays **completely untouched** — this is a pure HTTP client, not a service extraction.

## Package Layout

```
ra-hcp/
├── pyproject.toml                    # name="rahcp", uv workspace root
├── src/rahcp/__init__.py             # Re-exports from rahcp-client
├── packages/
│   ├── rahcp-client/
│   │   ├── pyproject.toml            # deps: httpx
│   │   └── src/rahcp_client/
│   │       ├── __init__.py           # Public API exports
│   │       ├── client.py             # HCPClient — auth, retry, auto-refresh
│   │       ├── s3.py                 # S3Ops — presign, upload, download, bulk, multipart, staging
│   │       ├── mapi.py               # MapiOps — tenant/ns/user/group CRUD, stats
│   │       ├── query.py              # QueryOps — object/operation metadata search
│   │       ├── errors.py             # HCPError hierarchy
│   │       ├── config.py             # HCPSettings (env var config)
│   │       ├── images.py             # validate_tiff, validate_jpg (Pillow optional)
│   │       └── _compat.py            # Stateless function API (hcp_s3 drop-in)
│   │
│   └── rahcp-cli/
│       ├── pyproject.toml            # deps: rahcp-client, typer, rich
│       └── src/rahcp_cli/
│           ├── __init__.py
│           ├── main.py               # Entry point, global flags (--endpoint, --json)
│           ├── auth.py               # rahcp login / rahcp whoami
│           ├── s3.py                 # rahcp s3 ls/upload/download/rm/presign
│           ├── tenant.py             # rahcp tenant list/get/stats/chargeback
│           ├── namespace.py          # rahcp ns list/get/create/export
│           ├── user.py               # rahcp user list/create/delete
│           └── _output.py            # Rich table/JSON formatting helpers
│
├── backend/                          # UNCHANGED — only pyproject.toml adds workspace source
├── frontend/                         # UNCHANGED
└── docs/                             # Update argo.md Dockerfiles to use pip install rahcp-client
```

## Dependency Graph

```
rahcp-cli ──→ rahcp ──→ rahcp-client ──→ httpx
                                      ──→ pydantic-settings (config)

rahcp[images] pulls in Pillow
rahcp[cli] pulls in rahcp-cli (typer + rich)
```

## What Goes Where

### rahcp-client (~400-500 lines)

#### `client.py` — HCPClient
Absorbs patterns from: `error-handling.md` (HCPClient dataclass, retry function), `workflows.md` (login/authed_client helpers)

```python
class HCPClient:
    """Async HTTP client for the HCP Unified API."""
    # Constructor: base_url, username, password, tenant (or from env)
    # Auto-login on __aenter__, auto-refresh on 401
    # Built-in retry with exponential backoff (408, 429, 5xx)
    # Properties: .s3, .mapi, .query (lazy-initialized operation namespaces)
    # Class method: from_env() reads HCP_ENDPOINT, HCP_USERNAME, HCP_PASSWORD, HCP_TENANT
```

#### `s3.py` — S3Ops
Absorbs: all functions from `hcp_s3.py` + bulk ops from `workflows.md`

```python
class S3Ops:
    """S3 data-plane operations."""
    # Constructed with reference to HCPClient._request method

    async def list_buckets() -> dict
    async def list_objects(bucket, prefix, max_keys=1000) -> list[dict]
    async def upload(bucket, key, data: bytes) -> str  # returns etag
    async def upload_file(bucket, key, path: Path) -> str
    async def download(bucket, key, dest: Path) -> int  # returns byte count
    async def download_bytes(bucket, key) -> bytes
    async def delete(bucket, key) -> None
    async def copy(bucket, key, source_bucket, source_key) -> None
    async def head(bucket, key) -> dict

    # Presigned URL operations
    async def presign(bucket, key, method="get_object", expires=600) -> str
    async def presign_bulk(bucket, keys, expires=3600) -> list[dict]

    # Bulk operations
    async def delete_bulk(bucket, keys: list[str]) -> dict
    async def download_zip(bucket, keys: list[str], dest: Path) -> Path

    # Multipart upload (presigned, parallel)
    async def upload_multipart(bucket, key, path: Path, concurrency=6) -> str

    # Staging pattern (from hcp_s3.py)
    async def commit_staging(bucket, staging_prefix, dest_prefix) -> int
    async def cleanup_staging(bucket, staging_prefix) -> int

    # Verification
    async def verify_upload(bucket, key, expected_size: int) -> None
```

#### `mapi.py` — MapiOps
Absorbs: tenant provisioning, user management, monitoring workflows from `workflows.md`

```python
class MapiOps:
    """MAPI management-plane operations."""

    # Tenants
    async def list_tenants(verbose=False) -> list[dict]
    async def get_tenant(tenant, verbose=False) -> dict
    async def create_tenant(tenant_data, username, password) -> dict
    async def update_tenant(tenant, data) -> None

    # Namespaces
    async def list_namespaces(tenant, verbose=False) -> list[dict]
    async def get_namespace(tenant, ns, verbose=False) -> dict
    async def create_namespace(tenant, ns_data) -> dict
    async def update_namespace(tenant, ns, data) -> None
    async def delete_namespace(tenant, ns) -> None
    async def export_namespace(tenant, ns) -> dict
    async def export_namespaces(tenant, names: list[str]) -> dict

    # Users
    async def list_users(tenant, verbose=False) -> list[dict]
    async def get_user(tenant, username, verbose=False) -> dict
    async def create_user(tenant, user_data, password) -> dict
    async def update_user(tenant, username, data) -> None
    async def delete_user(tenant, username) -> None
    async def change_password(tenant, username, old_pw, new_pw) -> None

    # Groups
    async def list_groups(tenant, verbose=False) -> list[dict]
    async def create_group(tenant, group_data) -> dict
    async def delete_group(tenant, group_name) -> None

    # Statistics
    async def get_statistics(tenant) -> dict
    async def get_chargeback(tenant, start, end, granularity="day") -> dict
    async def get_ns_statistics(tenant, ns) -> dict
    async def get_ns_chargeback(tenant, ns, start, end, granularity="day") -> dict

    # Credentials
    async def get_credentials() -> dict
```

#### `query.py` — QueryOps

```python
class QueryOps:
    """Metadata Query API operations."""

    async def search_objects(tenant, query_data) -> dict
    async def search_operations(tenant, query_data) -> dict
```

#### `errors.py`

```python
class HCPError(Exception):
    """Base error for all rahcp operations."""
    status_code: int | None
    message: str

class AuthenticationError(HCPError): ...    # 401
class NotFoundError(HCPError): ...          # 404
class ConflictError(HCPError): ...          # 409
class RetryableError(HCPError): ...         # 408, 429, 5xx
class UploadVerificationError(HCPError): ... # size mismatch after upload
```

#### `config.py`

```python
class HCPSettings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="HCP_")

    endpoint: str = "http://localhost:8000/api/v1"
    username: str = ""
    password: str = ""
    tenant: str | None = None
    timeout: float = 30.0
    max_retries: int = 4
    retry_base_delay: float = 1.0
```

#### `images.py` — Optional Pillow validation
Absorbs: `validate_tiff`, `validate_jpg` from `hcp_s3.py`

```python
def validate_tiff(path: Path) -> None: ...
def validate_jpg(path: Path) -> None: ...
# Raises ImportError with helpful message if Pillow not installed
```

#### `_compat.py` — Drop-in replacement for hcp_s3.py
Stateless sync functions with same signatures as `hcp_s3.py`, so Argo workflows can do `from rahcp_client._compat import *` (or `import rahcp_client.compat as hcp_s3`) with minimal changes.

```python
# Same signatures as hcp_s3.py — sync wrappers around the async client
def read_token(secret_path="/secrets/source/token") -> str: ...
def auth_headers(token: str) -> dict[str, str]: ...
def presign(base, token, bucket, key, method, expires=600) -> str: ...
def download(base, token, bucket, key, dest) -> int: ...
def upload(base, token, bucket, key, data) -> str: ...
def verify_upload(base, token, bucket, key, expected_size) -> None: ...
def list_objects(base, token, bucket, prefix, max_keys=1000) -> list[dict]: ...
def delete_keys(base, token, bucket, keys) -> None: ...
def commit_staging(base, token, bucket, staging_prefix, dest_prefix) -> int: ...
def cleanup_staging(base, token, bucket, staging_prefix) -> int: ...
def validate_tiff(path) -> None: ...
def validate_jpg(path) -> None: ...
```

### rahcp-cli (~400-600 lines)

#### `main.py`

```
rahcp [--endpoint URL] [--json] [--token TOKEN] COMMAND

Global options:
  --endpoint   HCP API base URL (default: $HCP_ENDPOINT or http://localhost:8000/api/v1)
  --json       Output raw JSON instead of formatted tables
  --token      Bearer token (default: from ~/.rahcp/token or $HCP_TOKEN)
```

#### Commands

```
rahcp login                                    # Interactive login, stores token in ~/.rahcp/token
rahcp whoami                                   # Show current user info

rahcp s3 ls [BUCKET] [--prefix PREFIX]         # List buckets or objects
rahcp s3 upload BUCKET KEY FILE                # Upload a local file
rahcp s3 download BUCKET KEY [--output FILE]   # Download an object
rahcp s3 rm BUCKET KEY [KEY...]                # Delete one or more objects
rahcp s3 cp BUCKET KEY DEST_BUCKET DEST_KEY    # Copy object
rahcp s3 presign BUCKET KEY [--expires 3600]   # Get presigned download URL
rahcp s3 credentials                           # Show S3 access/secret keys

rahcp tenant list [--verbose]                  # List tenants
rahcp tenant get TENANT [--verbose]            # Get tenant details
rahcp tenant stats TENANT                      # Tenant statistics
rahcp tenant chargeback TENANT --start --end   # Chargeback report

rahcp ns list TENANT [--verbose]               # List namespaces
rahcp ns get TENANT NS [--verbose]             # Get namespace details
rahcp ns create TENANT --name --quota          # Create namespace
rahcp ns export TENANT NS [--output FILE]      # Export namespace template
rahcp ns delete TENANT NS                      # Delete namespace

rahcp user list TENANT [--verbose]             # List users
rahcp user get TENANT USERNAME                 # Get user details
rahcp user create TENANT USERNAME --password   # Create user
rahcp user delete TENANT USERNAME              # Delete user
```

## pyproject.toml Configurations

### Root `pyproject.toml` (NEW)

```toml
[project]
name = "rahcp"
version = "0.1.0"
description = "Python SDK & CLI for HCP Unified API"
requires-python = ">=3.13"
dependencies = ["rahcp-client"]

[project.optional-dependencies]
images = ["rahcp-client[images]"]
cli = ["rahcp-cli"]
all = ["rahcp-client[images]", "rahcp-cli"]

[tool.uv.workspace]
members = ["packages/*", "backend"]

[tool.uv.sources]
rahcp-client = { workspace = true }
rahcp-cli = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### `packages/rahcp-client/pyproject.toml`

```toml
[project]
name = "rahcp-client"
version = "0.1.0"
description = "Async Python client for HCP Unified API"
requires-python = ">=3.13"
dependencies = ["httpx>=0.28", "pydantic-settings>=2.13"]

[project.optional-dependencies]
images = ["pillow>=11.0"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### `packages/rahcp-cli/pyproject.toml`

```toml
[project]
name = "rahcp-cli"
version = "0.1.0"
description = "CLI for HCP Unified API"
requires-python = ">=3.13"
dependencies = ["rahcp-client", "typer>=0.15", "rich>=13.0"]

[project.scripts]
rahcp = "rahcp_cli.main:app"

[tool.uv.sources]
rahcp-client = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Updated `backend/pyproject.toml` (minimal change)

Add workspace source so backend CAN import rahcp-client if desired (not required initially):

```toml
# Add at end of existing file:
[tool.uv.sources]
rahcp-client = { workspace = true }
```

## Implementation Phases

### Phase 1: Workspace scaffold
1. Create root `pyproject.toml` with workspace config
2. Create `src/rahcp/__init__.py`
3. Create `packages/rahcp-client/` directory structure with `pyproject.toml` + empty `__init__.py`
4. Create `packages/rahcp-cli/` directory structure with `pyproject.toml` + empty `__init__.py`
5. Add `[tool.uv.sources]` to `backend/pyproject.toml`
6. Run `uv sync` — verify workspace resolves

### Phase 2: rahcp-client core
1. `errors.py` — HCPError hierarchy
2. `config.py` — HCPSettings with env var support
3. `client.py` — HCPClient with auth, retry, auto-refresh, operation namespace properties

### Phase 3: rahcp-client operations
1. `s3.py` — S3Ops (presign, upload, download, bulk, multipart, staging)
2. `mapi.py` — MapiOps (tenant/ns/user/group CRUD, stats, chargeback)
3. `query.py` — QueryOps (object/operation search)
4. `images.py` — validate_tiff, validate_jpg with optional Pillow
5. `_compat.py` — sync drop-in for hcp_s3.py
6. `__init__.py` — public API exports

### Phase 4: rahcp-cli
1. `_output.py` — Rich table/JSON formatting
2. `main.py` — Typer app with global options
3. `auth.py` — login/whoami commands
4. `s3.py` — s3 subcommands
5. `tenant.py` — tenant subcommands
6. `namespace.py` — namespace subcommands
7. `user.py` — user subcommands

### Phase 5: Umbrella + quality
1. Wire `src/rahcp/__init__.py` re-exports
2. Update `Makefile` — add `fmt`/`lint` targets for packages
3. Run `uv sync && make quality`

### Phase 6: Verify
1. `uv run python -c "from rahcp import HCPClient"` works
2. `uv run rahcp --help` works
3. `cd backend && uv run pytest` — existing tests still pass

## Makefile Updates

```makefile
# Updated fmt target
fmt:
	cd backend && uvx ruff format .
	cd packages/rahcp-client && uvx ruff format .
	cd packages/rahcp-cli && uvx ruff format .
	cd frontend && deno task fmt

# Updated lint target
lint:
	cd backend && uvx ruff check .
	cd packages/rahcp-client && uvx ruff check .
	cd packages/rahcp-cli && uvx ruff check .
	cd frontend && deno lint
```

## Usage After Implementation

### Argo Dockerfile (replaces COPY hcp_s3.py)

```dockerfile
FROM python:3.13-slim
RUN pip install --no-cache-dir rahcp-client[images]
```

### Argo workflow pod code

```python
# Before:
import hcp_s3
size = hcp_s3.download(BASE, TOKEN, BUCKET, KEY, Path("/tmp/data"))

# After (drop-in compat):
from rahcp_client._compat import download
size = download(BASE, TOKEN, BUCKET, KEY, Path("/tmp/data"))

# After (recommended async style):
from rahcp_client import HCPClient

async with HCPClient.from_env() as hcp:
    size = await hcp.s3.download(BUCKET, KEY, Path("/tmp/data"))
```

### CLI

```bash
pip install rahcp[cli]
rahcp login --endpoint https://hcp-api.internal
rahcp s3 ls my-bucket --prefix reports/
rahcp tenant stats my-tenant
rahcp ns export my-tenant datasets > template.json
```

### Scripts

```python
pip install rahcp

from rahcp import HCPClient

async with HCPClient(
    endpoint="https://hcp-api.internal/api/v1",
    username="admin",
    password="secret",
    tenant="my-tenant",
) as hcp:
    buckets = await hcp.s3.list_buckets()
    stats = await hcp.mapi.get_statistics("my-tenant")
    await hcp.s3.upload("my-bucket", "data.json", b'{"key": "value"}')
```
