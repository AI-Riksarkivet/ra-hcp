# Architecture

This page describes the overall design of the HCP application, how the backend and frontend work together, and the key architectural decisions.

## System Overview

```mermaid
graph TB
    subgraph "Browser"
        FE["SvelteKit Frontend<br/>:5173"]
    end

    subgraph "Backend Server"
        API["FastAPI Backend<br/>:8000"]
        MW["Middleware Stack<br/>CORS · GZip · RequestID"]
        AUTH["JWT Auth<br/>OAuth2 Password Flow"]
    end

    subgraph "Services Layer"
        MAPI["MapiService<br/>HCP Management API"]
        S3["StorageProtocol<br/>Backend-agnostic S3"]
        QUERY["QueryService<br/>Metadata Query"]
        CACHE["CacheService<br/>Redis (optional)"]
    end

    subgraph "External Systems"
        HCP["HCP System<br/>Management API :9090"]
        S3EP["HCP S3 Endpoint<br/>Object Storage"]
        REDIS["Redis<br/>(optional)"]
    end

    FE -->|"REST API<br/>JWT Bearer"| API
    API --> MW --> AUTH
    AUTH --> MAPI
    AUTH --> S3
    AUTH --> QUERY
    MAPI --> CACHE
    S3 --> CACHE
    QUERY --> CACHE
    MAPI -->|"HTTPS :9090"| HCP
    S3 -->|"S3 Protocol"| S3EP
    QUERY -->|"HTTPS"| HCP
    CACHE -->|"Redis Protocol"| REDIS
```

## Request Flow

```mermaid
sequenceDiagram
    participant B as Browser
    participant F as SvelteKit
    participant A as FastAPI
    participant M as Middleware
    participant S as Service Layer
    participant H as HCP System

    B->>F: User action (click, form submit)
    F->>A: HTTP request + JWT token
    A->>M: RequestID + GZip + CORS
    M->>M: Decode JWT → extract credentials
    M->>S: Forward with HCP credentials

    alt Cache hit (Redis enabled)
        S-->>M: Return cached response
    else Cache miss or no Redis
        S->>H: MAPI/S3 request with credentials
        H-->>S: HCP response
        S->>S: Cache response (if Redis enabled)
        S-->>M: Return response
    end

    M-->>A: Add X-Request-ID header
    A-->>F: JSON response
    F-->>B: Update UI reactively
```

## Backend Architecture

The FastAPI backend is organized in layers:

```mermaid
graph TD
    subgraph "API Layer"
        R["Routers<br/>api/v1/endpoints/"]
        DEP["Dependencies<br/>api/dependencies.py"]
    end

    subgraph "Service Layer"
        MS["MapiService"]
        CMS["CachedMapiService"]
        SP["StorageProtocol"]
        SB["StorageBase (ABC)"]
        HCP_A["HcpStorage<br/>boto3 adapter"]
        CHCP["CachedHcpStorage"]
        QS["QueryService"]
        CQS["CachedQueryService"]
        CS["CacheService"]
    end

    subgraph "Core"
        CFG["Config<br/>MapiSettings · S3Settings<br/>CacheSettings · AuthSettings"]
        SEC["Security<br/>JWT · OAuth2"]
        AUTH2["Auth Utils<br/>S3 key derivation"]
        TEL["Telemetry<br/>OpenTelemetry"]
    end

    R --> DEP
    DEP --> MS
    DEP --> CMS
    DEP -->|"type-hints"| SP
    DEP -->|"actual impl"| CHCP
    SP -.->|"structural typing"| SB
    SB -->|"inherits"| HCP_A
    HCP_A -->|"inherits"| CHCP
    CHCP --> CS
    MS --> CFG
    CMS --> MS
    CMS --> CS
    HCP_A --> CFG
    HCP_A --> AUTH2
    QS --> CFG
    CQS --> QS
    CQS --> CS
    R --> SEC
```

### Key Design Decisions

