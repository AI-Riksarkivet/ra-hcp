# Data Explorer + SQL Query Feature

## Context

Add a data exploration and SQL query interface to the HCP frontend, inspired by the Lance Data Viewer reference project. Users can:
1. **Browse** data files on HCP S3 — view schema, select columns, paginate rows (like Lance Data Viewer)
2. **Query** data files with SQL — write arbitrary queries against S3-hosted files (DuckDB)

Both run **server-side** in the Python backend to avoid browser memory limits for GB-sized files.

## Architecture

```
Frontend                             Backend (FastAPI)                     HCP S3
┌──────────────────────┐            ┌────────────────────────────┐        ┌─────────┐
│ Dataset Browser      │──REST API─▶│ DuckDB engine              │──S3──▶│ Buckets │
│   schema, columns,   │            │   + httpfs (S3 access)     │        │ Objects │
│   rows, pagination   │            │   + Lance extension        │        │ .lance  │
│                      │            │   + S3 secrets (HCP creds) │        │ .parquet│
│ SQL Editor           │            │                            │        │ .csv    │
│   textarea + results │◀──JSON────│                            │        └─────────┘
└──────────────────────┘            └────────────────────────────┘
```

**Approach:** DuckDB handles everything — it can query Parquet, CSV, JSON natively and Lance files via the community extension. One engine, all formats. The browse/inspect endpoints are sugar over DuckDB SQL internally.

## Backend Files to Create

### 1. `backend/app/schemas/sql.py` — Pydantic models

```python
class SqlQueryRequest(BaseModel):
    sql: str = Field(description="SQL query to execute")
    limit: int = Field(10000, ge=1, le=100000, description="Max rows")

class SqlQueryResponse(BaseModel):
    columns: list[str]
    rows: list[list]
    row_count: int
    duration_ms: float
    truncated: bool

class DatasetSchemaField(BaseModel):
    name: str
    type: str
    nullable: bool
    is_vector: bool = False

class DatasetSchemaResponse(BaseModel):
    fields: list[DatasetSchemaField]

class DatasetRowsRequest(BaseModel):
    bucket: str
    key: str
    limit: int = Field(50, ge=1, le=200)
    offset: int = Field(0, ge=0)
    columns: list[str] | None = None

class DatasetRowsResponse(BaseModel):
    rows: list[dict]
    total: int
    limit: int
    offset: int
```

### 2. `backend/app/services/duckdb_service.py` — DuckDB service

Per-request DuckDB connection configured with user's HCP S3 credentials:

```python
import duckdb

class DuckDBService:
    def __init__(self, s3_endpoint: str, access_key: str, secret_key: str):
        self.conn = duckdb.connect(':memory:')
        self.conn.execute("INSTALL httpfs; LOAD httpfs;")
        # Try loading Lance extension (optional, may not be available)
        try:
            self.conn.execute("INSTALL lance FROM community; LOAD lance;")
        except Exception:
            pass  # Lance support optional
        # Configure S3 for HCP
        self.conn.execute(f"""
            CREATE SECRET (TYPE S3, KEY_ID '{access_key}',
                SECRET '{secret_key}', ENDPOINT '{s3_endpoint}',
                URL_STYLE 'path', USE_SSL true);
        """)

    def execute_query(self, sql: str, limit: int) -> SqlQueryResponse: ...
    def get_schema(self, s3_path: str) -> DatasetSchemaResponse: ...
    def get_rows(self, s3_path: str, limit, offset, columns) -> DatasetRowsResponse: ...
    def close(self): self.conn.close()
```

Schema inspection: `DESCRIBE SELECT * FROM 's3://bucket/file.parquet'`
Row fetching: `SELECT {columns} FROM 's3://...' LIMIT {limit} OFFSET {offset}`

### 3. `backend/app/api/v1/endpoints/sql.py` — Endpoints

Two modes of operation:

```python
router = APIRouter(prefix="/sql", tags=["SQL"])

# Free-form SQL query
@router.post("", response_model=SqlQueryResponse)
async def execute_sql(body: SqlQueryRequest, ...): ...

# Dataset browsing (inspired by Lance Data Viewer)
@router.get("/schema", response_model=DatasetSchemaResponse)
async def get_schema(bucket: str, key: str, ...): ...

@router.get("/rows", response_model=DatasetRowsResponse)
async def get_rows(bucket: str, key: str, limit: int = 50,
                   offset: int = 0, columns: str | None = None, ...): ...
```

### 4. `backend/app/api/dependencies.py` — DuckDB dependency

Add `get_duckdb_service` that creates a per-request DuckDB connection using the user's S3 creds (from `auth_utils.py`: `base64(username)` / `md5(password)`).

## Frontend Files to Create

### 5. `frontend/src/lib/remote/sql.remote.ts` — Remote functions

```typescript
export const execute_sql = command(z.object({ sql: z.string(), limit: z.number().optional() }), ...);
export const get_dataset_schema = query(async (bucket: string, key: string) => ...);
export const get_dataset_rows = query(async (params: { bucket, key, limit, offset, columns? }) => ...);
```

### 6. `frontend/src/routes/(app)/sql/+page.svelte` — Main page

Two tabs:
- **Browse** — Select a file from S3 → view schema → select columns → paginate rows (like Lance Data Viewer)
- **Query** — SQL editor textarea → run → results table

### 7. `frontend/src/routes/(app)/sql/sections/sql-browser.svelte`

Dataset browser (inspired by Lance Data Viewer):
1. Bucket/file picker (reuse `get_buckets`/`get_objects` from `buckets.remote.ts`)
2. Schema display (field name, type, vector badge)
3. Column selector (multi-select with All/None/Apply)
4. Data table with pagination (using existing DataTable component)

### 8. `frontend/src/routes/(app)/sql/sections/sql-editor.svelte`

- Monospace textarea with example placeholder
- Run button + Ctrl/Cmd+Enter
- Error display below textarea
- Query history (in-memory)

### 9. `frontend/src/routes/(app)/sql/sections/sql-results.svelte`

- Dynamic DataTable from query results (same pattern as `bucket-object-browser.svelte`)
- Footer: "X rows in Y ms"

## Files to Modify

### 10. `frontend/src/lib/components/layout/AppSidebar.svelte`

Add "Analytics" sidebar group with `TerminalSquare` icon → `/sql` route.

### 11. `backend/pyproject.toml`

Add `duckdb` dependency.

### 12. `backend/app/main.py`

Register SQL router.

## Key Patterns to Reuse

- **S3 credentials:** `backend/app/core/auth_utils.py`
- **Auth dependency:** `get_current_user` from `backend/app/api/dependencies.py`
- **Remote functions:** `query()`/`command()` from `frontend/src/lib/remote/buckets.remote.ts`
- **DataTable:** `createSvelteTable` from `frontend/src/lib/components/ui/data-table/index.js`
- **Bucket browsing:** `get_buckets`/`get_objects` for file picker

## Implementation Order

1. Add `duckdb` to `backend/pyproject.toml`
2. Create `backend/app/schemas/sql.py`
3. Create `backend/app/services/duckdb_service.py`
4. Create `backend/app/api/v1/endpoints/sql.py`
5. Register router in `backend/app/main.py`, add dependency
6. Create `frontend/src/lib/remote/sql.remote.ts`
7. Add sidebar entry in `AppSidebar.svelte`
8. Create page + section components
9. Wire together

## Verification

1. Backend: `curl -X POST /api/v1/sql -d '{"sql":"SELECT 1 AS test"}'` → returns rows
2. Backend: `curl /api/v1/sql/schema?bucket=x&key=data.parquet` → returns schema
3. Frontend: `/sql` loads, Browse tab shows file picker, Query tab has editor
4. Select a Parquet file → schema + rows display
5. Write SQL → results show in table
6. `make quality` passes
