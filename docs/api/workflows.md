# API Workflows

Copy-paste-ready **curl** and **Python 3.13+ (`httpx`)** examples for the most common HCP API workflows. Every example assumes the API is running at `http://localhost:8000` -- adjust `BASE` to match your environment.

## Prerequisites

```bash
# One-off script -- uv handles the virtual environment automatically
uv run --with httpx my_script.py

# Or add httpx to an existing uv project
uv add httpx
uv run python my_script.py
```

All Python examples target **Python >= 3.13** and use **async** `httpx`. Run them with `asyncio.run()` or inside an async framework. A minimal entry point:

```python
# upload_report.py
import asyncio

async def main():
    ...  # paste any example here

asyncio.run(main())
```

```bash
uv run --python 3.13 --with httpx upload_report.py
```

---

## 1. Authentication helper

Obtain a JWT token once and reuse it for all subsequent requests.

### curl

```bash
# Variables -- set once per session
BASE="http://localhost:8000/api/v1"

# System-level login
TOKEN=$(curl -s -X POST "$BASE/auth/token" \
  -d "username=admin&password=secret" | jq -r .access_token)

# Tenant-scoped login (slash notation)
TOKEN=$(curl -s -X POST "$BASE/auth/token" \
  -d "username=dev-ai/admin&password=secret" | jq -r .access_token)

# Tenant-scoped login (explicit tenant field)
TOKEN=$(curl -s -X POST "$BASE/auth/token" \
  -d "username=admin&password=secret&tenant=dev-ai" | jq -r .access_token)

# Verify the token works
curl -s -H "Authorization: Bearer $TOKEN" "$BASE/buckets" | jq .
```

### Python

```python
import httpx

BASE = "http://localhost:8000/api/v1"

async def login(
    username: str,
    password: str,
    tenant: str | None = None,
) -> str:
    """Return a JWT access token."""
    data: dict[str, str] = {"username": username, "password": password}
    if tenant:
        data["tenant"] = tenant
    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{BASE}/auth/token", data=data)
        resp.raise_for_status()
        return resp.json()["access_token"]

def authed_client(token: str) -> httpx.AsyncClient:
    """Create a reusable client with the Authorization header."""
    return httpx.AsyncClient(
        base_url=BASE,
        headers={"Authorization": f"Bearer {token}"},
        timeout=30.0,
    )
```

!!! note "Token lifetime"
    Tokens expire after **8 hours** by default (configurable via `API_TOKEN_EXPIRE_MINUTES`). For long-running scripts, re-authenticate when you receive a `401` response.

---

## 2. Tenant provisioning

Create a tenant, add an administrator user, then create a namespace -- the typical day-one setup.

### curl

```bash
BASE="http://localhost:8000/api/v1"

# 1. Login as system admin
TOKEN=$(curl -s -X POST "$BASE/auth/token" \
  -d "username=admin&password=secret" | jq -r .access_token)
AUTH="Authorization: Bearer $TOKEN"

# 2. Create a new tenant with initial admin user
curl -s -X PUT "$BASE/mapi/tenants?username=tenantadmin&password=Ch4ng3Me!" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "research",
    "systemVisibleDescription": "Research department storage",
    "hardQuota": "500 GB",
    "softQuota": 80
  }' | jq .

# 3. Login as the new tenant admin
TENANT_TOKEN=$(curl -s -X POST "$BASE/auth/token" \
  -d "username=research/tenantadmin&password=Ch4ng3Me!" | jq -r .access_token)
TAUTH="Authorization: Bearer $TENANT_TOKEN"

# 4. Create a namespace
curl -s -X PUT "$BASE/mapi/tenants/research/namespaces" \
  -H "$TAUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "datasets",
    "description": "ML training datasets",
    "hardQuota": "200 GB",
    "softQuota": 90
  }' | jq .
```

### Python

```python
import httpx

BASE = "http://localhost:8000/api/v1"

async def provision_tenant():
    async with httpx.AsyncClient(base_url=BASE) as c:
        # Login as system admin
        resp = await c.post("/auth/token", data={"username": "admin", "password": "secret"})
        token = resp.json()["access_token"]
        c.headers["Authorization"] = f"Bearer {token}"

        # Create tenant with initial admin
        resp = await c.put(
            "/mapi/tenants",
            params={"username": "tenantadmin", "password": "Ch4ng3Me!"},
            json={
                "name": "research",
                "systemVisibleDescription": "Research department storage",
                "hardQuota": "500 GB",
                "softQuota": 80,
            },
        )
        resp.raise_for_status()
        print("Tenant created:", resp.json())

        # Login as tenant admin
        resp = await c.post(
            "/auth/token",
            data={"username": "research/tenantadmin", "password": "Ch4ng3Me!"},
        )
        tenant_token = resp.json()["access_token"]
        c.headers["Authorization"] = f"Bearer {tenant_token}"

        # Create namespace
        resp = await c.put(
            "/mapi/tenants/research/namespaces",
            json={
                "name": "datasets",
                "description": "ML training datasets",
                "hardQuota": "200 GB",
                "softQuota": 90,
            },
        )
        resp.raise_for_status()
        print("Namespace created:", resp.json())
```

---

## 3. Object lifecycle

Upload, list, download, copy, and delete objects using the S3 endpoints.

### curl

```bash
BASE="http://localhost:8000/api/v1"
TOKEN="<your-token>"
AUTH="Authorization: Bearer $TOKEN"
BUCKET="my-bucket"

# Upload a file
curl -s -X POST "$BASE/buckets/$BUCKET/objects/reports/q1.pdf" \
  -H "$AUTH" \
  -F "file=@/tmp/q1-report.pdf" | jq .

# List objects with prefix
curl -s "$BASE/buckets/$BUCKET/objects?prefix=reports/&max_keys=50" \
  -H "$AUTH" | jq .

# Download a file
curl -s "$BASE/buckets/$BUCKET/objects/reports/q1.pdf" \
  -H "$AUTH" -o q1-report.pdf

# Copy to another bucket
curl -s -X POST "$BASE/buckets/archive/objects/2025/q1.pdf/copy" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"source_bucket\": \"$BUCKET\", \"source_key\": \"reports/q1.pdf\"}" | jq .

# Delete the original
curl -s -X DELETE "$BASE/buckets/$BUCKET/objects/reports/q1.pdf" \
  -H "$AUTH" | jq .
```

### Python

```python
import httpx
from pathlib import Path

BASE = "http://localhost:8000/api/v1"

async def object_lifecycle(token: str):
    headers = {"Authorization": f"Bearer {token}"}
    bucket = "my-bucket"

    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        # Upload
        file_path = Path("/tmp/q1-report.pdf")
        with file_path.open("rb") as f:
            resp = await c.post(
                f"/buckets/{bucket}/objects/reports/q1.pdf",
                files={"file": (file_path.name, f, "application/pdf")},
            )
            resp.raise_for_status()
            print("Uploaded:", resp.json())

        # List
        resp = await c.get(
            f"/buckets/{bucket}/objects",
            params={"prefix": "reports/", "max_keys": 50},
        )
        for obj in resp.json()["objects"]:
            print(f"  {obj['key']}  ({obj['size']} bytes)")

        # Download
        resp = await c.get(f"/buckets/{bucket}/objects/reports/q1.pdf")
        Path("q1-report.pdf").write_bytes(resp.content)

        # Copy to archive bucket
        resp = await c.post(
            "/buckets/archive/objects/2025/q1.pdf/copy",
            json={"source_bucket": bucket, "source_key": "reports/q1.pdf"},
        )
        resp.raise_for_status()

        # Delete original
        resp = await c.delete(f"/buckets/{bucket}/objects/reports/q1.pdf")
        resp.raise_for_status()
        print("Deleted original")
```

---

## 4. Namespace backup / export

Export namespace configuration as a reusable template -- useful for disaster recovery or cloning environments.

### curl

```bash
BASE="http://localhost:8000/api/v1"
TOKEN="<your-token>"
AUTH="Authorization: Bearer $TOKEN"
TENANT="research"

# Export a single namespace template
curl -s "$BASE/mapi/tenants/$TENANT/namespaces/datasets/export" \
  -H "$AUTH" | jq . > datasets-template.json

# Export multiple namespaces at once
curl -s "$BASE/mapi/tenants/$TENANT/namespaces/export?names=datasets,archives" \
  -H "$AUTH" | jq . > namespace-bundle.json

# Review the template
cat datasets-template.json | jq '.name, .hardQuota, .complianceSettings'
```

### Python

