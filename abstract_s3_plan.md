# Abstract S3 Data Plane — Refactoring Plan

Make the S3 data-plane backend-agnostic so the same API endpoints work
against HCP, MinIO, Ceph RGW, or AWS S3 with a config switch.

---

## 1  Current State

### What we have (15 operations)

| Category | Operations |
|----------|-----------|
| Bucket CRUD | `list_buckets`, `create_bucket`, `head_bucket`, `delete_bucket` |
| Object CRUD | `list_objects` (v2), `put_object`, `get_object`, `head_object`, `delete_object`, `delete_objects`, `copy_object` |
| Bucket config | `get/put_bucket_versioning`, `get/put_bucket_acl` |
| Object config | `get/put_object_acl` |
| Presigned URLs | `generate_presigned_url` (get_object / put_object) |

### HCP-specific coupling (5 points)

| # | Where | What |
|---|-------|------|
| 1 | `auth_utils.py:31-39` | Credential derivation: `access_key = base64(username)`, `secret_key = md5(password)` |
| 2 | `s3_service.py:31-41` | `_disable_region_redirector()` — boto3 crashes on HCP's non-standard redirect responses |
| 3 | `s3_service.py:193-212` | Multi-delete workaround — HCP requires Content-MD5 but boto3 sends CRC32 |
| 4 | `tenant_routing.py` | `https://{tenant}.{domain}` subdomain routing |
| 5 | `config.py:36-81` | `S3Settings` shares `hcp_username`/`hcp_password` with MAPI, derives keys via HCP convention |

---

## 2  Missing Endpoints (verified against HCP S3 docs)

### HCP S3 API — complete operation list (from `hcp_s3.md`)

**Service level:** Get service (list buckets)

**Bucket level:**
- DELETE bucket, GET bucket (list objects v1), GET bucket ACL,
  GET bucket list multipart uploads, GET bucket versioning,
  GET bucket versions, HEAD bucket, PUT bucket, PUT bucket ACL,
  PUT bucket versioning

**Object level:**
- DELETE object, DELETE multiple objects, GET object, GET object ACL,
  HEAD object, POST object (form upload), PUT object, PUT object ACL,
  PUT object copy

**Multipart upload:**
- POST initiate multipart upload, PUT upload part,
  PUT upload part copy, GET list parts,
  POST complete multipart upload, DELETE abort multipart upload

**S3 Object Lock (HCP supports all of these):**
- GetBucketObjectLockConfiguration / PutBucketObjectLockConfiguration
- GetObjectRetention / PutObjectRetention
- GetObjectLegalHold / PutObjectLegalHold

**HCP-specific headers (not standard S3 but available via x-hcp-*):**
- `x-hcp-retention` (on PUT/GET/HEAD object) — retention value
- `x-hcp-retentionhold` (on PUT/GET/HEAD object) — hold status
- `x-hcp-labelretentionhold` (on PUT object copy) — labeled holds
- `x-hcp-privileged` (on DELETE object) — privileged delete

### What HCP does NOT support at the S3 level

These are standard AWS S3 operations that have **no equivalent** in HCP S3:
- Bucket tagging (GET/PUT/DELETE)
- Object tagging (GET/PUT/DELETE)
- Bucket lifecycle (GET/PUT/DELETE)
- Bucket policy (GET/PUT/DELETE)
- Bucket encryption config (GET/PUT/DELETE)
- Bucket notification config (GET/PUT/DELETE)
- Bucket replication config (GET/PUT/DELETE) — replication exists but
  is configured at the system level, not via S3 API

### Priority of missing endpoints for our backend

| Priority | Feature | HCP | MinIO | Ceph | AWS | Notes |
|----------|---------|-----|-------|------|-----|-------|
| **P0** | Multipart upload (init/part/complete/abort/list) | Yes | Yes | Yes | Yes | Required for large files (>5 GB). Currently hidden inside boto3's `upload_fileobj`, but no browser-direct upload support. |
| **P0** | List object versions | Yes (`?versions`) | Yes | Yes | Yes | Without this, the versioning toggle is useless in the UI. |
| **P0** | Delete multiple objects | Yes (`POST /?delete`) | Yes | Yes | Yes | We have this but use single-delete loop due to HCP Content-MD5 bug. Should use native batch on non-HCP backends. |
| **P1** | S3 Object Lock config | Yes | Yes | Yes | Yes | Get/Put bucket object lock configuration. |
| **P1** | Object retention (get/put) | Yes (S3 Object Lock + x-hcp-retention) | Yes | Partial | Yes | Core compliance feature, HCP's key selling point. |
| **P1** | Legal hold (enable/disable/check) | Yes (S3 Object Lock + x-hcp-retentionhold) | Yes | Partial | Yes | Paired with retention for compliance. |
| **P2** | Object tagging | No (HCP) | Yes | Yes | Yes | Standard in MinIO/AWS/Ceph. Not available on HCP — skip in HCP adapter. |
| **P2** | Bucket tagging | No (HCP) | Yes | Yes | Yes | Same — cost allocation/organization. |
| **P2** | Bucket lifecycle | No (HCP S3) | Yes | Yes | Yes | Configured via MAPI on HCP, not S3 API. |
| **P2** | Bucket policy | No (HCP) | Yes | Yes | Yes | IAM-style access. HCP uses ACLs + MAPI permissions. |
| **P3** | Bucket encryption config | No (HCP S3) | Yes | Yes | Yes | HCP encrypts at system level. |

