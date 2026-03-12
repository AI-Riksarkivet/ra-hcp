# Plan: Extract `rahcp` Python SDK from Backend Services

## Context

The `ra-hcp` monorepo has a well-factored FastAPI backend where services (`MapiService`, `StorageProtocol` adapters, `QueryService`) have **zero FastAPI imports** — they're pure domain logic. However, to use any HCP operation today you must run the full FastAPI server.

By extracting these services into standalone SDK packages, we enable:
- **Programmatic access** — Python scripts can talk to HCP directly without a server
- **CLI** — `rahcp s3 ls`, `rahcp tenant list` for ops/admin tasks
- **Thinner backend** — FastAPI app becomes a thin HTTP adapter over the SDK
- **Reusability** — migration scripts, audit tools, CI/CD pipelines import the SDK directly

The monorepo stays unified: `backend/`, `frontend/`, `docs/`, and new `packages/` all live in `ra-hcp/`. Only Python packages participate in the uv workspace; the frontend (Deno) is unaffected.

## Gains

| Gain | Detail |
|------|--------|
| **No server required** | `from rahcp import HCPClient` — scripts talk to HCP directly |
| **CLI for ops** | `rahcp s3 ls`, `rahcp tenant stats` — replaces curl/manual workflows |
| **Thinner backend** | Backend imports SDK; no duplicated service code |
| **Selective installs** | `pip install rahcp-s3` (40 MB) vs full backend (180 MB) |
| **Better testing** | SDK tested with moto/respx directly, no ASGI transport needed |
| **Independent versioning** | Fix `rahcp-s3` without releasing `rahcp-mapi` |
| **Reusable** | Migration scripts, audit tools import SDK without FastAPI/Redis deps |

## Package Architecture

```
ra-hcp/                              # Workspace root = rahcp umbrella package
├── pyproject.toml                   # name="rahcp"
│                                    # [tool.uv.workspace] members=["packages/*","backend"]
├── uv.lock                          # Single lockfile for entire workspace
├── src/rahcp/
│   ├── __init__.py                  # Re-exports: HCPClient, S3Client, MapiClient
│   └── client.py                    # HCPClient composes S3 + MAPI
│
├── packages/
│   ├── rahcp-core/                  # Shared: auth, config, routing, types
│   │   ├── pyproject.toml           # deps: pydantic, pydantic-settings
│   │   └── src/rahcp_core/
│   │       ├── __init__.py
│   │       ├── auth.py              # <- backend/app/core/auth_utils.py
│   │       ├── config.py            # <- MapiSettings, S3Settings, StorageSettings
│   │       ├── errors.py            # Base RaHcpError
│   │       ├── routing.py           # <- backend/app/core/tenant_routing.py
│   │       └── types.py             # Shared enums from schemas/common.py
│   │
│   ├── rahcp-s3/                    # S3/object storage operations
│   │   ├── pyproject.toml           # deps: rahcp-core, boto3, opentelemetry-api
│   │   └── src/rahcp_s3/
│   │       ├── __init__.py          # Exports: StorageProtocol, StorageError, create_storage
│   │       ├── client.py            # High-level S3Client (NEW)
│   │       ├── protocol.py          # <- storage/protocol.py
│   │       ├── errors.py            # <- storage/errors.py
│   │       ├── _ops.py              # <- adapters/_boto3_ops.py
│   │       ├── adapters/
│   │       │   ├── hcp.py           # <- adapters/hcp.py
│   │       │   └── generic.py       # <- adapters/generic_boto3.py
│   │       ├── factory.py           # create_storage() only (no cached version)
│   │       └── types.py             # S3 response models
│   │
│   ├── rahcp-mapi/                  # HCP Management API + Query API
│   │   ├── pyproject.toml           # deps: rahcp-core, httpx, opentelemetry-api
│   │   └── src/rahcp_mapi/
│   │       ├── __init__.py          # Exports: MapiService, MapiError, QueryService
│   │       ├── client.py            # High-level MapiClient (NEW)
│   │       ├── service.py           # <- mapi_service.py
│   │       ├── errors.py            # <- mapi_errors.py
│   │       ├── query.py             # <- query_service.py
│   │       └── types.py             # <- schemas/query.py
│   │
│   └── rahcp-cli/                   # CLI (optional: pip install rahcp[cli])
│       ├── pyproject.toml           # deps: rahcp, typer, rich
│       └── src/rahcp_cli/
│           ├── __init__.py          # app = typer.Typer()
│           ├── main.py              # Entry point, --endpoint/--profile flags
│           ├── s3.py                # rahcp s3 ls/cp/rm/presign
│           ├── tenant.py            # rahcp tenant list/get/stats
│           ├── namespace.py         # rahcp ns list/create/export
│           └── _output.py           # Rich table/JSON formatting
│
├── backend/                         # FastAPI app (workspace member, imports from SDK)
│   ├── pyproject.toml               # deps: rahcp-s3, rahcp-mapi + fastapi, redis, etc.
│   └── app/...                      # Services become re-export shims
│
├── frontend/                        # SvelteKit app (unchanged, NOT a uv member)
└── docs/                            # Zensical docs
```