- **Credential pass-through**: The API does not store user passwords. Credentials are embedded in the JWT and forwarded to HCP on each request. HCP is the sole authority for authentication and authorization.

- **Optional caching**: When Redis is configured, `CachedMapiService`, `CachedQueryService`, and `CachedHcpStorage` wrap the base services with TTL-based caching. When Redis is not configured, the base services are used directly.

- **S3 credential derivation**: S3 access keys are derived from HCP credentials (base64-encoded username + MD5-hashed password) per HCP convention. No separate S3 credentials need to be configured.

- **Backend-agnostic storage layer**: The S3 data-plane uses a hybrid Protocol + ABC pattern so storage backends (HCP, MinIO, Ceph, AWS) can be swapped without touching endpoint code. See [Storage Layer Architecture](#storage-layer-architecture) for details.

- **Sync-over-async S3**: Storage operations use synchronous boto3 calls executed via `asyncio.to_thread()`. This avoids the complexity of async S3 clients while keeping the FastAPI event loop non-blocking.

### Backend Router Organization

The API is organized into five endpoint groups, each with distinct auth requirements:

| Group | Prefix | Auth | Examples |
|-------|--------|------|----------|
| **S3 Data-Plane** | `/api/v1/buckets`, `/objects`, `/versions`, `/multipart`, `/credentials` | JWT | Bucket CRUD, object upload/download, presigned URLs |
| **System MAPI** | `/api/v1/mapi/system/` | System admin | Tenant management, replication, erasure coding |
| **Tenant MAPI** | `/api/v1/mapi/tenants/{tenant}/` | Tenant admin/monitor/security | Users, groups, settings, chargeback |
| **Namespace MAPI** | `/api/v1/mapi/tenants/{tenant}/namespaces/` | Admin/compliance | Namespace config, compliance, protocols, CORS |
| **Query** | `/api/v1/query/` | JWT | Metadata search |

## Storage Layer Architecture

The S3 data-plane is designed to be backend-agnostic. Endpoint code type-hints against `StorageProtocol` (structural typing) and never imports backend-specific libraries like `boto3`.

```mermaid
graph TD
    subgraph "Endpoint Code"
        EP["S3 Endpoints<br/>buckets · objects · versions · multipart"]
    end

    subgraph "Contracts"
        SP["StorageProtocol<br/>(Protocol — structural typing)"]
        SB["StorageBase<br/>(ABC — enforced at instantiation)"]
    end

    subgraph "Adapters"
        HCP_A["HcpStorage<br/>boto3 wrapper<br/>HCP-specific workarounds"]
        FUTURE["MinIO / Ceph / AWS<br/>(future adapters)"]
    end

    subgraph "Caching"
        CHCP["CachedHcpStorage<br/>Redis caching layer"]
    end

    EP -->|"type-hints against"| SP
    SP -.->|"structural match"| SB
    SB -->|"inherits"| HCP_A
    SB -.->|"inherits"| FUTURE
    HCP_A -->|"inherits"| CHCP
```

### How it works

| Layer | File | Role |
|-------|------|------|
| `StorageProtocol` | `services/storage/protocol.py` | Structural typing interface — endpoint DI type hints use this |
| `StorageBase` | `services/storage/base.py` | Abstract base class — enforces method implementation at instantiation |
| `HcpStorage` | `services/storage/adapters/hcp.py` | Concrete adapter — wraps boto3 with HCP-specific workarounds |
| `CachedHcpStorage` | `services/cached_s3.py` | Caching decorator — inherits from `HcpStorage`, adds Redis caching |
| `StorageError` | `services/storage/errors.py` | Backend-agnostic exceptions — adapters catch library errors and re-raise |

### Adding a new storage backend

To add support for MinIO, Ceph, or AWS S3:

1. Create `services/storage/adapters/minio.py` (or similar)
2. Inherit from `StorageBase` — the ABC enforces all required methods
3. Catch the backend's native exceptions and re-raise as `StorageError`
4. Register the new adapter in the dependency injection layer
5. No endpoint code changes needed — they type-hint against `StorageProtocol`

### Storage operations

The storage layer supports these operation groups:

| Group | Operations |
|-------|-----------|
| **Buckets** | list, create, head, delete |
| **Objects** | list, put, get, head, delete, copy, bulk delete |
| **Versioning** | get/set bucket versioning, list object versions, version-aware get/delete |
| **ACLs** | get/set bucket ACL, get/set object ACL |
| **Multipart uploads** | create, upload part, complete, abort, list parts |
| **Presigned URLs** | generate for get/put operations |

### HCP-specific workarounds

The `HcpStorage` adapter handles several HCP quirks that differ from standard S3:

| Workaround | Reason |
|------------|--------|
| Disabled S3 region redirector | HCP returns non-standard redirect responses that confuse boto3 |
| Path-style addressing | HCP does not support virtual-hosted bucket names |
| Individual deletes for bulk | HCP requires `Content-MD5` on multi-delete but boto3 sends CRC32 instead |
| OTel span tracing | Every storage operation is traced with bucket, key, and method attributes |

### Namespace protocol configuration

Each HCP namespace supports multiple access protocols configured independently via MAPI:

| Protocol | Schema | Description |
|----------|--------|-------------|
| **HTTP/REST/S3/WebDAV** | `HttpProtocol` | Primary data access protocols with IP-based access control |
| **NFS** | `NfsProtocol` | Network file system mount access |
| **CIFS/SMB** | `CifsProtocol` | Windows file sharing access |
| **SMTP** | `SmtpProtocol` | Email ingestion (storing email as objects) |

Protocol settings are managed through the namespace access endpoints (`/api/v1/mapi/tenants/{tenant}/namespaces/{ns}/protocols/`) and each includes `ipSettings` for IP-based access control.

## Frontend Architecture

The SvelteKit frontend follows a reactive pattern with remote function abstractions and server-side RBAC:

```mermaid
graph TD
    subgraph "Pages"
        P["SvelteKit Routes<br/>+page.svelte"]
        L["Layout Server Load<br/>+layout.server.ts"]
        G["Route Guards<br/>+page.server.ts"]
    end

    subgraph "RBAC"
        HOOK["Server Hook<br/>Token extraction"]
        AL["Access Levels<br/>sys-admin · tenant-admin<br/>namespace-user"]
        GUARD["requireAdmin()<br/>Server-side redirect"]
    end

    subgraph "Components"
        UI["UI Components<br/>DataTable · FormDialog<br/>FileViewer · etc."]
        FEAT["Feature Components<br/>Namespace settings<br/>User management"]
        SIDE["Sidebar<br/>Role-conditional sections"]
    end

    subgraph "Data Layer"
        Q["query()<br/>GET requests with caching"]
        C["command()<br/>POST/PUT/DELETE mutations"]
        REM["Remote Functions<br/>*.remote.ts"]
    end

    subgraph "State"
        ST["$state<br/>Mutable reactive state"]
        DER["$derived<br/>Computed values"]
        EFF["$effect<br/>Side effects"]
    end

    HOOK -->|"JWT cookie"| L
    L -->|"fetch user profile"| REM
    L -->|"accessLevel"| AL
    AL --> G
    G -->|"namespace-user → /buckets"| GUARD
    L --> P
    P --> UI
    P --> FEAT
    SIDE -->|"isAdmin filter"| AL
    FEAT --> Q
    FEAT --> C
    Q --> REM
    C --> REM
    REM -->|"fetch()"| API2["FastAPI Backend"]
    P --> ST
    P --> DER
    P --> EFF
    C -->|".updates(queryData)"| Q
```

### Frontend RBAC

The frontend enforces role-based access control entirely on the server side, making it impossible to bypass via client-side manipulation.

```mermaid
sequenceDiagram
    participant B as Browser
    participant H as hooks.server.ts
    participant L as +layout.server.ts
    participant G as +page.server.ts
    participant A as FastAPI Backend

    B->>H: Request /tenant-settings
    H->>H: Extract hcp_token cookie
    H->>L: event.locals.token

    alt No token
        L-->>B: Redirect → /login
    else Has token
        L->>L: Parse JWT (username, tenant)
        L->>A: GET /userAccounts/{username}?verbose=true
        A-->>L: { roles: [ADMINISTRATOR, ...], userGUID }
        L->>L: getAccessLevel(tenant, roles)

        alt sys-admin (no tenant)
            L-->>G: accessLevel = "sys-admin"
        else tenant-admin (has ADMINISTRATOR role)
            L-->>G: accessLevel = "tenant-admin"
        else namespace-user (other roles)
            L-->>G: accessLevel = "namespace-user"
        end

        G->>G: requireAdmin(accessLevel)

        alt namespace-user on admin route
            G-->>B: Redirect → /buckets
        else admin or sys-admin
            G-->>B: Render page
        end
    end
```

#### Access levels

| Level | Condition | Access |
|-------|-----------|--------|
| **sys-admin** | No tenant in JWT | Full access to all routes |
| **tenant-admin** | Has `ADMINISTRATOR` role | Full access to tenant routes |
| **namespace-user** | Any other role set | Storage routes only (buckets, access control, analytics, settings) |

#### Protected routes

These routes call `requireAdmin()` in their `+page.server.ts` and redirect non-admin users to `/buckets`:

- `/namespaces`, `/namespaces/[namespace]`
- `/users`, `/users/[username]`, `/users/groups/[groupname]`
- `/tenant-settings`
- `/search`
- `/content-classes`, `/content-classes/[name]`

#### Sidebar filtering

The sidebar conditionally renders sections based on access level:

- **All users**: Storage (Buckets, Access Control), Analytics (Data Explorer)
- **Admins only**: Tenant (Namespaces, Users & Groups, Tenant Settings), Search & Indexing (Search, Content Classes)

### Frontend Patterns

- **Remote functions**: All API calls are defined in `*.remote.ts` files using `query()` for reads and `command()` for mutations.

- **Mutation refresh**: After a mutation, `command(...).updates(queryData)` automatically invalidates and refetches the relevant query data.

- **Svelte 5 runes**: Components use `$state` for mutable state, `$derived` for computed values, and `$effect` for async side effects with cancellation.

## Mock Server

For development without an HCP system, the backend includes a mock server:

```mermaid
graph LR
    subgraph "Mock Server"
        DISP["mapi_state.py<br/>Request dispatcher"]
        FIX["fixtures.py<br/>Seed data"]
        STATE["In-memory state<br/>Dict-based storage"]
    end

    API3["FastAPI"] -->|"same interface as<br/>MapiService"| DISP
    FIX -->|"initial data"| STATE
    DISP -->|"CRUD operations"| STATE
```

The mock server implements the same interface as the real MAPI service, allowing the frontend to be developed and tested independently. Start it with `make run-api-mock`.

## Deployment

```mermaid
graph LR
    subgraph "Docker / Production"
        FE2["Frontend<br/>SvelteKit + Node"]
        BE["Backend<br/>FastAPI + uvicorn"]
        RD["Redis<br/>(optional)"]
    end

    LB["Load Balancer /<br/>Reverse Proxy"] --> FE2
    LB --> BE
    BE --> RD
    BE --> HCP2["HCP System"]
    BE --> S3E["HCP S3 Endpoint"]
```

| Component | Technology | Port |
|-----------|-----------|------|
| Frontend | SvelteKit 2 + Svelte 5, Deno | 5173 (dev) |
| Backend | FastAPI, Python 3.12+, uv | 8000 |
| Storage adapters | HcpStorage (boto3) — pluggable via StorageProtocol | — |
| Cache | Redis 7+ (optional) | 6379 |
| HCP MAPI | Hitachi Content Platform | 9090 |
| S3 endpoint | S3-compatible endpoint (HCP, MinIO, Ceph, AWS) | 443 |