---

## 3  Architecture: Backend-Agnostic Storage

### 3.1  Storage Protocol

Define a Python `Protocol` that every backend must implement.
The protocol is the **union** of operations supported by at least two
backends, with optional methods for backend-specific features.

```
backend/app/services/
├── storage/
│   ├── __init__.py
│   ├── protocol.py           # StorageProtocol — the abstract interface
│   ├── errors.py             # StorageError (backend-agnostic exception)
│   ├── base_boto3.py         # GenericBoto3Storage — standard boto3, no hacks
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── hcp.py            # HcpStorage — region redirector fix, MD5 workaround,
│   │   │                     #   credential derivation, x-hcp-* retention headers
│   │   ├── minio.py          # MinioStorage — uses minio-py client
│   │   ├── ceph.py           # CephStorage — standard boto3, RGW-specific quirks
│   │   └── aws.py            # AwsStorage — standard boto3, IAM roles
│   ├── cached.py             # CachedStorage — wraps any StorageProtocol
│   └── factory.py            # create_storage(backend, settings) → StorageProtocol
├── s3_service.py             # KEPT as backward-compat alias → factory
└── cached_s3.py              # KEPT as backward-compat alias → CachedStorage
```

### 3.2  The Protocol Interface

```python
class StorageProtocol(Protocol):
    """Backend-agnostic S3-compatible storage interface."""

    # ── Bucket operations ──────────────────────────────────────
    def list_buckets(self) -> dict: ...
    def create_bucket(self, name: str) -> dict: ...
    def head_bucket(self, name: str) -> dict: ...
    def delete_bucket(self, name: str) -> dict: ...
    def get_bucket_versioning(self, bucket: str) -> dict: ...
    def put_bucket_versioning(self, bucket: str, status: str) -> dict: ...

    # ── Object operations ──────────────────────────────────────
    def list_objects(self, bucket, prefix=None, max_keys=1000,
                     continuation_token=None, delimiter=None,
                     fetch_owner=True) -> dict: ...
    def put_object(self, bucket: str, key: str, body: IO[bytes]) -> None: ...
    def get_object(self, bucket: str, key: str) -> dict: ...
    def head_object(self, bucket: str, key: str) -> dict: ...
    def delete_object(self, bucket: str, key: str) -> dict: ...
    def delete_objects(self, bucket: str, keys: list[str]) -> dict: ...
    def copy_object(self, src_bucket, src_key, dst_bucket, dst_key) -> dict: ...

    # ── Presigned URLs ─────────────────────────────────────────
    def generate_presigned_url(self, bucket, key, expires_in=3600,
                               method="get_object") -> str: ...

    # ── Object versions (P0) ──────────────────────────────────
    def list_object_versions(self, bucket, prefix=None,
                             max_keys=1000) -> dict: ...

    # ── ACLs (optional — only HCP + Ceph) ─────────────────────
    def get_bucket_acl(self, bucket: str) -> dict: ...
    def put_bucket_acl(self, bucket: str, acl: dict) -> dict: ...
    def get_object_acl(self, bucket: str, key: str) -> dict: ...
    def put_object_acl(self, bucket: str, key: str, acl: dict) -> dict: ...

    # ── Object Lock / Retention / Legal Hold (P1) ─────────────
    def get_object_lock_config(self, bucket: str) -> dict: ...
    def put_object_lock_config(self, bucket: str, config: dict) -> dict: ...
    def get_object_retention(self, bucket: str, key: str) -> dict: ...
    def put_object_retention(self, bucket: str, key: str, config: dict) -> dict: ...
    def get_object_legal_hold(self, bucket: str, key: str) -> dict: ...
    def put_object_legal_hold(self, bucket: str, key: str, enabled: bool) -> dict: ...

    # ── Tagging (P2 — not on HCP, optional) ───────────────────
    def get_object_tags(self, bucket: str, key: str) -> dict: ...
    def put_object_tags(self, bucket: str, key: str, tags: dict) -> dict: ...
    def delete_object_tags(self, bucket: str, key: str) -> dict: ...

    # ── Lifecycle (P2 — not on HCP) ──────────────────────────
    def get_bucket_lifecycle(self, bucket: str) -> dict: ...
    def put_bucket_lifecycle(self, bucket: str, config: dict) -> dict: ...
    def delete_bucket_lifecycle(self, bucket: str) -> dict: ...
```