**Dependency graph:**
```
rahcp-cli ──→ rahcp ──→ rahcp-s3 ──→ rahcp-core
                    └──→ rahcp-mapi ──→ rahcp-core

backend ──→ rahcp-s3
        └──→ rahcp-mapi
```

## What Moves vs Stays

| Component | → SDK package | Notes |
|-----------|--------------|-------|
| `auth_utils.py` (get_hcp_auth_header, derive_s3_keys) | `rahcp-core/auth.py` | Zero internal deps |
| `tenant_routing.py` (host derivation functions) | `rahcp-core/routing.py` | Zero internal deps |
| `config.py` → MapiSettings, S3Settings, StorageSettings | `rahcp-core/config.py` | Remove hardcoded env_file path |
| `schemas/common.py` → Role, Permission enums | `rahcp-core/types.py` | Shared vocabulary |
| `storage/protocol.py` (StorageProtocol) | `rahcp-s3/protocol.py` | Zero internal deps |
| `storage/errors.py` (StorageError hierarchy) | `rahcp-s3/errors.py` | Only imports botocore |
| `adapters/_boto3_ops.py` (Boto3Operations, Boto3Forwarder) | `rahcp-s3/_ops.py` | Rewrite `app.` → `rahcp_s3.` imports |
| `adapters/hcp.py` (HcpStorage) | `rahcp-s3/adapters/hcp.py` | 3 import rewrites |
| `adapters/generic_boto3.py` (GenericBoto3Storage) | `rahcp-s3/adapters/generic.py` | 3 import rewrites |
| `storage/factory.py` → `create_storage()` only | `rahcp-s3/factory.py` | Keep `create_cached_storage` in backend |
| `mapi_errors.py` (MapiError hierarchy) | `rahcp-mapi/errors.py` | Zero internal deps |
| `mapi_service.py` (MapiService, AuthenticatedMapiService) | `rahcp-mapi/service.py` | Remove CachedMapiService TYPE_CHECKING |
| `query_service.py` (QueryService, AuthenticatedQueryService) | `rahcp-mapi/query.py` | 6 import rewrites |
| `schemas/query.py` (query types) | `rahcp-mapi/types.py` | Zero internal deps |

**Stays in backend (not extracted):**
- `CachedStorage`, `CachedMapiService`, `CachedQueryService` — Redis wrappers
- `CacheService` — Redis client
- `CacheSettings`, `AuthSettings` — backend-only config
- `dependencies.py` — FastAPI DI layer
- `main.py` lifespan — app.state initialization
- All FastAPI endpoints
- `LanceService` — optional vector search

## Import Rewrite Map

### SDK internal imports (files that move)

| File (new location) | Old import | New import |
|---|---|---|
| `rahcp_core/config.py` | `from app.core.auth_utils import derive_s3_keys` | `from rahcp_core.auth import derive_s3_keys` |
| `rahcp_s3/_ops.py` | `from app.services.storage.errors import ...` | `from rahcp_s3.errors import ...` |
| `rahcp_s3/adapters/hcp.py` | `from app.core.config import S3Settings` | `from rahcp_core.config import S3Settings` |
| `rahcp_s3/adapters/hcp.py` | `from app.services.storage.adapters._boto3_ops import ...` | `from rahcp_s3._ops import ...` |
| `rahcp_s3/adapters/generic.py` | `from app.core.config import StorageSettings` | `from rahcp_core.config import StorageSettings` |
| `rahcp_s3/adapters/generic.py` | `from app.services.storage.adapters._boto3_ops import ...` | `from rahcp_s3._ops import ...` |
| `rahcp_s3/factory.py` | `from app.services.storage.adapters.hcp import HcpStorage` | `from rahcp_s3.adapters.hcp import HcpStorage` |
| `rahcp_s3/factory.py` | `from app.services.storage.adapters.generic_boto3 import ...` | `from rahcp_s3.adapters.generic import ...` |
| `rahcp_mapi/service.py` | `from app.core.auth_utils import get_hcp_auth_header` | `from rahcp_core.auth import get_hcp_auth_header` |
| `rahcp_mapi/service.py` | `from app.core.config import MapiSettings` | `from rahcp_core.config import MapiSettings` |
| `rahcp_mapi/service.py` | `from app.services.mapi_errors import ...` | `from rahcp_mapi.errors import ...` |
| `rahcp_mapi/query.py` | `from app.core.tenant_routing import ...` | `from rahcp_core.routing import ...` |
| `rahcp_mapi/query.py` | `from app.schemas.query import ...` | `from rahcp_mapi.types import ...` |

