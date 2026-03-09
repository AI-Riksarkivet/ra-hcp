# Namespaces API

Namespace endpoints manage storage namespaces within an HCP tenant. Each namespace is a logical container for objects with its own configuration for protocols, compliance, indexing, and access control.

All endpoints require JWT authentication. See [Authentication](authentication.md) for details.

---

## Namespace Management

**Base path:** `/api/v1/mapi/tenants/{tenant_name}/namespaces`

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../namespaces` | List all namespaces in the tenant. Add `verbose=true` for full details. |
| `PUT` | `.../namespaces` | Create a new namespace. Body: [NamespaceCreate](#namespacecreate). |
| `GET` | `.../namespaces/{ns_name}` | Get namespace details. |
| `HEAD` | `.../namespaces/{ns_name}` | Check whether a namespace exists. Returns `200` or `404`. |
| `POST` | `.../namespaces/{ns_name}` | Update namespace settings. Body: [NamespaceUpdate](#namespaceupdate). |
| `DELETE` | `.../namespaces/{ns_name}` | Delete a namespace. |

### NamespaceCreate

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Namespace name (must be unique within the tenant) |
| `description` | string | No | Human-readable description |
| `hardQuota` | string | No | Maximum storage capacity (e.g., `"50 GB"`) |
| `softQuota` | integer | No | Soft quota percentage (0--100) |
| `hashScheme` | string | No | Object hashing scheme |
| `optimizedFor` | string | No | Optimization target (e.g., `cloud`, `default`) |
| `versioningSettings` | object | No | Versioning configuration |
| `tags` | object | No | Custom tags |

### NamespaceUpdate

All fields are optional: `description`, `hardQuota`, `softQuota`, `tags`, `versioningSettings`, and more.

---

## Namespace Templates

Export namespace configurations as reusable templates.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../namespaces/{ns_name}/export` | Export a single namespace as a template |
| `GET` | `.../namespaces/export?names=ns1,ns2` | Export multiple namespaces as a template bundle |

---

## Versioning

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../namespaces/{ns_name}/versioningSettings` | Get versioning configuration |
| `POST` | `.../namespaces/{ns_name}/versioningSettings` | Update versioning configuration |

---

## Compliance

Manage compliance settings and retention classes. Requires the `COMPLIANCE` role.

**Base path:** `/api/v1/mapi/tenants/{tenant_name}/namespaces/{ns_name}`

### Compliance Settings

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../complianceSettings` | Get namespace compliance configuration |
| `POST` | `.../complianceSettings` | Update namespace compliance configuration |

### Retention Classes

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../retentionClasses` | List all retention classes |
| `PUT` | `.../retentionClasses` | Create a new retention class |
| `GET` | `.../retentionClasses/{class_name}` | Get retention class details |
| `HEAD` | `.../retentionClasses/{class_name}` | Check whether a retention class exists |
| `POST` | `.../retentionClasses/{class_name}` | Update a retention class |
| `DELETE` | `.../retentionClasses/{class_name}` | Delete a retention class |

### RetentionClassCreate

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | Yes | Retention class name |
| `value` | string | Yes | Retention period (e.g., `"A+7y"` for 7 years after ingest) |
| `description` | string | No | Human-readable description |
| `allowDeletion` | boolean | No | Allow deletion before retention expires |

---

## Access & Protocols

Manage namespace permissions and protocol configurations. Requires the `ADMINISTRATOR` role.

### Permissions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../permissions` | Get namespace permissions |
| `POST` | `.../permissions` | Update namespace permissions |

### Protocol Configuration

Each protocol has its own get/set endpoints:

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../protocols/httpConfig` | Get HTTP/REST protocol settings |
| `POST` | `.../protocols/httpConfig` | Update HTTP/REST protocol settings |
| `GET` | `.../protocols/nfsConfig` | Get NFS protocol settings |
| `POST` | `.../protocols/nfsConfig` | Update NFS protocol settings |
| `GET` | `.../protocols/cifsConfig` | Get CIFS/SMB protocol settings |
| `POST` | `.../protocols/cifsConfig` | Update CIFS/SMB protocol settings |
| `GET` | `.../protocols/smtpConfig` | Get SMTP protocol settings |
| `POST` | `.../protocols/smtpConfig` | Update SMTP protocol settings |

### CORS

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../cors` | Get namespace CORS configuration |
| `PUT` | `.../cors` | Set namespace CORS configuration |
| `DELETE` | `.../cors` | Remove namespace CORS configuration |

### Replication Collision Settings

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../replicationCollisionSettings` | Get collision handling settings |
| `POST` | `.../replicationCollisionSettings` | Update collision handling settings |

---

## Indexing

Manage custom metadata indexing. Requires the `ADMINISTRATOR` role.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../cifsConfig` | Get CIFS config (includes indexing settings) |
| `POST` | `.../cifsConfig` | Update CIFS config and indexing settings |

---

## Namespace Statistics

View namespace resource usage and chargeback data. Requires the `MONITOR` role.

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `.../statistics` | Get namespace statistics |
| `GET` | `.../chargebackReport` | Get namespace chargeback report |

### Chargeback Query Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `start` | string | -- | Start time (ISO 8601) |
| `end` | string | -- | End time (ISO 8601) |
| `granularity` | string | `total` | Report granularity: `hour`, `day`, or `total` |