```python
import httpx
import json
from pathlib import Path

BASE = "http://localhost:8000/api/v1"

async def export_namespaces(token: str, tenant: str, ns_names: list[str]):
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        if len(ns_names) == 1:
            resp = await c.get(
                f"/mapi/tenants/{tenant}/namespaces/{ns_names[0]}/export"
            )
        else:
            resp = await c.get(
                f"/mapi/tenants/{tenant}/namespaces/export",
                params={"names": ",".join(ns_names)},
            )

        resp.raise_for_status()
        template = resp.json()

        filename = f"{'-'.join(ns_names)}-template.json"
        Path(filename).write_text(json.dumps(template, indent=2))
        print(f"Exported to {filename}")
        return template
```

---

## 5. User management

Create users, assign roles, and change passwords at the tenant level.

### curl

```bash
BASE="http://localhost:8000/api/v1"
TOKEN="<your-tenant-admin-token>"
AUTH="Authorization: Bearer $TOKEN"
TENANT="research"

# Create a user with MONITOR role
curl -s -X PUT "$BASE/mapi/tenants/$TENANT/userAccounts?password=InitialP4ss!" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "analyst",
    "fullName": "Data Analyst",
    "localAuthentication": true,
    "enabled": true,
    "forcePasswordChange": true,
    "description": "Read-only monitoring account",
    "roles": {"role": ["MONITOR"]}
  }' | jq .

# List all users
curl -s "$BASE/mapi/tenants/$TENANT/userAccounts?verbose=true" \
  -H "$AUTH" | jq .

# Update user -- add COMPLIANCE role
curl -s -X POST "$BASE/mapi/tenants/$TENANT/userAccounts/analyst" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "roles": {"role": ["MONITOR", "COMPLIANCE"]}
  }' | jq .

# Change password
curl -s -X POST "$BASE/mapi/tenants/$TENANT/userAccounts/analyst/changePassword" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"newPassword": "N3wS3cure!"}' | jq .

# Delete a user
curl -s -X DELETE "$BASE/mapi/tenants/$TENANT/userAccounts/analyst" \
  -H "$AUTH" | jq .
```

### Python

```python
import httpx

BASE = "http://localhost:8000/api/v1"

async def manage_users(token: str, tenant: str):
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        # Create user
        resp = await c.put(
            f"/mapi/tenants/{tenant}/userAccounts",
            params={"password": "InitialP4ss!"},
            json={
                "username": "analyst",
                "fullName": "Data Analyst",
                "localAuthentication": True,
                "enabled": True,
                "forcePasswordChange": True,
                "description": "Read-only monitoring account",
                "roles": {"role": ["MONITOR"]},
            },
        )
        resp.raise_for_status()
        print("User created:", resp.json())

        # List users
        resp = await c.get(
            f"/mapi/tenants/{tenant}/userAccounts",
            params={"verbose": True},
        )
        for user in resp.json():
            print(f"  {user['username']} -- roles: {user.get('roles', {})}")

        # Update roles
        resp = await c.post(
            f"/mapi/tenants/{tenant}/userAccounts/analyst",
            json={"roles": {"role": ["MONITOR", "COMPLIANCE"]}},
        )
        resp.raise_for_status()

        # Change password
        resp = await c.post(
            f"/mapi/tenants/{tenant}/userAccounts/analyst/changePassword",
            json={"newPassword": "N3wS3cure!"},
        )
        resp.raise_for_status()
        print("Password changed")
```

---

## 6. Monitoring and chargeback

Fetch storage statistics and pull chargeback reports for billing or capacity planning.

### curl

```bash
BASE="http://localhost:8000/api/v1"
TOKEN="<your-monitor-token>"
AUTH="Authorization: Bearer $TOKEN"
TENANT="research"

# Tenant-level statistics
curl -s "$BASE/mapi/tenants/$TENANT/statistics" \
  -H "$AUTH" | jq .

# Namespace-level statistics
curl -s "$BASE/mapi/tenants/$TENANT/namespaces/datasets/statistics" \
  -H "$AUTH" | jq .

# Chargeback report for January 2025 (daily granularity)
curl -s "$BASE/mapi/tenants/$TENANT/chargebackReport?\
start=2025-01-01T00:00:00Z&end=2025-02-01T00:00:00Z&granularity=day" \
  -H "$AUTH" | jq .

# Namespace-level chargeback
curl -s "$BASE/mapi/tenants/$TENANT/namespaces/datasets/chargebackReport?\
start=2025-01-01T00:00:00Z&end=2025-02-01T00:00:00Z&granularity=total" \
  -H "$AUTH" | jq .
```

### Python

```python
import httpx

BASE = "http://localhost:8000/api/v1"

async def monitoring(token: str, tenant: str, namespace: str):
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        # Tenant statistics
        resp = await c.get(f"/mapi/tenants/{tenant}/statistics")
        stats = resp.json()
        print(f"Tenant storage used: {stats.get('storageCapacityUsed', 'N/A')}")
        print(f"Object count: {stats.get('objectCount', 'N/A')}")

        # Namespace statistics
        resp = await c.get(
            f"/mapi/tenants/{tenant}/namespaces/{namespace}/statistics"
        )
        ns_stats = resp.json()
        print(f"Namespace '{namespace}': {ns_stats}")

        # Chargeback report (daily for January 2025)
        resp = await c.get(
            f"/mapi/tenants/{tenant}/chargebackReport",
            params={
                "start": "2025-01-01T00:00:00Z",
                "end": "2025-02-01T00:00:00Z",
                "granularity": "day",
            },
        )
        report = resp.json()
        print(f"Chargeback entries: {len(report) if isinstance(report, list) else 'N/A'}")
        return report
```

---

## 7. Metadata query

Search objects by indexed metadata and audit operations across namespaces.

!!! note
    Metadata query endpoints use the `/api/v1/query` prefix (not `/api/v1/mapi`). The target namespace must have indexing enabled.

### curl

```bash
BASE="http://localhost:8000/api/v1"
TOKEN="<your-token>"
AUTH="Authorization: Bearer $TOKEN"
TENANT="research"

# Search for large files (>1 MB) in the datasets namespace
curl -s -X POST "$BASE/query/tenants/$TENANT/objects" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "namespace:datasets AND size:[1048576 TO *]",
    "count": 50,
    "offset": 0,
    "sort": "-changeTimeMilliseconds",
    "verbose": true,
    "objectProperties": ["urlName", "size", "contentType", "changeTimeString"]
  }' | jq .

# Search by custom metadata
curl -s -X POST "$BASE/query/tenants/$TENANT/objects" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "customMetadata.department:\"engineering\" AND contentType:application/pdf",
    "count": 100,
    "verbose": true
  }' | jq .

# Audit operations -- all deletes in the last 24 hours
curl -s -X POST "$BASE/query/tenants/$TENANT/operations" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "count": 100,
    "verbose": true,
    "systemMetadata": {
      "changeTime": {
        "start": "2025-01-01T00:00:00Z",
        "end": "2025-01-02T00:00:00Z"
      },
      "transactions": {
        "transaction": ["delete", "purge"]
      }
    }
  }' | jq .
```

### Python

```python
import httpx

BASE = "http://localhost:8000/api/v1"

async def search_objects(token: str, tenant: str):
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        # Search for large files
        resp = await c.post(
            f"/query/tenants/{tenant}/objects",
            json={
                "query": "namespace:datasets AND size:[1048576 TO *]",
                "count": 50,
                "sort": "-changeTimeMilliseconds",
                "verbose": True,
                "objectProperties": [
                    "urlName", "size", "contentType", "changeTimeString",
                ],
            },
        )
        resp.raise_for_status()
        results = resp.json()
        for obj in results.get("resultSet", []):
            print(f"  {obj.get('urlName')}  ({obj.get('size')} bytes)")

async def audit_deletes(token: str, tenant: str, start: str, end: str):
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        resp = await c.post(
            f"/query/tenants/{tenant}/operations",
            json={
                "count": 100,
                "verbose": True,
                "systemMetadata": {
                    "changeTime": {"start": start, "end": end},
                    "transactions": {"transaction": ["delete", "purge"]},
                },
            },
        )
        resp.raise_for_status()
        ops = resp.json()
        print(f"Found {len(ops.get('resultSet', []))} delete/purge operations")
        return ops
```

---

## 8. Bulk operations

Delete, presign, or download multiple objects in a single request.

### curl