### Backend re-export shims (Phase 6)

Backend files become thin re-exports so **no endpoint code changes**:

| Backend file | Becomes re-export of |
|---|---|
| `app/core/auth_utils.py` | `from rahcp_core.auth import *` |
| `app/core/tenant_routing.py` | `from rahcp_core.routing import *` |
| `app/core/config.py` | Keeps CacheSettings/AuthSettings locally; re-exports MapiSettings/S3Settings/StorageSettings |
| `app/services/mapi_errors.py` | `from rahcp_mapi.errors import *` |
| `app/services/mapi_service.py` | `from rahcp_mapi.service import *` |
| `app/services/query_service.py` | `from rahcp_mapi.query import *` |
| `app/services/storage/protocol.py` | `from rahcp_s3.protocol import *` |
| `app/services/storage/errors.py` | `from rahcp_s3.errors import *` |
| `app/services/storage/adapters/_boto3_ops.py` | `from rahcp_s3._ops import *` |
| `app/services/storage/adapters/hcp.py` | `from rahcp_s3.adapters.hcp import *` |
| `app/services/storage/adapters/generic_boto3.py` | `from rahcp_s3.adapters.generic import *` |
| `app/services/storage/factory.py` | Re-export `create_storage` from SDK; keep `create_cached_storage` locally |
| `app/schemas/query.py` | `from rahcp_mapi.types import *` |

## Key Design Decisions

1. **Root = umbrella package** — follows uv workspace best practice (root is both workspace config and a package)
2. **Config: remove hardcoded env_file** — SDK settings read env vars only; backend passes `_env_file="../.env"` explicitly
3. **OpenTelemetry: api-only in SDK** — `opentelemetry-api` (no-op by default); backend brings `opentelemetry-sdk` with exporters
4. **Re-export shims first** — Phase 6 uses `from rahcp_x import *` shims so zero endpoint code changes; direct imports in follow-up PR
5. **AuthenticatedMapiService type hint** — change `base: MapiService | CachedMapiService` → `base: MapiService` (CachedMapiService conforms at runtime via duck typing)
6. **create_cached_storage stays in backend** — depends on CacheService (Redis), not an SDK concern

## Implementation Phases

### Phase 1: Workspace scaffold
- Create root `pyproject.toml` with `[tool.uv.workspace]` config
- Create `src/rahcp/__init__.py` (empty)
- Create directory structure for all 4 sub-packages with `pyproject.toml` + empty `__init__.py`
- Update `backend/pyproject.toml` to add workspace source deps
- Run `uv sync` — verify resolution works

### Phase 2: Extract `rahcp-core`
- `auth.py` ← copy `app/core/auth_utils.py` (zero changes)
- `routing.py` ← copy `app/core/tenant_routing.py` (zero changes)
- `config.py` ← copy MapiSettings/S3Settings/StorageSettings, remove `env_file`, fix import
- `errors.py` ← new `RaHcpError` base exception
- `types.py` ← copy enums from `schemas/common.py`

### Phase 3: Extract `rahcp-s3`
- `protocol.py` ← copy `storage/protocol.py` (zero changes)
- `errors.py` ← copy `storage/errors.py` (zero changes)
- `_ops.py` ← copy `_boto3_ops.py` (1 import rewrite)
- `adapters/hcp.py` ← copy (3 import rewrites)
- `adapters/generic.py` ← copy (3 import rewrites)
- `factory.py` ← copy `create_storage()` only (4 import rewrites)

### Phase 4: Extract `rahcp-mapi`
- `errors.py` ← copy `mapi_errors.py` (zero changes)
- `service.py` ← copy `mapi_service.py` (3 import rewrites, remove CachedMapiService type)
- `query.py` ← copy `query_service.py` (6 import rewrites)
- `types.py` ← copy `schemas/query.py` (zero changes)

### Phase 5: Create `rahcp` umbrella
- `client.py` — `HCPClient` composing S3Client + MapiService + QueryService
- `__init__.py` — re-exports from sub-packages

### Phase 6: Update backend imports
- Replace extracted files with re-export shims (`from rahcp_x import *`)
- Split `config.py`: keep CacheSettings/AuthSettings, re-export SDK settings
- Split `factory.py`: keep `create_cached_storage`, re-export `create_storage`
- **Zero changes to endpoint files or test files**

