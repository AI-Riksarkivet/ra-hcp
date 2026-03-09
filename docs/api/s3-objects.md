# S3 Objects API

Manage objects within S3-compatible buckets. All endpoints require JWT authentication.

**Base path:** `/api/v1/buckets/{bucket}/objects`

!!! tip "Interactive docs"
    For full request/response schemas and try-it-out, visit the [Swagger UI](/docs#/S3%20Objects) at `/docs`.

---

## Single-Object Endpoints

These endpoints operate on individual objects using the object key as a path parameter.

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `.../objects/{key}` | Upload an object |
| `GET` | `.../objects/{key}` | Download an object |
| `HEAD` | `.../objects/{key}` | Get object metadata |
| `DELETE` | `.../objects/{key}` | Delete an object |
| `POST` | `.../objects/{key}/copy` | Copy an object |
| `GET` | `.../objects/{key}/acl` | Get object ACL |
| `PUT` | `.../objects/{key}/acl` | Set object ACL |

!!! info "Path parameter"
    The `{key}` parameter supports full paths (e.g., `folder/subfolder/file.txt`). It captures everything after `/objects/`.

---

### Upload object

```
POST /api/v1/buckets/{bucket}/objects/{key}
```

Upload a file as a multipart form. The object key is specified in the URL path.

**Request body:** Multipart form data with a `file` field.

**Response:** `UploadObjectResponse` — `{ bucket, key, status }`

---

### Download object

```
GET /api/v1/buckets/{bucket}/objects/{key}
```

Returns the object content as a streaming response with appropriate `Content-Type` and `Content-Disposition` headers.

---

### Get object metadata

```
HEAD /api/v1/buckets/{bucket}/objects/{key}
```

**Response:** `HeadObjectResponse`

| Field | Type | Description |
|-------|------|-------------|
| `content_length` | integer | File size in bytes |
| `content_type` | string | MIME type |
| `etag` | string | Entity tag (hash) |
| `last_modified` | string | Last modification timestamp |

---

### Delete object

```
DELETE /api/v1/buckets/{bucket}/objects/{key}
```

**Response:** `ObjectMutationResponse` — `{ status, bucket, key }`

---

### Copy object

```
POST /api/v1/buckets/{bucket}/objects/{key}/copy
```

Copy an object from a source location to this destination key.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `source_bucket` | string | Yes | Source bucket name |
| `source_key` | string | Yes | Source object key |

**Response:** `ObjectMutationResponse`

---

### Get object ACL

```
GET /api/v1/buckets/{bucket}/objects/{key}/acl
```

**Response:** `AclResponse` — `{ owner, grants }`

---

### Set object ACL

```
PUT /api/v1/buckets/{bucket}/objects/{key}/acl
```

**Request body:** `AclPolicy` — `{ Owner, Grants }`

**Response:** `StatusResponse`

---

## Bulk Endpoints

These endpoints operate on multiple objects at once.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../objects` | List objects in a bucket |
| `POST` | `.../objects/delete` | Bulk delete objects |
| `POST` | `.../objects/download` | Bulk download as ZIP |
| `POST` | `.../objects/presign` | Bulk presigned URLs |

---

### List objects

```
GET /api/v1/buckets/{bucket}/objects
```

**Query parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `prefix` | string | | Filter objects by key prefix |
| `max_keys` | integer | 1000 | Maximum number of keys to return |
| `continuation_token` | string | | Token for paginating results |
| `delimiter` | string | | Group keys by delimiter (e.g., `/` for directory listing) |

**Response:** `ListObjectsResponse`

| Field | Type | Description |
|-------|------|-------------|
| `objects` | array | List of objects (`key`, `size`, `last_modified`, `etag`, `storage_class`, `owner`) |
| `common_prefixes` | array | Grouped prefixes when using delimiter |
| `is_truncated` | boolean | Whether there are more results |
| `next_continuation_token` | string | Token for the next page |
| `key_count` | integer | Number of keys returned |

---

### Bulk delete

```
POST /api/v1/buckets/{bucket}/objects/delete
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keys` | array | Yes | List of object keys to delete |

**Response:** `DeleteObjectsResponse` — `{ status, deleted, errors }`

---

### Bulk download (ZIP)

```
POST /api/v1/buckets/{bucket}/objects/download
```

Downloads multiple objects as a single ZIP archive (streaming response).

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keys` | array | Yes | List of object keys to include |

---

### Bulk presigned URLs

```
POST /api/v1/buckets/{bucket}/objects/presign
```

Generate presigned URLs for multiple objects.

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `keys` | array | Yes | List of object keys |
| `expires_in` | integer | No | URL expiration in seconds (default: 3600) |

**Response:** `BulkPresignResponse` — `{ urls: [{ key, url }], expires_in }`

---

## S3 Credentials & Presigned URLs

These endpoints are at the API root level (not scoped to a bucket).

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/v1/presign` | Generate a presigned URL |
| `GET` | `/api/v1/credentials` | Get S3 credentials |

### Generate presigned URL

```
POST /api/v1/presign
```

**Request body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `bucket` | string | Yes | Bucket name |
| `key` | string | Yes | Object key |
| `expires_in` | integer | No | Expiration in seconds |
| `method` | string | Yes | `get_object` or `put_object` |

**Response:** `PresignedUrlResponse` — `{ url, bucket, key, expires_in, method }`

### Get S3 credentials

```
GET /api/v1/credentials
```

**Response:** `S3CredentialsResponse`

| Field | Type | Description |
|-------|------|-------------|
| `access_key_id` | string | S3 access key (base64-encoded HCP username) |
| `secret_access_key` | string | S3 secret key (MD5-hashed HCP password) |
| `username` | string | HCP username |
| `tenant` | string | Tenant name |
| `endpoint_url` | string | S3 endpoint URL |

---

## Code Examples

```bash
# List objects with prefix
curl -s "http://localhost:8000/api/v1/buckets/my-bucket/objects?prefix=documents/&max_keys=50" \
  -H "Authorization: Bearer $TOKEN" | jq .

# Upload an object
curl -s -X POST \
  http://localhost:8000/api/v1/buckets/my-bucket/objects/documents/report.pdf \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/report.pdf" | jq .

# Download an object
curl -s http://localhost:8000/api/v1/buckets/my-bucket/objects/documents/report.pdf \
  -H "Authorization: Bearer $TOKEN" -o report.pdf

# Get object metadata
curl -s -I http://localhost:8000/api/v1/buckets/my-bucket/objects/documents/report.pdf \
  -H "Authorization: Bearer $TOKEN"

# Bulk delete
curl -s -X POST http://localhost:8000/api/v1/buckets/my-bucket/objects/delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"keys": ["temp/file1.txt", "temp/file2.txt"]}' | jq .

# Copy an object between buckets
curl -s -X POST \
  http://localhost:8000/api/v1/buckets/dest-bucket/objects/archive/report.pdf/copy \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"source_bucket": "source-bucket", "source_key": "documents/report.pdf"}' | jq .

# Get S3 credentials
curl -s http://localhost:8000/api/v1/credentials \
  -H "Authorization: Bearer $TOKEN" | jq .
```