```bash
BASE="http://localhost:8000/api/v1"
TOKEN="<your-token>"
AUTH="Authorization: Bearer $TOKEN"
BUCKET="my-bucket"

# Bulk delete
curl -s -X POST "$BASE/buckets/$BUCKET/objects/delete" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"keys": ["temp/file1.txt", "temp/file2.txt", "temp/file3.txt"]}' | jq .

# Bulk presigned URLs (for sharing download links)
curl -s -X POST "$BASE/buckets/$BUCKET/objects/presign" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{
    "keys": ["reports/q1.pdf", "reports/q2.pdf"],
    "expires_in": 7200
  }' | jq .

# Bulk download as ZIP
curl -s -X POST "$BASE/buckets/$BUCKET/objects/download" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d '{"keys": ["reports/q1.pdf", "reports/q2.pdf", "reports/q3.pdf"]}' \
  -o reports.zip
```

### Python

```python
import httpx
from pathlib import Path

BASE = "http://localhost:8000/api/v1"

async def bulk_operations(token: str, bucket: str):
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        # Bulk delete
        resp = await c.post(
            f"/buckets/{bucket}/objects/delete",
            json={"keys": ["temp/file1.txt", "temp/file2.txt"]},
        )
        resp.raise_for_status()
        result = resp.json()
        print(f"Deleted: {result.get('deleted', [])}")
        if result.get("errors"):
            print(f"Errors: {result['errors']}")

        # Bulk presigned URLs
        resp = await c.post(
            f"/buckets/{bucket}/objects/presign",
            json={
                "keys": ["reports/q1.pdf", "reports/q2.pdf"],
                "expires_in": 7200,
            },
        )
        resp.raise_for_status()
        for item in resp.json().get("urls", []):
            print(f"  {item['key']}: {item['url']}")

        # Bulk download as ZIP
        resp = await c.post(
            f"/buckets/{bucket}/objects/download",
            json={"keys": ["reports/q1.pdf", "reports/q2.pdf"]},
        )
        resp.raise_for_status()
        Path("reports.zip").write_bytes(resp.content)
        print("Downloaded reports.zip")
```

---

## 9. Multipart upload

Upload large files using presigned multipart upload -- the recommended approach for files >= 100 MB.

### curl

```bash
BASE="http://localhost:8000/api/v1"
TOKEN="<your-token>"
AUTH="Authorization: Bearer $TOKEN"
BUCKET="my-bucket"
KEY="large-dataset.tar.gz"
FILE="/tmp/large-dataset.tar.gz"
FILE_SIZE=$(stat -f%z "$FILE" 2>/dev/null || stat -c%s "$FILE")

# 1. Get presigned URLs
PRESIGN=$(curl -s -X POST "$BASE/buckets/$BUCKET/multipart/$KEY/presign" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"file_size\": $FILE_SIZE}")

UPLOAD_ID=$(echo "$PRESIGN" | jq -r .upload_id)
TOTAL_PARTS=$(echo "$PRESIGN" | jq -r .total_parts)
PART_SIZE=$(echo "$PRESIGN" | jq -r .part_size)

echo "Upload ID: $UPLOAD_ID, Parts: $TOTAL_PARTS, Part size: $PART_SIZE"

# 2. Upload each part directly to HCP (no auth needed -- URL is presigned)
PARTS="[]"
for i in $(seq 0 $((TOTAL_PARTS - 1))); do
  PART_NUM=$((i + 1))
  URL=$(echo "$PRESIGN" | jq -r ".urls[$i].url")
  SKIP=$((i * PART_SIZE))

  ETAG=$(dd if="$FILE" bs=$PART_SIZE skip=$i count=1 2>/dev/null | \
    curl -s -X PUT "$URL" --data-binary @- -D - -o /dev/null | \
    grep -i etag | tr -d '\r' | awk '{print $2}')

  PARTS=$(echo "$PARTS" | jq ". + [{\"PartNumber\": $PART_NUM, \"ETag\": $ETAG}]")
  echo "  Part $PART_NUM/$TOTAL_PARTS uploaded (ETag: $ETAG)"
done

# 3. Complete the upload
curl -s -X POST "$BASE/buckets/$BUCKET/multipart/$KEY/complete" \
  -H "$AUTH" \
  -H "Content-Type: application/json" \
  -d "{\"upload_id\": \"$UPLOAD_ID\", \"parts\": $PARTS}" | jq .
```

### Python

```python
import asyncio
import httpx
from pathlib import Path

BASE = "http://localhost:8000/api/v1"

async def multipart_upload(
    token: str,
    bucket: str,
    key: str,
    file_path: str,
    concurrency: int = 6,
):
    """Upload a large file using presigned multipart upload."""
    headers = {"Authorization": f"Bearer {token}"}
    path = Path(file_path)
    file_size = path.stat().st_size

    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        # 1. Get presigned URLs
        resp = await c.post(
            f"/buckets/{bucket}/multipart/{key}/presign",
            json={"file_size": file_size},
        )
        resp.raise_for_status()
        presign = resp.json()
        upload_id = presign["upload_id"]
        part_size = presign["part_size"]
        urls = presign["urls"]
        print(f"Uploading {file_size} bytes in {len(urls)} parts")

    # 2. Upload parts directly to HCP (presigned -- no auth header)
    data = path.read_bytes()
    semaphore = asyncio.Semaphore(concurrency)

    async def upload_part(part_info: dict) -> dict:
        async with semaphore:
            pn = part_info["part_number"]
            url = part_info["url"]
            start = (pn - 1) * part_size
            end = min(start + part_size, file_size)
            chunk = data[start:end]

            async with httpx.AsyncClient() as hcp:
                resp = await hcp.put(url, content=chunk)
                resp.raise_for_status()
                etag = resp.headers["etag"]
                print(f"  Part {pn}/{len(urls)} uploaded")
                return {"PartNumber": pn, "ETag": etag}

    parts = await asyncio.gather(*[upload_part(u) for u in urls])
    parts = sorted(parts, key=lambda p: p["PartNumber"])

    # 3. Complete the upload
    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        resp = await c.post(
            f"/buckets/{bucket}/multipart/{key}/complete",
            json={"upload_id": upload_id, "parts": parts},
        )
        resp.raise_for_status()
        print("Upload complete:", resp.json())
```

