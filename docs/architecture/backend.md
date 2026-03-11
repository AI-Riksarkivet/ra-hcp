# Backend Architecture

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

## Key Design Decisions

- **Credential pass-through**: The API does not store user passwords. Credentials are embedded in the JWT and forwarded to HCP on each request. HCP is the sole authority for authentication and authorization.

- **Optional caching**: When Redis is configured, `CachedMapiService`, `CachedQueryService`, and `CachedHcpStorage` wrap the base services with TTL-based caching. When Redis is not configured, the base services are used directly.

- **S3 credential derivation**: S3 access keys are derived from HCP credentials (base64-encoded username + MD5-hashed password) per HCP convention. No separate S3 credentials need to be configured.

- **Backend-agnostic storage layer**: The S3 data-plane uses a hybrid Protocol + ABC pattern so storage backends (HCP, MinIO, Ceph, AWS) can be swapped without touching endpoint code. See [Storage Layer Architecture](storage.md) for details.

- **Sync-over-async S3**: Storage operations use synchronous boto3 calls executed via `asyncio.to_thread()`. This avoids the complexity of async S3 clients while keeping the FastAPI event loop non-blocking.

## Router Organization

The API is organized into five endpoint groups, each with distinct auth requirements:

| Group | Prefix | Auth | Examples |
|-------|--------|------|----------|
| **S3 Data-Plane** | `/api/v1/buckets`, `/objects`, `/versions`, `/multipart`, `/credentials` | JWT | Bucket CRUD, object upload/download, presigned URLs |
| **System MAPI** | `/api/v1/mapi/system/` | System admin | Tenant management, replication, erasure coding |
| **Tenant MAPI** | `/api/v1/mapi/tenants/{tenant}/` | Tenant admin/monitor/security | Users, groups, settings, chargeback |
| **Namespace MAPI** | `/api/v1/mapi/tenants/{tenant}/namespaces/` | Admin/compliance | Namespace config, compliance, protocols, CORS |
| **Query** | `/api/v1/query/` | JWT | Metadata search |
