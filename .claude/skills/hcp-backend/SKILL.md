---
name: hcp-backend
description: >
  HCP backend design patterns and mock server conventions.
  Use when: writing FastAPI endpoints, adding mock server routes,
  creating Pydantic schemas, or working with backend Python code.
---

# HCP Backend — Patterns & Conventions

## Stack

- **FastAPI** with async handlers
- **Pydantic v2** schemas for request/response models
- **uv** for dependency management
- **ruff** for linting/formatting, **ty** for type checking
- Quality: `make quality` runs ruff format/check + ty check

## Project Layout

```
backend/
├── app/
│   ├── api/v1/
│   │   ├── endpoints/mapi/    # MAPI API endpoints (tenant management)
│   │   │   ├── namespace/     # Namespace CRUD + sub-resources
│   │   │   ├── user.py        # User management
│   │   │   ├── group.py       # Group management
│   │   │   └── ...
│   │   ├── endpoints/s3/      # S3-compatible API
│   │   └── router.py          # Route registration
│   ├── schemas/               # Pydantic models
│   │   ├── common.py          # Shared types (Role enum, etc.)
│   │   └── ...
│   └── core/                  # Config, dependencies, auth
├── mock_server/
│   ├── mapi_state.py          # Request dispatcher + in-memory state
│   └── fixtures.py            # Seed data for development
└── tests/
    └── mapi/                  # API tests
```

## Mock Server

The mock server (`mock_server/`) provides a fake HCP MAPI backend for
frontend development. It uses in-memory state, not a database.

### State structure

```python
state.tenants = { "tenant-name": { ... } }
state.namespaces = { "tenant": { "ns-name": { ... } } }
state.ns_settings = { ("tenant", "ns"): { "protocols": {...}, "compliance": {...}, ... } }
state.users = { "tenant": { "username": { ... } } }
state.groups = { "tenant": { "groupname": { ... } } }
```

### Adding a new mock route

1. Find the dispatcher method in `mapi_state.py` (e.g., `_handle_namespaces`)
2. Parse URL segments to determine the sub-resource
3. Return JSON from state, or modify state for POST/PUT/DELETE
4. Match the exact response shape that the real HCP MAPI returns

### Important rules

- **Enum values must match Pydantic schemas exactly**
  - Roles: `ADMINISTRATOR`, `SECURITY`, `MONITOR`, `COMPLIANCE`
  - NOT `ADMIN`, `admin`, etc.
- **Fixture data in `fixtures.py`** must use these exact values
- **Response format**: MAPI wraps responses in XML-like JSON structures
  (e.g., `{ "name": { "namespaceSettings": [...] } }`)

## Required Checklist for Every Backend Change

Any change to the backend **MUST** include all three:

1. **Backend endpoint** — the actual FastAPI route in `app/api/v1/endpoints/`
2. **Mock server support** — matching route in `mock_server/mapi_state.py` + seed data in `fixtures.py`
3. **Tests** — pytest tests in `backend/tests/` covering the new/changed endpoint

The mock server is what the frontend develops against. If a backend endpoint
exists but the mock doesn't handle it, the frontend cannot be tested locally.
Never skip the mock or tests — they are not optional.

## Endpoint Pattern

```python
@router.get("/tenants/{tenant_name}/namespaces/{ns_name}")
async def get_namespace(
    tenant_name: str,
    ns_name: str,
    verbose: bool = False,
    request: Request = None,
):
    url = f"{base_url}/mapi/tenants/{tenant_name}/namespaces/{ns_name}"
    params = {"verbose": str(verbose).lower()} if verbose else {}
    response = await client.get(url, params=params)
    return handle_response(response)
```

## Required Skills

When working on backend code, **always activate these skills**:

- `astral:ruff` — Python linting and formatting
- `astral:uv` — Python package management
- `testing-python` — pytest patterns and best practices

## Testing

Tests live in `backend/tests/` and use pytest with async support.

```python
@pytest.mark.asyncio
async def test_export_namespace(client):
    response = await client.get("/api/v1/mapi/tenants/test/namespaces/ns1/export")
    assert response.status_code == 200
    data = response.json()
    assert "name" not in data  # read-only fields stripped
```