!!! warning "CORS required for browser uploads"
    If calling presigned URLs from a browser, the target HCP namespace must have CORS configured to allow `PUT` requests and expose the `ETag` header. See [S3 Objects -- CORS Configuration](s3-objects.md#cors-configuration-for-presigned-uploads) for details.

---

## 10. Argo Workflows with HCP S3

[Argo Workflows](https://argoproj.github.io/workflows/) can use HCP as an S3-compatible artifact store. This enables pipelines to read input data from and write results back to HCP namespaces. The examples below show how to configure Argo to work with the HCP API's S3 credentials endpoint and presigned URLs.

### Configuring HCP S3 credentials for Argo

First, retrieve the S3 credentials from the API and create a Kubernetes Secret that Argo can reference:

```bash
BASE="http://localhost:8000/api/v1"
TOKEN="<your-token>"

# Fetch S3 credentials from the HCP API
CREDS=$(curl -s "$BASE/credentials" -H "Authorization: Bearer $TOKEN")

ACCESS_KEY=$(echo "$CREDS" | jq -r .access_key_id)
SECRET_KEY=$(echo "$CREDS" | jq -r .secret_access_key)
ENDPOINT=$(echo "$CREDS" | jq -r .endpoint_url)

# Create Kubernetes Secret for Argo
kubectl create secret generic hcp-s3-credentials \
  --from-literal=accessKey="$ACCESS_KEY" \
  --from-literal=secretKey="$SECRET_KEY" \
  -n argo
```

Or automate it with Python:

```python
import httpx
import subprocess

BASE = "http://localhost:8000/api/v1"

async def create_argo_s3_secret(token: str, namespace: str = "argo"):
    """Fetch HCP S3 credentials and create a Kubernetes Secret for Argo."""
    headers = {"Authorization": f"Bearer {token}"}

    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        resp = await c.get("/credentials")
        resp.raise_for_status()
        creds = resp.json()

    subprocess.run(
        [
            "kubectl", "create", "secret", "generic", "hcp-s3-credentials",
            f"--from-literal=accessKey={creds['access_key_id']}",
            f"--from-literal=secretKey={creds['secret_access_key']}",
            "-n", namespace,
            "--dry-run=client", "-o", "yaml",
        ],
        check=True,
    )
```

### Argo Workflow with HCP S3 artifacts

A workflow that reads a dataset from HCP, processes it, and writes results back:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hcp-etl-
spec:
  entrypoint: etl-pipeline
  artifactGC:
    strategy: OnWorkflowDeletion
  templates:
    - name: etl-pipeline
      dag:
        tasks:
          - name: extract
            template: extract-data
          - name: transform
            template: transform-data
            dependencies: [extract]
          - name: load
            template: load-results
            dependencies: [transform]

    - name: extract-data
      container:
        image: python:3.13-slim
        command: [python, -c]
        args:
          - |
            from pathlib import Path
            import json
            # Read the input artifact (mounted by Argo from HCP S3)
            data = json.loads(Path("/tmp/input/manifest.json").read_text())
            print(f"Loaded {len(data['files'])} files from manifest")
            # Write output for next step
            Path("/tmp/output/extracted.json").write_text(json.dumps(data))
      inputs:
        artifacts:
          - name: input-manifest
            path: /tmp/input/manifest.json
            s3:
              endpoint: hcp-s3.example.com
              bucket: datasets
              key: manifests/latest.json
              accessKeySecret:
                name: hcp-s3-credentials
                key: accessKey
              secretKeySecret:
                name: hcp-s3-credentials
                key: secretKey
              insecure: false
      outputs:
        artifacts:
          - name: extracted
            path: /tmp/output/extracted.json

    - name: transform-data
      container:
        image: python:3.13-slim
        command: [python, -c]
        args:
          - |
            from pathlib import Path
            import json
            data = json.loads(Path("/tmp/input/extracted.json").read_text())
            results = {"processed": len(data.get("files", [])), "status": "ok"}
            Path("/tmp/output/results.json").write_text(json.dumps(results))
      inputs:
        artifacts:
          - name: extracted
            path: /tmp/input/extracted.json
      outputs:
        artifacts:
          - name: results
            path: /tmp/output/results.json

    - name: load-results
      container:
        image: python:3.13-slim
        command: [python, -c]
        args:
          - |
            from pathlib import Path
            data = Path("/tmp/input/results.json").read_text()
            print(f"Results uploaded to HCP: {data}")
      inputs:
        artifacts:
          - name: results
            path: /tmp/input/results.json
      outputs:
        artifacts:
          - name: final-results
            path: /tmp/input/results.json
            s3:
              endpoint: hcp-s3.example.com
              bucket: results
              key: "etl/{{workflow.name}}/results.json"
              accessKeySecret:
                name: hcp-s3-credentials
                key: accessKey
              secretKeySecret:
                name: hcp-s3-credentials
                key: secretKey
```

### Argo with presigned URLs (sidecar-free)

For cases where you cannot mount S3 credentials into every pod, use the HCP API to generate presigned URLs and pass them as parameters:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hcp-presign-
spec:
  entrypoint: presigned-pipeline
  arguments:
    parameters:
      - name: hcp-api-base
        value: "http://hcp-api.default.svc:8000/api/v1"
      - name: hcp-token
        value: "<your-token>"
      - name: bucket
        value: "datasets"
  templates:
    - name: presigned-pipeline
      steps:
        - - name: generate-urls
            template: presign
        - - name: process
            template: process-with-urls
            arguments:
              parameters:
                - name: download-url
                  value: "{{steps.generate-urls.outputs.parameters.download-url}}"
                - name: upload-url
                  value: "{{steps.generate-urls.outputs.parameters.upload-url}}"

    - name: presign
      script:
        image: curlimages/curl:latest
        command: [sh]
        source: |
          BASE="{{workflow.parameters.hcp-api-base}}"
          TOKEN="{{workflow.parameters.hcp-token}}"
          BUCKET="{{workflow.parameters.bucket}}"

          # Get download URL for input
          DL=$(curl -s -X POST "$BASE/presign" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"bucket\":\"$BUCKET\",\"key\":\"input/data.csv\",\"method\":\"get_object\",\"expires_in\":3600}")
          echo "$DL" | grep -o '"url":"[^"]*"' | cut -d'"' -f4 > /tmp/download-url

          # Get upload URL for output
          UL=$(curl -s -X POST "$BASE/presign" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"bucket\":\"$BUCKET\",\"key\":\"output/result.csv\",\"method\":\"put_object\",\"expires_in\":3600}")
          echo "$UL" | grep -o '"url":"[^"]*"' | cut -d'"' -f4 > /tmp/upload-url
      outputs:
        parameters:
          - name: download-url
            valueFrom:
              path: /tmp/download-url
          - name: upload-url
            valueFrom:
              path: /tmp/upload-url

    - name: process-with-urls
      inputs:
        parameters:
          - name: download-url
          - name: upload-url
      container:
        image: python:3.13-slim
        command: [python, -c]
        args:
          - |
            import urllib.request
            # Download input via presigned URL (no credentials needed)
            urllib.request.urlretrieve("{{inputs.parameters.download-url}}", "/tmp/data.csv")
            # Process...
            with open("/tmp/result.csv", "w") as f:
                f.write("processed,data\n")
            # Upload result via presigned URL
            with open("/tmp/result.csv", "rb") as f:
                req = urllib.request.Request(
                    "{{inputs.parameters.upload-url}}", data=f.read(), method="PUT"
                )
                urllib.request.urlopen(req)
            print("Done: input downloaded and result uploaded via presigned URLs")
```

### Hera — Python SDK for Argo Workflows

[Hera](https://github.com/argoproj-labs/hera) lets you define Argo Workflows entirely in Python instead of YAML. Install it with:

```bash
uv add hera
```

#### ETL pipeline with HCP S3 artifacts (Hera)

This is the Python equivalent of the YAML DAG above:

```python
from hera.workflows import (
    DAG,
    Artifact,
    S3Artifact,
    Workflow,
    models as m,
    script,
)

HCP_S3 = m.S3Artifact(
    endpoint="hcp-s3.example.com",
    bucket="datasets",
    access_key_secret=m.SecretKeySelector(name="hcp-s3-credentials", key="accessKey"),
    secret_key_secret=m.SecretKeySelector(name="hcp-s3-credentials", key="secretKey"),
    insecure=False,
)


@script(image="python:3.13-slim")
def extract_data(manifest: Artifact) -> Artifact:
    """Read input from HCP S3, write extracted data."""
    from pathlib import Path
    import json

    data = json.loads(Path("/tmp/input/manifest.json").read_text())
    print(f"Loaded {len(data['files'])} files from manifest")
    Path("/tmp/output/extracted.json").write_text(json.dumps(data))


@script(image="python:3.13-slim")
def transform_data(extracted: Artifact) -> Artifact:
    """Process the extracted data."""
    from pathlib import Path
    import json

    data = json.loads(Path("/tmp/input/extracted.json").read_text())
    results = {"processed": len(data.get("files", [])), "status": "ok"}
    Path("/tmp/output/results.json").write_text(json.dumps(results))


@script(image="python:3.13-slim")
def load_results(results: Artifact) -> Artifact:
    """Upload results back to HCP S3."""
    from pathlib import Path

    data = Path("/tmp/input/results.json").read_text()
    print(f"Results uploaded to HCP: {data}")


with Workflow(
    generate_name="hcp-etl-",
    entrypoint="etl-pipeline",
    artifact_gc=m.ArtifactGC(strategy="OnWorkflowDeletion"),
) as w:
    with DAG(name="etl-pipeline"):
        ext = extract_data(
            name="extract",
            arguments=[
                S3Artifact(
                    name="manifest",
                    path="/tmp/input/manifest.json",
                    **HCP_S3.dict() | {"key": "manifests/latest.json"},
                ),
            ],
        )
        trn = transform_data(
            name="transform",
            arguments=[ext.get_artifact("extracted").with_name("extracted")],
        )
        ld = load_results(
            name="load",
            arguments=[trn.get_artifact("results").with_name("results")],
        )
        ext >> trn >> ld

w.create()  # submit to the Argo server
```

#### Presigned URL pipeline (Hera)

A Steps-based workflow using the HCP API to generate presigned URLs:

```python
from hera.workflows import (
    Parameter,
    Steps,
    Workflow,
    script,
)

HCP_BASE = "http://hcp-api.default.svc:8000/api/v1"


@script(image="curlimages/curl:latest")
def generate_presigned_urls(
    hcp_api_base: str,
    hcp_token: str,
    bucket: str,
):
    """Generate download and upload presigned URLs from the HCP API."""
    import subprocess, json

    def presign(key: str, method: str) -> str:
        result = subprocess.run(
            [
                "curl", "-s", "-X", "POST", f"{hcp_api_base}/presign",
                "-H", f"Authorization: Bearer {hcp_token}",
                "-H", "Content-Type: application/json",
                "-d", json.dumps({
                    "bucket": bucket, "key": key,
                    "method": method, "expires_in": 3600,
                }),
            ],
            capture_output=True, text=True, check=True,
        )
        return json.loads(result.stdout)["url"]

    dl = presign("input/data.csv", "get_object")
    ul = presign("output/result.csv", "put_object")

    # Write outputs for Argo parameter extraction
    from pathlib import Path
    Path("/tmp/download-url").write_text(dl)
    Path("/tmp/upload-url").write_text(ul)


@script(image="python:3.13-slim")
def process_with_urls(download_url: str, upload_url: str):
    """Download input, process, and upload result via presigned URLs."""
    import urllib.request

    urllib.request.urlretrieve(download_url, "/tmp/data.csv")

    with open("/tmp/result.csv", "w") as f:
        f.write("processed,data\n")

    with open("/tmp/result.csv", "rb") as f:
        req = urllib.request.Request(upload_url, data=f.read(), method="PUT")
        urllib.request.urlopen(req)

    print("Done: input downloaded and result uploaded via presigned URLs")


with Workflow(
    generate_name="hcp-presign-",
    entrypoint="presigned-pipeline",
    arguments=[
        Parameter(name="hcp-api-base", value=HCP_BASE),
        Parameter(name="hcp-token", value="<your-token>"),
        Parameter(name="bucket", value="datasets"),
    ],
) as w:
    with Steps(name="presigned-pipeline"):
        urls = generate_presigned_urls(
            name="generate-urls",
            arguments={
                "hcp_api_base": "{{workflow.parameters.hcp-api-base}}",
                "hcp_token": "{{workflow.parameters.hcp-token}}",
                "bucket": "{{workflow.parameters.bucket}}",
            },
        )
        process_with_urls(
            name="process",
            arguments={
                "download_url": urls.get_parameter("download-url"),
                "upload_url": urls.get_parameter("upload-url"),
            },
        )

w.create()
```

#### Running Hera workflows

```bash
# Submit directly from a script
uv run --with hera python etl_workflow.py

# Or export to YAML and submit with Argo CLI
uv run --with hera python -c "
from etl_workflow import w
print(w.to_yaml())
" | argo submit -

# Useful during development: validate without submitting
uv run --with hera python -c "
from etl_workflow import w
print(w.to_yaml())
" | argo lint -
```

### Batch processing — fan-out over HCP objects

A common pattern: list objects from an HCP bucket, process each one in parallel (fan-out), then aggregate results (fan-in).

#### Batch processing (YAML)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hcp-batch-
spec:
  entrypoint: batch-pipeline
  arguments:
    parameters:
      - name: hcp-api-base
        value: "http://hcp-api.default.svc:8000/api/v1"
      - name: hcp-token
        value: "<your-token>"
      - name: bucket
        value: "datasets"
      - name: prefix
        value: "incoming/"
  templates:
    # ── Orchestrator DAG ─────────────────────────────────────────
    - name: batch-pipeline
      dag:
        tasks:
          - name: discover
            template: list-objects
          - name: process
            template: fan-out
            dependencies: [discover]
            arguments:
              parameters:
                - name: object-keys
                  value: "{{tasks.discover.outputs.parameters.keys}}"
          - name: summarize
            template: aggregate
            dependencies: [process]

    # ── Step 1: List objects from HCP via the API ────────────────
    - name: list-objects
      retryStrategy:
        limit: 3
        backoff:
          duration: "5s"
          factor: 2
      script:
        image: curlimages/curl:latest
        command: [sh]
        source: |
          BASE="{{workflow.parameters.hcp-api-base}}"
          TOKEN="{{workflow.parameters.hcp-token}}"
          BUCKET="{{workflow.parameters.bucket}}"
          PREFIX="{{workflow.parameters.prefix}}"

          RESP=$(curl -s -f "$BASE/s3/buckets/$BUCKET/objects?prefix=$PREFIX&max_keys=100" \
            -H "Authorization: Bearer $TOKEN")

          # Extract object keys as a JSON array
          echo "$RESP" | jq '[.objects[].key]' > /tmp/keys.json
          echo "Found $(echo "$RESP" | jq '.objects | length') objects"
          cat /tmp/keys.json
      outputs:
        parameters:
          - name: keys
            valueFrom:
              path: /tmp/keys.json

    # ── Step 2: Fan out — one pod per object ─────────────────────
    - name: fan-out
      inputs:
        parameters:
          - name: object-keys
      steps:
        - - name: process-object
            template: process-single
            arguments:
              parameters:
                - name: key
                  value: "{{item}}"
            withParam: "{{inputs.parameters.object-keys}}"

    - name: process-single
      retryStrategy:
        limit: 2
        backoff:
          duration: "10s"
          factor: 2
      inputs:
        parameters:
          - name: key
      script:
        image: python:3.13-slim
        command: [python]
        source: |
          import urllib.request, json

          BASE = "{{workflow.parameters.hcp-api-base}}"
          TOKEN = "{{workflow.parameters.hcp-token}}"
          BUCKET = "{{workflow.parameters.bucket}}"
          KEY = "{{inputs.parameters.key}}"

          # Get a presigned download URL from the HCP API
          req = urllib.request.Request(
              f"{BASE}/s3/presign",
              data=json.dumps({
                  "bucket": BUCKET, "key": KEY,
                  "method": "get_object", "expires_in": 600,
              }).encode(),
              headers={
                  "Authorization": f"Bearer {TOKEN}",
                  "Content-Type": "application/json",
              },
          )
          url = json.loads(urllib.request.urlopen(req).read())["url"]

          # Download and process the object
          local_path = "/tmp/data"
          urllib.request.urlretrieve(url, local_path)
          import os
          size = os.path.getsize(local_path)
          result = {"key": KEY, "size": size, "status": "processed"}
          print(json.dumps(result))

          # Upload result back via presigned PUT
          result_key = KEY.replace("incoming/", "processed/") + ".result.json"
          req = urllib.request.Request(
              f"{BASE}/s3/presign",
              data=json.dumps({
                  "bucket": BUCKET, "key": result_key,
                  "method": "put_object", "expires_in": 600,
              }).encode(),
              headers={
                  "Authorization": f"Bearer {TOKEN}",
                  "Content-Type": "application/json",
              },
          )
          upload_url = json.loads(urllib.request.urlopen(req).read())["url"]
          req = urllib.request.Request(
              upload_url,
              data=json.dumps(result).encode(),
              method="PUT",
          )
          urllib.request.urlopen(req)
          print(f"Result uploaded to {result_key}")

    # ── Step 3: Fan in — aggregate results ───────────────────────
    - name: aggregate
      retryStrategy:
        limit: 2
      script:
        image: curlimages/curl:latest
        command: [sh]
        source: |
          BASE="{{workflow.parameters.hcp-api-base}}"
          TOKEN="{{workflow.parameters.hcp-token}}"
          BUCKET="{{workflow.parameters.bucket}}"

          # List all processed results
          RESULTS=$(curl -s -f "$BASE/s3/buckets/$BUCKET/objects?prefix=processed/&max_keys=1000" \
            -H "Authorization: Bearer $TOKEN")

          COUNT=$(echo "$RESULTS" | jq '.objects | length')
          SUMMARY="{\"workflow\":\"{{workflow.name}}\",\"objects_processed\":$COUNT,\"status\":\"complete\"}"
          echo "$SUMMARY"

          # Upload summary via presigned URL
          PRESIGN=$(curl -s -X POST "$BASE/s3/presign" \
            -H "Authorization: Bearer $TOKEN" \
            -H "Content-Type: application/json" \
            -d "{\"bucket\":\"$BUCKET\",\"key\":\"summaries/{{workflow.name}}.json\",\"method\":\"put_object\",\"expires_in\":600}")
          UPLOAD_URL=$(echo "$PRESIGN" | jq -r '.url')
          curl -s -X PUT "$UPLOAD_URL" -d "$SUMMARY"
          echo "Summary uploaded"
```

#### Batch processing (Hera)

```python
from hera.workflows import (
    DAG,
    Parameter,
    Steps,
    Workflow,
    models as m,
    script,
)

HCP_BASE = "http://hcp-api.default.svc:8000/api/v1"

RETRY = m.RetryStrategy(
    limit="3",
    backoff=m.Backoff(duration="5s", factor=2),
)


@script(image="curlimages/curl:latest", retry_strategy=RETRY)
def list_objects(hcp_api_base: str, hcp_token: str, bucket: str, prefix: str):
    """List objects from HCP and output their keys as a JSON array."""
    import subprocess, json

    result = subprocess.run(
        [
            "curl", "-s", "-f",
            f"{hcp_api_base}/s3/buckets/{bucket}/objects?prefix={prefix}&max_keys=100",
            "-H", f"Authorization: Bearer {hcp_token}",
        ],
        capture_output=True, text=True, check=True,
    )
    objects = json.loads(result.stdout)["objects"]
    keys = [obj["key"] for obj in objects]
    print(f"Found {len(keys)} objects")

    from pathlib import Path
    Path("/tmp/keys.json").write_text(json.dumps(keys))


@script(
    image="python:3.13-slim",
    retry_strategy=m.RetryStrategy(limit="2", backoff=m.Backoff(duration="10s", factor=2)),
)
def process_single(hcp_api_base: str, hcp_token: str, bucket: str, key: str):
    """Download an object via presigned URL, process it, upload the result."""
    import urllib.request, json, os

    # Presign download
    req = urllib.request.Request(
        f"{hcp_api_base}/s3/presign",
        data=json.dumps({
            "bucket": bucket, "key": key,
            "method": "get_object", "expires_in": 600,
        }).encode(),
        headers={
            "Authorization": f"Bearer {hcp_token}",
            "Content-Type": "application/json",
        },
    )
    url = json.loads(urllib.request.urlopen(req).read())["url"]

    # Download and process
    urllib.request.urlretrieve(url, "/tmp/data")
    size = os.path.getsize("/tmp/data")
    result = {"key": key, "size": size, "status": "processed"}
    print(json.dumps(result))

    # Presign upload and write result
    result_key = key.replace("incoming/", "processed/") + ".result.json"
    req = urllib.request.Request(
        f"{hcp_api_base}/s3/presign",
        data=json.dumps({
            "bucket": bucket, "key": result_key,
            "method": "put_object", "expires_in": 600,
        }).encode(),
        headers={
            "Authorization": f"Bearer {hcp_token}",
            "Content-Type": "application/json",
        },
    )
    upload_url = json.loads(urllib.request.urlopen(req).read())["url"]
    req = urllib.request.Request(upload_url, data=json.dumps(result).encode(), method="PUT")
    urllib.request.urlopen(req)
    print(f"Result uploaded to {result_key}")


@script(image="curlimages/curl:latest", retry_strategy=RETRY)
def aggregate(hcp_api_base: str, hcp_token: str, bucket: str):
    """List processed results and upload a summary."""
    import subprocess, json

    result = subprocess.run(
        [
            "curl", "-s", "-f",
            f"{hcp_api_base}/s3/buckets/{bucket}/objects?prefix=processed/&max_keys=1000",
            "-H", f"Authorization: Bearer {hcp_token}",
        ],
        capture_output=True, text=True, check=True,
    )
    count = len(json.loads(result.stdout)["objects"])
    summary = json.dumps({"objects_processed": count, "status": "complete"})
    print(summary)

    # Upload summary via presigned URL
    presign = subprocess.run(
        [
            "curl", "-s", "-X", "POST", f"{hcp_api_base}/s3/presign",
            "-H", f"Authorization: Bearer {hcp_token}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "bucket": bucket,
                "key": "summaries/batch-result.json",
                "method": "put_object", "expires_in": 600,
            }),
        ],
        capture_output=True, text=True, check=True,
    )
    upload_url = json.loads(presign.stdout)["url"]
    subprocess.run(["curl", "-s", "-X", "PUT", upload_url, "-d", summary], check=True)


WF_PARAMS = {
    "hcp_api_base": "{{workflow.parameters.hcp-api-base}}",
    "hcp_token": "{{workflow.parameters.hcp-token}}",
    "bucket": "{{workflow.parameters.bucket}}",
}

with Workflow(
    generate_name="hcp-batch-",
    entrypoint="batch-pipeline",
    arguments=[
        Parameter(name="hcp-api-base", value=HCP_BASE),
        Parameter(name="hcp-token", value="<your-token>"),
        Parameter(name="bucket", value="datasets"),
        Parameter(name="prefix", value="incoming/"),
    ],
) as w:
    with DAG(name="batch-pipeline"):
        # Step 1: Discover objects
        disc = list_objects(
            name="discover",
            arguments={**WF_PARAMS, "prefix": "{{workflow.parameters.prefix}}"},
        )
        # Step 2: Fan out — process each object in parallel
        with Steps(name="fan-out") as fan:
            process_single(
                name="process-object",
                arguments={
                    **WF_PARAMS,
                    "key": "{{item}}",
                },
                with_param=disc.get_parameter("keys"),
            )
        # Step 3: Aggregate results
        agg = aggregate(name="summarize", arguments=WF_PARAMS)

        disc >> fan >> agg

w.create()
```

!!! tip "Which approach to use?"
    - **S3 artifacts** (YAML or Hera DAG): Best when Argo has direct network access to HCP S3. Argo handles download/upload automatically. Requires the S3 credentials Secret.
    - **Presigned URLs** (YAML or Hera Steps): Best when pods cannot reach HCP directly or you want to avoid distributing S3 credentials. The HCP API generates short-lived URLs that anyone can use.
    - **Batch fan-out**: Use `withParam` (YAML) or `with_param` (Hera) to process N objects in parallel. Argo handles scheduling and concurrency limits.
    - **YAML vs Hera**: Use YAML for simple workflows or when non-Python teams maintain them. Use Hera when you want type safety, IDE autocompletion, and Python-native DAG composition (`>>` operator).

---

## 11. Error handling, retries, and idempotency

Production scripts need to handle transient failures, token expiry, and partial-success scenarios. HCP's S3 layer is **eventually consistent** for certain operations -- the patterns below help build resilient automation.

### Retry with exponential backoff

```python
import asyncio
import httpx
from collections.abc import Callable
from typing import Any

RETRYABLE_STATUS = {408, 429, 500, 502, 503, 504}

async def retry(
    fn: Callable[..., Any],
    *args: Any,
    max_attempts: int = 4,
    base_delay: float = 1.0,
    **kwargs: Any,
) -> Any:
    """Retry an async function with exponential backoff.

    Retries on network errors and retryable HTTP status codes.
    """
    last_exc: Exception | None = None
    for attempt in range(max_attempts):
        try:
            return await fn(*args, **kwargs)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code not in RETRYABLE_STATUS:
                raise  # 400, 401, 403, 404, 409 -- don't retry
            last_exc = exc
        except (httpx.ConnectError, httpx.ReadTimeout, httpx.WriteTimeout) as exc:
            last_exc = exc

        delay = base_delay * (2 ** attempt)
        print(f"  Attempt {attempt + 1} failed, retrying in {delay:.1f}s...")
        await asyncio.sleep(delay)

    raise RuntimeError(f"All {max_attempts} attempts failed") from last_exc
```

### Auto-refreshing auth wrapper

```python
import httpx
from dataclasses import dataclass, field

BASE = "http://localhost:8000/api/v1"

@dataclass
class HCPClient:
    """HTTP client that re-authenticates on 401."""

    username: str
    password: str
    tenant: str | None = None
    _token: str = field(default="", init=False, repr=False)
    _client: httpx.AsyncClient = field(init=False, repr=False)

    async def __aenter__(self):
        self._client = httpx.AsyncClient(base_url=BASE, timeout=30.0)
        await self._login()
        return self

    async def __aexit__(self, *exc: object):
        await self._client.aclose()

    async def _login(self):
        data: dict[str, str] = {
            "username": self.username,
            "password": self.password,
        }
        if self.tenant:
            data["tenant"] = self.tenant
        resp = await self._client.post("/auth/token", data=data)
        resp.raise_for_status()
        self._token = resp.json()["access_token"]
        self._client.headers["Authorization"] = f"Bearer {self._token}"

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        """Make a request, re-authenticate once on 401."""
        resp = await self._client.request(method, url, **kwargs)
        if resp.status_code == 401:
            await self._login()
            resp = await self._client.request(method, url, **kwargs)
        return resp
```

Usage:

```python
async def main():
    async with HCPClient("admin", "secret", tenant="research") as hcp:
        resp = await hcp.request("GET", "/mapi/tenants/research/statistics")
        print(resp.json())
```

### curl error handling

```bash
# Reusable function with status-code checking
hcp_request() {
  local METHOD="$1" URL="$2"; shift 2
  local RESP
  RESP=$(curl -s -w "\n%{http_code}" -X "$METHOD" "$URL" \
    -H "Authorization: Bearer $TOKEN" "$@")
  local BODY=$(echo "$RESP" | sed '$d')
  local CODE=$(echo "$RESP" | tail -1)

  case "$CODE" in
    2[0-9][0-9]) echo "$BODY" | jq . ;;
    401) echo "ERROR: Token expired -- re-authenticate" >&2; return 1 ;;
    404) echo "ERROR: Not found -- $URL" >&2; return 1 ;;
    409) echo "ERROR: Conflict -- resource already exists" >&2; return 1 ;;
    429|5[0-9][0-9])
      echo "WARN: Retryable error $CODE, waiting 5s..." >&2
      sleep 5
      hcp_request "$METHOD" "$URL" "$@"  # retry once
      ;;
    *) echo "ERROR $CODE: $BODY" >&2; return 1 ;;
  esac
}