Methods not supported by a backend raise `StorageOperationNotSupported`.
The API layer returns 501 for these.

### 3.3  Backend-Agnostic Error Handling

Replace direct `botocore.ClientError` catch in endpoints with a
backend-neutral exception:

```python
# storage/errors.py
class StorageError(Exception):
    """Raised by any storage adapter on operation failure."""
    def __init__(self, code: str, message: str, http_status: int = 502):
        self.code = code
        self.message = message
        self.http_status = http_status

class StorageOperationNotSupported(StorageError):
    """Raised when the current backend doesn't support the operation."""
    def __init__(self, operation: str, backend: str):
        super().__init__(
            "NotSupported",
            f"'{operation}' is not supported by the {backend} backend",
            501
        )
```

Each adapter catches its own library's exceptions and re-raises as
`StorageError`. The endpoint error handler in `errors.py` catches only
`StorageError` — no more `botocore` imports in endpoint code.

### 3.4  Configuration

```python
class StorageSettings(BaseSettings):
    # Which backend to use
    storage_backend: Literal["hcp", "minio", "ceph", "aws"] = "hcp"

    # Common S3 settings (all backends)
    s3_endpoint_url: str = ""
    s3_region: str = "us-east-1"
    s3_verify_ssl: bool = False

    # Direct credentials (MinIO, Ceph, AWS)
    s3_access_key: str = ""
    s3_secret_key: str = ""

    # HCP-specific (only when storage_backend=hcp)
    hcp_username: str = ""
    hcp_password: str = ""
    hcp_domain: str = ""
```

### 3.5  Credential Strategy per Backend

| Backend | Credential Source | How |
|---------|------------------|-----|
| HCP | JWT → derive | `base64(username)` / `md5(password)` from JWT claims |
| MinIO | Direct | `s3_access_key` / `s3_secret_key` from config OR per-user from JWT mapping |
| Ceph RGW | Direct or keystone | `s3_access_key` / `s3_secret_key` or keystone token |
| AWS | IAM / direct | IAM role (no explicit keys) or `s3_access_key` / `s3_secret_key` |

The dependency `get_s3_service()` becomes `get_storage_service()` and
uses a factory:

```python
async def get_storage_service(request, token) -> StorageProtocol:
    settings = get_storage_settings()
    creds = verify_token_with_credentials(token)
    return storage_factory.create(settings, creds)
```

### 3.6  What Changes per Backend

| Concern | HCP adapter | MinIO adapter | Generic boto3 (Ceph/AWS) |
|---------|-------------|---------------|--------------------------|
| Library | boto3 | minio-py | boto3 |
| Region redirector hack | Yes | N/A | No |
| Content-MD5 multi-delete | Loop individual deletes | Native batch | Native batch |
| ACL support | Full | Raise NotSupported | Full (Ceph) / Deprecated (AWS) |
| Retention | S3 Object Lock + x-hcp-* headers | S3 Object Lock | S3 Object Lock |
| Tagging | Raise NotSupported | Native | Native |
| Lifecycle | Raise NotSupported | Native | Native |
| Credential derivation | base64/md5 from username | Direct key/secret | Direct or IAM |
| Tenant routing | `{tenant}.{domain}` subdomains | Single endpoint | Account-based |

---

## 4  Implementation Phases

### Phase 1 — Extract Protocol + HCP Adapter (no behavior change)

1. Create `storage/protocol.py` with `StorageProtocol`
2. Create `storage/errors.py` with `StorageError`
3. Move current `S3Service` → `storage/adapters/hcp.py` as `HcpStorage`
4. Create `storage/factory.py` returning `HcpStorage` by default
5. Update `dependencies.py` to use factory
6. Update `errors.py` to catch `StorageError` instead of `botocore` exceptions
7. Keep `s3_service.py` as a re-export alias for backward compat
8. Update all tests — behavior unchanged, just imports

### Phase 2 — Add Missing P0 Endpoints

1. Add `list_object_versions()` to protocol + HCP adapter
2. Add `list_object_versions` endpoint + mock + tests
3. Fix `delete_objects()` to use native batch on non-HCP (prep for Phase 3)
4. Add multipart upload endpoints (init/upload-part/complete/abort/list-parts)
   - These are primarily for browser-direct upload via presigned URLs
   - The backend still uses `upload_fileobj` for server-side uploads

### Phase 3 — MinIO Adapter