### Phase 7: Create `rahcp-cli` (can defer)
- CLI entry point with typer subcommands
- `rahcp s3 ls/cp/rm`, `rahcp tenant list/get`, `rahcp ns list/create`

### Phase 8: SDK test suites
- `rahcp-core/tests/` — auth, config, routing tests
- `rahcp-s3/tests/` — moto integration tests, error mapping, factory
- `rahcp-mapi/tests/` — respx-mocked MAPI, query service tests

### Phase 9: Verify everything
- `uv sync` from root
- `uv run --package rahcp-core pytest` / `--package rahcp-s3` / `--package rahcp-mapi`
- `cd backend && uv run pytest` — all existing tests pass
- `make quality` — ruff/deno/prettier/svelte-check clean
- `uv run python -c "from rahcp import HCPClient"` — works

## pyproject.toml Configurations

### Root `pyproject.toml`
```toml
[project]
name = "rahcp"
version = "0.1.0"
description = "Python SDK for Hitachi Content Platform — S3 + MAPI"
requires-python = ">=3.13"
dependencies = ["rahcp-s3", "rahcp-mapi"]

[project.optional-dependencies]
cli = ["rahcp-cli"]

[tool.uv.workspace]
members = ["packages/*", "backend"]

[tool.uv.sources]
rahcp-s3 = { workspace = true }
rahcp-mapi = { workspace = true }
rahcp-cli = { workspace = true }
rahcp-core = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### `packages/rahcp-core/pyproject.toml`
```toml
[project]
name = "rahcp-core"
version = "0.1.0"
description = "Shared auth, config, routing, and types for rahcp"
requires-python = ">=3.13"
dependencies = ["pydantic>=2.12", "pydantic-settings>=2.13"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### `packages/rahcp-s3/pyproject.toml`
```toml
[project]
name = "rahcp-s3"
version = "0.1.0"
description = "S3 storage operations for Hitachi Content Platform"
requires-python = ">=3.13"
dependencies = ["rahcp-core", "boto3>=1.42", "opentelemetry-api>=1.29"]

[tool.uv.sources]
rahcp-core = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### `packages/rahcp-mapi/pyproject.toml`
```toml
[project]
name = "rahcp-mapi"
version = "0.1.0"
description = "MAPI + Metadata Query client for Hitachi Content Platform"
requires-python = ">=3.13"
dependencies = ["rahcp-core", "httpx>=0.28", "opentelemetry-api>=1.29"]

[tool.uv.sources]
rahcp-core = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### `packages/rahcp-cli/pyproject.toml`
```toml
[project]
name = "rahcp-cli"
version = "0.1.0"
description = "CLI for Hitachi Content Platform operations"
requires-python = ">=3.13"
dependencies = ["rahcp", "typer>=0.15", "rich>=13.0"]

[project.scripts]
rahcp = "rahcp_cli.main:app"

[tool.uv.sources]
rahcp = { workspace = true }

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Updated `backend/pyproject.toml`
```toml
[project]
name = "hcp-backend"
version = "0.1.0"
description = "FastAPI backend for HCP Unified API"
requires-python = ">=3.13"
dependencies = [
    "rahcp-s3",
    "rahcp-mapi",
    "fastapi>=0.133",
    "opentelemetry-sdk>=1.29",
    "opentelemetry-instrumentation-fastapi>=0.50b0",
    "opentelemetry-instrumentation-httpx>=0.50b0",
    "opentelemetry-exporter-otlp>=1.29",
    "pyjwt>=2.11",
    "python-multipart>=0.0.22",
    "redis[hiredis]>=5.0",
    "pyarrow>=17.0",
]
# ... rest unchanged, add:
[tool.uv.sources]
rahcp-s3 = { workspace = true }
rahcp-mapi = { workspace = true }
rahcp-core = { workspace = true }
```

## Usage Examples (end result)

### SDK
```python
from rahcp import HCPClient

client = HCPClient.from_env()              # reads HCP_HOST, HCP_USERNAME, etc.
buckets = client.s3.list_buckets()
await client.mapi.fetch_json("/tenants", username="admin", password="p@ss")
await client.close()
```

### CLI
```bash
export HCP_ENDPOINT=https://hcp.example.com
export HCP_ACCESS_KEY=...
export HCP_SECRET_KEY=...

rahcp s3 ls my-bucket/
rahcp s3 cp ./local.zip my-bucket/archive/
rahcp tenant list
rahcp ns list my-tenant --verbose
rahcp ns export my-tenant my-namespace > ns-config.json
```

### Selective install
```bash
pip install rahcp-s3          # Just S3 (40 MB)
pip install rahcp-mapi        # Just MAPI (10 MB)
pip install rahcp             # Both (45 MB)
pip install rahcp[cli]        # Both + CLI (50 MB)
```