# Usage
hcp_request GET "$BASE/mapi/tenants/research/statistics"
hcp_request PUT "$BASE/mapi/tenants/research/namespaces" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-ns", "hardQuota": "10 GB"}'
```

### Idempotent operations

Many HCP API operations are naturally idempotent. Knowing which ones are safe to retry avoids duplicate side-effects:

| Operation | Idempotent? | Notes |
|-----------|:-----------:|-------|
| `GET` / `HEAD` any endpoint | Yes | Read-only, always safe to retry |
| `PUT` create tenant/namespace | Yes | Returns `409 Conflict` if already exists -- check and continue |
| `PUT` create user | Yes | Same -- `409` means user already exists |
| `POST` upload object (same key) | Yes | Overwrites existing object with same key |
| `DELETE` object/user/namespace | Yes | Second delete returns `404` -- treat as success |
| `POST` update settings | Yes | Applies the same state, no cumulative effect |
| `POST` change password | **No** | Repeated calls succeed but generate audit events |
| `PUT` multipart presign | **No** | Each call creates a new upload ID |

### Safe "create-if-not-exists" pattern

```python
import httpx

async def ensure_namespace(
    client: httpx.AsyncClient,
    tenant: str,
    name: str,
    hard_quota: str = "100 GB",
) -> dict:
    """Create a namespace, or return the existing one."""
    # Try to create
    resp = await client.put(
        f"/mapi/tenants/{tenant}/namespaces",
        json={"name": name, "hardQuota": hard_quota},
    )
    match resp.status_code:
        case 201 | 200:
            print(f"Created namespace '{name}'")
            return resp.json()
        case 409:
            # Already exists -- fetch and return it
            resp = await client.get(
                f"/mapi/tenants/{tenant}/namespaces/{name}",
                params={"verbose": True},
            )
            resp.raise_for_status()
            print(f"Namespace '{name}' already exists")
            return resp.json()
        case _:
            resp.raise_for_status()  # raises for unexpected errors
            return {}  # unreachable, satisfies type checker