1. Add `minio` to dependencies
2. Implement `MinioStorage` in `storage/adapters/minio.py`
3. Map all protocol methods to minio-py equivalents
4. Handle return type normalization (minio objects → dicts matching protocol)
5. `delete_objects` → native `remove_objects()` (no Content-MD5 issue)
6. ACL methods → raise `StorageOperationNotSupported`
7. Add MinIO config section to `StorageSettings`
8. Test with local MinIO container

### Phase 4 — Generic Boto3 Adapter (Ceph / AWS)

1. Implement `GenericBoto3Storage` — standard boto3, no HCP hacks
2. Subclass for Ceph-specific quirks if needed
3. AWS variant uses IAM credential chain
4. Tagging, lifecycle, policy — all supported natively

### Phase 5 — Add P1 Endpoints (Retention / Legal Hold)

1. Add Object Lock config endpoints (get/put)
2. Add Object Retention endpoints (get/put)
3. Add Legal Hold endpoints (enable/disable/check)
4. HCP adapter: uses S3 Object Lock API + x-hcp-* headers
5. MinIO/AWS adapter: standard S3 Object Lock API
6. Mock server + tests for all

### Phase 6 — Add P2 Features (Tagging, Lifecycle, Policy)

1. Object tagging endpoints (get/put/delete) — returns 501 on HCP
2. Bucket tagging endpoints — returns 501 on HCP
3. Bucket lifecycle endpoints — returns 501 on HCP
4. Bucket policy endpoints — returns 501 on HCP
5. Frontend handles 501 gracefully (hides UI elements for unsupported features)

---

## 5  Migration Checklist

For every phase, follow the backend change checklist:

- [ ] Backend endpoint in `app/api/v1/endpoints/`
- [ ] Protocol method in `storage/protocol.py`
- [ ] Implementation in each active adapter
- [ ] Mock server support in `mock_server/`
- [ ] Tests in `backend/tests/`
- [ ] Frontend schema types updated if response shape changes

---

## 6  Feature Support Matrix (reference)

| Operation | HCP | MinIO | Ceph RGW | AWS S3 |
|-----------|-----|-------|----------|--------|
| Bucket CRUD | Yes | Yes | Yes | Yes |
| Object CRUD | Yes | Yes | Yes | Yes |
| Multipart upload | Yes | Yes | Yes | Yes |
| Object versions list | Yes | Yes | Yes | Yes |
| Presigned URLs | Yes | Yes | Yes | Yes |
| Bucket ACL | Yes | Deprecated | Yes | Deprecated |
| Object ACL | Yes | Deprecated | Yes | Deprecated |
| Bucket versioning | Yes | Yes | Yes | Yes |
| S3 Object Lock | Yes | Yes | Yes | Yes |
| Object retention | Yes (+ x-hcp-retention) | Yes | Partial | Yes |
| Legal hold | Yes (+ x-hcp-retentionhold) | Yes | Partial | Yes |
| Labeled hold | Yes (x-hcp-labelretentionhold) | No | No | No |
| Privileged delete | Yes (x-hcp-privileged) | No | No | No |
| Object tagging | **No** | Yes | Yes | Yes |
| Bucket tagging | **No** | Yes | Yes | Yes |
| Bucket lifecycle | **No** (via MAPI only) | Yes | Yes | Yes |
| Bucket policy | **No** | Yes | Yes | Yes |
| Bucket encryption | **No** (system-level) | Yes | Yes | Yes |
| Bucket notification | **No** | Yes | Yes | Yes |
| Bucket replication | **No** (system-level) | Yes | Yes | Yes |
| Select object content | **No** | Yes | Yes | Yes |

---

## 7  Key Design Decisions

1. **Protocol returns `dict`** — matching current boto3 convention. This avoids
   rewriting all endpoint code. MinIO adapter normalizes its typed objects to
   the same dict shape.

2. **Unsupported operations return 501** — not 404. The frontend uses this to
   conditionally hide UI elements.

3. **CachedStorage wraps any adapter** — the caching layer is already
   backend-agnostic (it caches dict results keyed by operation+args).
   No per-backend cache implementations needed.

4. **ACLs kept in protocol** — even though AWS/MinIO deprecated them. HCP and
   Ceph still use them. Backends that don't support ACLs raise NotSupported.

5. **Multipart upload as presigned URL workflow** — the backend doesn't need to
   proxy multipart parts. Instead, it generates presigned URLs for each part,
   and the frontend uploads directly to the storage backend. The backend only
   handles initiate/complete/abort.

6. **HCP x-hcp-* headers abstracted** — retention/hold operations use the
   protocol's `get/put_object_retention` and `get/put_object_legal_hold`.
   The HCP adapter translates these to x-hcp-retention and x-hcp-retentionhold
   headers internally. Other adapters use standard S3 Object Lock API.
