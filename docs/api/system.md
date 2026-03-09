# System API

All System API endpoints require JWT authentication with **system-level admin credentials**.
Log in with a system-level username (no tenant prefix) to obtain a valid token.

Base URL: `/api/v1/mapi`

---

## Replication Links

Manage replication links between HCP systems.

**Prefix:** `/services/replication/links`

### Link CRUD

| Method | Path | Description |
|--------|------|-------------|
| GET | `/services/replication/links` | List all replication links |
| PUT | `/services/replication/links` | Create a replication link |
| GET | `/services/replication/links/{link_name}` | Get link details |
| HEAD | `/services/replication/links/{link_name}` | Check if link exists |
| POST | `/services/replication/links/{link_name}` | Modify link or trigger action |
| DELETE | `/services/replication/links/{link_name}` | Delete a replication link |

### Link Actions

Link actions are triggered via `POST /services/replication/links/{link_name}` with query parameters:

| Query Param | Description |
|-------------|-------------|
| `suspend` | Suspend the replication link |
| `resume` | Resume a suspended link |
| `failOver` | Trigger failover to the remote system |
| `failBack` | Trigger failback to the local system |
| `beginRecover` | Begin recovery after failover |
| `completeRecovery` | Complete the recovery process |
| `restore` | Restore link state |

### Link Content

Manage which tenants, directories, and chained links are included in replication.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{link_name}/content` | Get all link content |
| GET | `/{link_name}/content/tenants` | List tenants in link |
| PUT | `/{link_name}/content/tenants/{tenant_name}` | Add tenant to link |
| GET | `/{link_name}/content/tenants/{tenant_name}` | Get tenant replication details |
| POST | `/{link_name}/content/tenants/{tenant_name}` | Pause/resume tenant replication |
| DELETE | `/{link_name}/content/tenants/{tenant_name}` | Remove tenant from link |
| GET | `/{link_name}/content/defaultNamespaceDirectories` | List default namespace directories |
| PUT | `/{link_name}/content/defaultNamespaceDirectories/{dir}` | Add directory to link |
| DELETE | `/{link_name}/content/defaultNamespaceDirectories/{dir}` | Remove directory from link |
| GET | `/{link_name}/content/chainedLinks` | List chained links |
| PUT | `/{link_name}/content/chainedLinks/{chained}` | Add chained link |
| DELETE | `/{link_name}/content/chainedLinks/{chained}` | Remove chained link |

### Link Schedule

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{link_name}/schedule` | Get link schedule |
| POST | `/{link_name}/schedule` | Update link schedule |

### Link Candidates

| Method | Path | Description |
|--------|------|-------------|
| GET | `/{link_name}/localCandidates` | All local candidates |
| GET | `/{link_name}/localCandidates/tenants` | Local tenant candidates |
| GET | `/{link_name}/localCandidates/defaultNamespaceDirectories` | Local directory candidates |
| GET | `/{link_name}/localCandidates/chainedLinks` | Local chained link candidates |
| GET | `/{link_name}/remoteCandidates` | All remote candidates |
| GET | `/{link_name}/remoteCandidates/tenants` | Remote tenant candidates |

---

## Replication Certificates

Manage SSL certificates used for replication link encryption.

**Prefix:** `/services/replication/certificates`

| Method | Path | Description |
|--------|------|-------------|
| GET | `/services/replication/certificates` | List all certificates |
| PUT | `/services/replication/certificates` | Upload a certificate (PEM file) |
| GET | `/services/replication/certificates/{id}` | Get certificate details |
| DELETE | `/services/replication/certificates/{id}` | Delete a certificate |
| GET | `/services/replication/certificates/server` | Download server certificate |

---

## Replication Service

View and modify the global replication service configuration.

| Method | Path | Description |
|--------|------|-------------|
| GET | `/services/replication` | Get replication service status |
| POST | `/services/replication` | Update replication settings |

Query parameters for POST: `shutDownAllLinks`, `reestablishAllLinks`.

---

## Erasure Coding

Manage erasure coding (EC) topologies for storage efficiency.

**Prefix:** `/services/erasureCoding`

### EC Topologies

| Method | Path | Description |
|--------|------|-------------|
| GET | `/services/erasureCoding/ecTopologies` | List EC topologies |
| PUT | `/services/erasureCoding/ecTopologies` | Create EC topology |
| GET | `/services/erasureCoding/ecTopologies/{name}` | Get topology details |
| HEAD | `/services/erasureCoding/ecTopologies/{name}` | Check if topology exists |
| POST | `/services/erasureCoding/ecTopologies/{name}` | Modify or retire topology |
| DELETE | `/services/erasureCoding/ecTopologies/{name}` | Delete topology |