```

```bash
# Bash equivalent -- create-if-not-exists
CODE=$(curl -s -o /dev/null -w "%{http_code}" -X PUT \
  "$BASE/mapi/tenants/$TENANT/namespaces" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"name\": \"$NS\", \"hardQuota\": \"100 GB\"}")

if [ "$CODE" = "201" ] || [ "$CODE" = "200" ]; then
  echo "Created namespace $NS"
elif [ "$CODE" = "409" ]; then
  echo "Namespace $NS already exists (OK)"
else
  echo "Failed to create namespace: HTTP $CODE" >&2
  exit 1
fi
```

### Multipart upload with fault tolerance

Presigned multipart upload can resume after partial failures. If some parts fail, re-upload only the missing ones:

```python
import asyncio
import httpx
from pathlib import Path

BASE = "http://localhost:8000/api/v1"

async def resilient_multipart_upload(
    token: str,
    bucket: str,
    key: str,
    file_path: str,
    concurrency: int = 6,
    part_retries: int = 3,
):
    """Multipart upload that retries individual failed parts."""
    headers = {"Authorization": f"Bearer {token}"}
    path = Path(file_path)
    file_size = path.stat().st_size

    # 1. Initiate
    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        resp = await c.post(
            f"/buckets/{bucket}/multipart/{key}/presign",
            json={"file_size": file_size},
        )
        resp.raise_for_status()
        presign = resp.json()

    upload_id = presign["upload_id"]
    part_size = presign["part_size"]
    data = path.read_bytes()
    semaphore = asyncio.Semaphore(concurrency)
    completed: dict[int, dict] = {}
    failed: list[int] = []

    async def upload_part(part_info: dict) -> None:
        pn = part_info["part_number"]
        url = part_info["url"]
        start = (pn - 1) * part_size
        end = min(start + part_size, file_size)
        chunk = data[start:end]

        async with semaphore:
            for attempt in range(part_retries):
                try:
                    async with httpx.AsyncClient(timeout=120.0) as hcp:
                        resp = await hcp.put(url, content=chunk)
                        resp.raise_for_status()
                        completed[pn] = {
                            "PartNumber": pn,
                            "ETag": resp.headers["etag"],
                        }
                        print(f"  Part {pn}/{len(presign['urls'])} OK")
                        return
                except (httpx.HTTPError, httpx.StreamError):
                    delay = 2.0 ** attempt
                    print(f"  Part {pn} attempt {attempt + 1} failed, retry in {delay}s")
                    await asyncio.sleep(delay)
            failed.append(pn)

    # 2. Upload all parts with per-part retries
    await asyncio.gather(*[upload_part(u) for u in presign["urls"]])

    if failed:
        # Abort the upload -- caller can retry the whole thing
        async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
            await c.post(
                f"/buckets/{bucket}/multipart/{key}/abort",
                json={"upload_id": upload_id},
            )
        raise RuntimeError(f"Parts {failed} failed after {part_retries} retries each")

    # 3. Complete
    parts = sorted(completed.values(), key=lambda p: p["PartNumber"])
    async with httpx.AsyncClient(base_url=BASE, headers=headers) as c:
        resp = await c.post(
            f"/buckets/{bucket}/multipart/{key}/complete",
            json={"upload_id": upload_id, "parts": parts},
        )
        resp.raise_for_status()
        print("Upload complete:", resp.json())
```

### Consistency considerations

HCP follows S3 semantics for consistency:

| Operation | Consistency |
|-----------|-------------|
| `PUT` new object | **Read-after-write** -- immediately visible |
| `PUT` overwrite existing object | **Eventually consistent** -- stale reads possible briefly |
| `DELETE` object | **Eventually consistent** -- object may still appear in listings briefly |
| `LIST` objects | **Eventually consistent** -- recently added/deleted objects may not appear immediately |
| MAPI `PUT`/`POST` create/update | **Strongly consistent** -- change visible on next read |

!!! tip "Eventual consistency workaround"
    If your script writes an object and then immediately reads it back (e.g., to verify a checksum), add a brief delay or use a `HEAD` request with retries:

    ```python
    import asyncio
    import httpx

    async def wait_for_object(
        client: httpx.AsyncClient,
        bucket: str,
        key: str,
        max_wait: float = 10.0,
    ) -> bool:
        """Poll until an object is visible after upload."""
        elapsed = 0.0
        delay = 0.5
        while elapsed < max_wait:
            resp = await client.head(f"/buckets/{bucket}/objects/{key}")
            if resp.status_code == 200:
                return True
            await asyncio.sleep(delay)
            elapsed += delay
            delay = min(delay * 2, 2.0)
        return False
    ```

### Argo-native retries and timeouts

Argo Workflows has built-in retry and timeout support at the template level. Use these **in addition to** application-level retries -- Argo retries restart the entire pod, which handles OOM kills, node evictions, and infrastructure failures that application code cannot catch.

#### retryStrategy (YAML)

```yaml
templates:
  - name: process-data
    retryStrategy:
      limit: 3                    # max 3 retries (4 total attempts)
      retryPolicy: Always         # retry on both errors and node failures
      backoff:
        duration: "10s"           # initial delay
        factor: 2                 # exponential: 10s, 20s, 40s
        maxDuration: "2m"         # cap at 2 minutes
    activeDeadlineSeconds: 600    # hard timeout: kill pod after 10 min
    container:
      image: python:3.13-slim
      command: [python, -c]
      args:
        - |
          # your processing code here
          print("processing...")
```

#### retryStrategy (Hera)

```python
from hera.workflows import models as m, script

@script(
    image="python:3.13-slim",
    retry_strategy=m.RetryStrategy(
        limit="3",
        retry_policy="Always",
        backoff=m.Backoff(duration="10s", factor=2, max_duration="2m"),
    ),
    active_deadline_seconds=600,
)
def process_data():
    """Processing with Argo-managed retries and timeout."""
    print("processing...")