### EC Topology Tenants

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ecTopologies/{name}/tenants` | List tenants in topology |
| PUT | `/ecTopologies/{name}/tenants/{tenant}` | Add tenant to topology |
| DELETE | `/ecTopologies/{name}/tenants/{tenant}` | Remove tenant from topology |

### EC Candidates

| Method | Path | Description |
|--------|------|-------------|
| GET | `/ecTopologies/{name}/tenantCandidates` | Eligible tenants |
| GET | `/ecTopologies/{name}/tenantConflictingCandidates` | Tenants with conflicts |
| GET | `/linkCandidates` | Eligible replication links |

---

## Infrastructure

### Network

| Method | Path | Description |
|--------|------|-------------|
| GET | `/network` | Get network settings |
| POST | `/network` | Update network settings |

### Licenses

| Method | Path | Description |
|--------|------|-------------|
| GET | `/storage/licenses` | List all licenses |
| PUT | `/storage/licenses` | Upload a license file |
| GET | `/storage/licenses/{serial}` | Get license details |

### Statistics

| Method | Path | Description |
|--------|------|-------------|
| GET | `/nodes/statistics` | Node-level statistics (CPU, memory, disk) |
| GET | `/services/statistics` | Service-level statistics |

---

## Operations

### Health Check

| Method | Path | Description |
|--------|------|-------------|
| GET | `/healthCheckReport` | Get health check status |
| POST | `/healthCheckReport/prepare` | Prepare a health check |
| POST | `/healthCheckReport/download` | Download health check data |
| POST | `/healthCheckReport/cancel` | Cancel in-progress health check |

### Logs

| Method | Path | Description |
|--------|------|-------------|
| GET | `/logs` | Get log download status |
| POST | `/logs` | Mark logs or cancel download |
| POST | `/logs/prepare` | Prepare log download |
| POST | `/logs/download` | Download logs |

### Support Access

| Method | Path | Description |
|--------|------|-------------|
| GET | `/supportaccesscredentials` | Get support credentials |
| PUT | `/supportaccesscredentials` | Upload support credentials |

---

## System Identity

Manage system-level user and group accounts.

### User Accounts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/userAccounts` | List system user accounts |
| GET | `/userAccounts/{username}` | Get user account details |
| HEAD | `/userAccounts/{username}` | Check if user exists |
| POST | `/userAccounts/{username}` | Modify user account |
| POST | `/userAccounts/{username}/changePassword` | Change user password |

### Group Accounts

| Method | Path | Description |
|--------|------|-------------|
| GET | `/groupAccounts` | List system group accounts |
| GET | `/groupAccounts/{group}` | Get group account details |
| HEAD | `/groupAccounts/{group}` | Check if group exists |

---

## Metadata Query

Search object metadata and audit operations across tenant namespaces.

**Prefix:** `/query/tenants/{tenant_name}`

!!! note
    Metadata Query endpoints use the `/api/v1/query` prefix (not `/api/v1/mapi`).

### Object Query

```
POST /api/v1/query/tenants/{tenant_name}/objects
```

Search for objects using Lucene query syntax against indexed metadata.

**Request Body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `query` | string | *(required)* | Lucene query expression |
| `count` | integer | `100` | Maximum results to return |
| `offset` | integer | `0` | Starting offset for pagination |
| `sort` | string | `null` | Sort field (`+field` ascending, `-field` descending) |
| `verbose` | boolean | `false` | Include full metadata in results |
| `objectProperties` | string[] | `null` | Specific properties to return |
| `facets` | string[] | `null` | Facet fields to aggregate |

**Example:**

```json
{
  "query": "namespace:finance AND size:[1048576 TO *]",
  "count": 50,
  "offset": 0,
  "sort": "-changeTimeMilliseconds",
  "verbose": true,
  "objectProperties": ["urlName", "size", "contentType", "changeTimeString"]
}
```

### Operation Query

```
POST /api/v1/query/tenants/{tenant_name}/operations
```

Audit trail of create, delete, purge, and dispose events.

**Request Body:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `count` | integer | `100` | Maximum results to return |
| `lastResult` | object | `null` | Cursor from previous page (for pagination) |
| `verbose` | boolean | `false` | Include full metadata |
| `systemMetadata` | object | `null` | Filters for time range, namespaces, transactions |

**System Metadata Filters:**

| Field | Type | Description |
|-------|------|-------------|
| `changeTime.start` | string | Start time (epoch ms or ISO 8601) |
| `changeTime.end` | string | End time (epoch ms or ISO 8601) |
| `namespaces.namespace` | string[] | Filter to specific namespaces |
| `transactions.transaction` | string[] | Transaction types: `create`, `delete`, `purge`, `dispose` |

---

## Common Patterns

### Verbose Mode

Most `GET` endpoints accept a `verbose` query parameter. When `true`, the response includes all available fields. When `false` (default), only names or identifiers are returned.

### Status Responses

Mutating operations return a `StatusResponse`:

```json
{
  "status": "created"
}
```

Common status values: `created`, `updated`, `deleted`, `ok`, `password_changed`, `cancelled`.

### Error Responses

| Status Code | Meaning |
|-------------|---------|
| 400 | Bad request (invalid body or parameters) |
| 401 | Unauthorized (missing or expired JWT) |
| 403 | Forbidden (insufficient permissions) |
| 404 | Resource not found |
| 409 | Conflict (resource already exists) |
| 500 | Internal server error |