```

### Cleanup on failure — exit handlers

Use Argo exit handlers to guarantee cleanup runs regardless of workflow success or failure. This is essential for aborting in-progress multipart uploads, deleting partial results, or releasing resources.

#### Exit handler (YAML)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: hcp-safe-upload-
spec:
  entrypoint: upload-pipeline
  onExit: cleanup                    # always runs, even on failure
  arguments:
    parameters:
      - name: hcp-api-base
        value: "http://hcp-api.default.svc:8000/api/v1"
      - name: hcp-token
        value: "<your-token>"
      - name: bucket
        value: "datasets"
  templates:
    - name: upload-pipeline
      steps:
        - - name: upload
            template: do-upload

    - name: do-upload
      retryStrategy:
        limit: 2
      script:
        image: python:3.13-slim
        command: [python]
        source: |
          # ... upload logic ...
          print("uploading data")

    # ── Guaranteed cleanup ──────────────────────────────────────
    - name: cleanup
      script:
        image: curlimages/curl:latest
        command: [sh]
        source: |
          BASE="{{workflow.parameters.hcp-api-base}}"
          TOKEN="{{workflow.parameters.hcp-token}}"
          BUCKET="{{workflow.parameters.bucket}}"
          STATUS="{{workflow.status}}"    # Succeeded / Failed / Error

          if [ "$STATUS" != "Succeeded" ]; then
            echo "Workflow $STATUS -- cleaning up partial uploads..."

            # Abort any in-progress multipart uploads
            # Delete partial results to avoid polluting the bucket
            curl -s -X POST "$BASE/s3/buckets/$BUCKET/objects/delete" \
              -H "Authorization: Bearer $TOKEN" \
              -H "Content-Type: application/json" \
              -d "{\"keys\": [\"partial/{{workflow.name}}/\"]}" || true

            echo "Cleanup complete"
          else
            echo "Workflow succeeded -- no cleanup needed"
          fi
```

#### Exit handler (Hera)

```python
from hera.workflows import DAG, Parameter, Steps, Workflow, models as m, script

HCP_BASE = "http://hcp-api.default.svc:8000/api/v1"


@script(image="python:3.13-slim", retry_strategy=m.RetryStrategy(limit="2"))
def do_upload(hcp_api_base: str, hcp_token: str, bucket: str):
    """Upload data to HCP."""
    print("uploading data")


@script(image="curlimages/curl:latest")
def cleanup(hcp_api_base: str, hcp_token: str, bucket: str):
    """Clean up partial uploads on failure. Runs as onExit handler."""
    import subprocess, os

    status = os.environ.get("ARGO_WORKFLOW_STATUS", "Unknown")
    if status != "Succeeded":
        print(f"Workflow {status} -- cleaning up...")
        subprocess.run(
            [
                "curl", "-s", "-X", "POST",
                f"{hcp_api_base}/s3/buckets/{bucket}/objects/delete",
                "-H", f"Authorization: Bearer {hcp_token}",
                "-H", "Content-Type: application/json",
                "-d", '{"keys": ["partial/"]}',
            ],
            check=False,  # don't fail cleanup on errors
        )
        print("Cleanup complete")
    else:
        print("Workflow succeeded -- no cleanup needed")


with Workflow(
    generate_name="hcp-safe-upload-",
    entrypoint="upload-pipeline",
    on_exit="cleanup",
    arguments=[
        Parameter(name="hcp-api-base", value=HCP_BASE),
        Parameter(name="hcp-token", value="<your-token>"),
        Parameter(name="bucket", value="datasets"),
    ],
) as w:
    with Steps(name="upload-pipeline"):
        do_upload(
            name="upload",
            arguments={
                "hcp_api_base": "{{workflow.parameters.hcp-api-base}}",
                "hcp_token": "{{workflow.parameters.hcp-token}}",
                "bucket": "{{workflow.parameters.bucket}}",
            },
        )

    # Exit handler template (registered by name via on_exit="cleanup")
    cleanup(
        name="cleanup",
        arguments={
            "hcp_api_base": "{{workflow.parameters.hcp-api-base}}",
            "hcp_token": "{{workflow.parameters.hcp-token}}",
            "bucket": "{{workflow.parameters.bucket}}",
        },
    )

w.create()
```

### ACID-like guarantees for workflows

Object storage is not a relational database -- there are no transactions. But you can approximate ACID properties through careful workflow design:

| Property | S3/HCP reality | How to achieve it |
|----------|---------------|-------------------|
| **Atomicity** | Individual PUTs are atomic, but a multi-object "transaction" is not. | Use exit handlers (`onExit`) to clean up partial state on failure. Write to a staging prefix first, then "commit" by copying to the final location. |
| **Consistency** | New PUTs are read-after-write consistent. Overwrites and deletes are eventually consistent. | Use `HEAD` polling after writes ([`wait_for_object`](#consistency-considerations) above). Use unique keys per workflow run (`{{workflow.name}}`) to avoid overwrites. |
| **Isolation** | No locking — concurrent writers to the same key cause last-write-wins. | Namespace outputs by workflow run ID: `results/{{workflow.name}}/output.json`. Never write to a shared key from parallel pods. |
| **Durability** | S3 objects are durable once the PUT succeeds (HCP replicates across nodes). | Verify uploads with a `HEAD` request checking `Content-Length` and `ETag`. For critical data, use versioning-enabled namespaces. |

#### Staged-commit pattern

Write results to a temporary prefix, verify them, then "commit" by copying to the final location. On failure, the exit handler deletes the staging prefix.

```python
import httpx

BASE = "http://localhost:8000/api/v1"

async def staged_upload(
    token: str,
    bucket: str,
    final_key: str,
    data: bytes,
    workflow_id: str,
):
    """Upload to a staging key, verify, then copy to the final location."""
    headers = {"Authorization": f"Bearer {token}"}
    staging_key = f"staging/{workflow_id}/{final_key}"

    async with httpx.AsyncClient(base_url=BASE, headers=headers, timeout=60.0) as c:
        # 1. Write to staging
        resp = await c.put(
            f"/s3/buckets/{bucket}/objects/{staging_key}",
            content=data,
        )
        resp.raise_for_status()

        # 2. Verify — HEAD to confirm size
        resp = await c.head(f"/s3/buckets/{bucket}/objects/{staging_key}")
        resp.raise_for_status()
        actual_size = int(resp.headers.get("content-length", 0))
        if actual_size != len(data):
            # Mismatch — delete staging and raise
            await c.delete(f"/s3/buckets/{bucket}/objects/{staging_key}")
            raise RuntimeError(
                f"Size mismatch: expected {len(data)}, got {actual_size}"
            )

        # 3. Commit — copy from staging to final
        resp = await c.post(
            f"/s3/buckets/{bucket}/objects/{final_key}/copy",
            json={"source_bucket": bucket, "source_key": staging_key},
        )
        resp.raise_for_status()

        # 4. Clean up staging
        await c.delete(f"/s3/buckets/{bucket}/objects/{staging_key}")

        print(f"Committed {final_key} ({actual_size} bytes)")
```

```bash
# Bash equivalent — staged commit
STAGING_KEY="staging/$(uuidgen)/$FINAL_KEY"

# 1. Write to staging
curl -s -X PUT "$BASE/s3/buckets/$BUCKET/objects/$STAGING_KEY" \
  -H "$AUTH" --data-binary @"$LOCAL_FILE"

# 2. Verify
SIZE=$(curl -s -I "$BASE/s3/buckets/$BUCKET/objects/$STAGING_KEY" \
  -H "$AUTH" | grep -i content-length | awk '{print $2}' | tr -d '\r')
EXPECTED=$(stat -f%z "$LOCAL_FILE")
if [ "$SIZE" != "$EXPECTED" ]; then
  echo "ERROR: Size mismatch ($SIZE != $EXPECTED)" >&2
  curl -s -X DELETE "$BASE/s3/buckets/$BUCKET/objects/$STAGING_KEY" -H "$AUTH"
  exit 1
fi

# 3. Commit — copy to final location
curl -s -X POST "$BASE/s3/buckets/$BUCKET/objects/$FINAL_KEY/copy" \
  -H "$AUTH" -H "Content-Type: application/json" \
  -d "{\"source_bucket\": \"$BUCKET\", \"source_key\": \"$STAGING_KEY\"}"

# 4. Clean up staging
curl -s -X DELETE "$BASE/s3/buckets/$BUCKET/objects/$STAGING_KEY" -H "$AUTH"

echo "Committed $FINAL_KEY"
```

!!! warning "Multipart uploads are not atomic"
    A multipart upload is only visible after `CompleteMultipartUpload`. If the workflow fails between uploading parts and completing, the parts remain as invisible orphans consuming storage. Always use exit handlers to call `AbortMultipartUpload` on failure, and consider enabling `artifactGC` on the workflow to clean up Argo-managed artifacts.
