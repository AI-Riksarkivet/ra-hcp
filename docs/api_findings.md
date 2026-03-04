# HCP API Investigation Findings

## Quick Reference: What We Can Do But Don't Yet

### High Priority — Frontend gaps where backend + mock already work

| Feature | Backend | Mock | Frontend |
|---|---|---|---|
| Namespace statistics per-ns | `GET .../namespaces/{N}/statistics` | Static fixture | **Not used** |
| Chargeback reports (tenant + ns) | `GET .../chargebackReport` | Static fixture | **Not used** |
| Modify tenant settings (all sub-resources) | All POST endpoints | Supported | **Read-only display** |
| Modify namespace (main properties) | `POST .../namespaces/{N}` | Supported | **Not used** |
| Versioning settings CRUD | `GET/POST/DELETE` | Supported | **Not used** |
| Compliance settings | `GET/POST` | Supported | **Not used** |
| Retention classes CRUD | Full CRUD | Supported | **Not used** |
| Group details/modify/delete | Full CRUD | Supported | **Only list + create** |
| Namespace CORS | `GET/PUT/DELETE` | Supported | **Not used** |
| Custom metadata indexing settings | `GET/POST` | Supported | **Not used** |

---

## 1. Statistics & Dashboard Data

### Tenant Statistics
- **Endpoint:** `GET /tenants/{T}/statistics`
- **Fields:** `customMetadataCount`, `customMetadataSize`, `ingestedVolume`, `objectCount`, `shredCount`, `shredSize`, `storageCapacityUsed`
- **Role required:** MONITOR or ADMINISTRATOR

### Namespace Statistics
- **Endpoint:** `GET /tenants/{T}/namespaces/{N}/statistics`
- **Fields:** Same as tenant statistics, scoped per namespace

### Chargeback Reports (best source for activity data)
- **Endpoints:** `GET /tenants/{T}/chargebackReport`, `GET /tenants/{T}/namespaces/{N}/chargebackReport`
- **Query params:** `start`, `end`, `granularity` (hour, day, total)
- **Fields:** `objectCount`, `ingestedVolume`, `storageCapacityUsed`, `bytesIn`, `bytesOut`, `reads`, `writes`, `deletes`, `multipartObjects`, `multipartObjectParts`, `multipartObjectBytes`, `multipartUploads`, `multipartUploadParts`, `multipartUploadBytes`, `deleted`, `valid`
- **Note:** Data kept for 180 days

### System-Level (requires system admin)
- `GET /nodes/statistics` — per-node CPU, IO, connections, storage volumes
- `GET /services/statistics` — service-level stats
- `GET/POST /logs` — log management (prepare, download, mark)

---

## 2. Roles Explained

| Role | What it controls |
|---|---|
| **ADMINISTRATOR** | Full tenant admin: create namespaces, manage users/groups, view statistics |
| **SECURITY** | Manage console security, search security, authentication settings |
| **MONITOR** | View tenant/namespace statistics and chargeback reports (read-only) |
| **COMPLIANCE** | Manage compliance/retention settings on namespaces |

### Data Access Permissions (per user/group per namespace)
`BROWSE`, `READ`, `WRITE`, `DELETE`, `PURGE`, `SEARCH`, `READ_ACL`, `WRITE_ACL`, `CHOWN`, `PRIVILEGED`

### User Account Properties
| Property | Writable | Notes |
|---|---|---|
| `username` | Create only | 3-64 chars |
| `fullName` | Yes | Display name |
| `description` | Yes | Free-form |
| `enabled` | Yes | Default: true |
| `forcePasswordChange` | Yes | Default: false |
| `localAuthentication` | Yes | Non-AD auth |
| `roles` | Yes | ADMINISTRATOR, COMPLIANCE, MONITOR, SECURITY |
| `allowNamespaceManagement` | Yes | Can create/manage namespaces |
| `userGUID`, `userID` | Read-only | System-generated |
| `password` | Write-only | Never returned |

---

## 3. Namespace Settings Explained

### Main Properties
| Setting | Values | Meaning |
|---|---|---|
| `searchEnabled` | boolean | Enables HCP metadata query engine indexing. NOT S3 search — it's a separate HCP Search Console / Metadata Query API |
| `indexingEnabled` | boolean | Whether indexing engine indexes new/changed objects (separate from searchEnabled) |
| `customMetadataIndexingEnabled` | boolean | Whether `x-amz-meta-*` headers are indexed for queries |
| `versioningSettings.enabled` | boolean | Object versioning with integer version IDs. Disabling does NOT delete old versions |
| `versioningSettings.prune` | boolean | Auto-delete old versions after `pruneDays` days |
| `optimizedFor` | CLOUD / ALL | CLOUD = S3/REST only. ALL = also CIFS, NFS file protocols |
| `hashScheme` | MD5/SHA-1/SHA-256/SHA-384/SHA-512/RIPEMD-160 | Object integrity verification. **Set at creation, cannot change** |
| `enterpriseMode` | boolean | Allows privileged delete of retained objects. Without = truly immutable |
| `aclsUsage` | ENFORCED/NOT_ENFORCED/OFF | ACL enforcement level |
| `retentionType` | HCP / S3 | HCP-native vs AWS S3 Object Lock compatible |
| `directoryUsage` | Balanced / Unbalanced | Directory distribution strategy |
| `hardQuota` | decimal (GB) | Storage limit |
| `softQuota` | integer (%) | Warning threshold |

### Protocol Settings
| Protocol | Properties | What it does |
|---|---|---|
| **HTTP** | httpEnabled, httpsEnabled, restEnabled, hs3Enabled, webdavEnabled, etc. | REST API, S3, WebDAV access |
| **CIFS** | enabled, caseSensitive, caseForcing | Windows file sharing (SMB) |
| **NFS** | enabled, uid, gid | Unix/Linux NFS mount |
| **SMTP** | enabled, emailDomain | Email-based object ingestion |

### Namespace Sub-Resources (all support GET + POST)
- `protocols/{http|cifs|nfs|smtp}` — protocol config
- `complianceSettings` — compliance mode (requires COMPLIANCE role)
- `versioningSettings` — versioning + pruning
- `customMetadataIndexingSettings` — metadata indexing config
- `permissions` — data access mask (DELETE, PRIVILEGED, PURGE, READ, SEARCH, WRITE)
- `cors` — CORS config (PUT/GET/DELETE)
- `replicationCollisionSettings` — conflict resolution

---

## 4. Tenant Admin Capabilities

### What a Tenant Admin CAN Change (via POST)
| Sub-resource | Endpoint | Controls |
|---|---|---|
| Tenant itself | `POST /tenants/{T}` | quotas, auth types, descriptions, logging |
| Console security | `POST .../consoleSecurity` | IP allowlist/denylist, password policy, login timeout (needs SECURITY role) |
| Contact info | `POST .../contactInfo` | Name, email, phone |
| Email notification | `POST .../emailNotification` | SMTP server, sender, enabled |
| Namespace defaults | `POST .../namespaceDefaults` | Default quota, hash scheme, search/versioning defaults |
| Permissions | `POST .../permissions` | Tenant-level data access mask |
| Search security | `POST .../searchSecurity` | IP allowlist/denylist for search (needs SECURITY role) |
| CORS | `PUT/DELETE .../cors` | Cross-origin config |

### Read-Only (cannot change)
- `name` — set at creation
- `hashScheme` on namespaces — set at creation
- `userGUID`, `userID` — system-generated
- `username`, `groupname` — set at creation

---

## 5. S3-Level Features

### No S3 Search API
HCP S3 has no full-text or metadata query API. Search is only via the separate HCP Metadata Query Engine.

### Versioning
- `GET /?versioning` / `PUT /?versioning` — standard S3 versioning
- Integer version IDs (not UUIDs)
- Supports delete markers, pruning

### Retention & Compliance (S3)
- HCP-native: `x-hcp-retention`, `x-hcp-retentionhold`, `x-hcp-labelretentionhold`
- S3 Object Lock: `x-amz-object-lock-mode` (GOVERNANCE/COMPLIANCE), `x-amz-object-lock-retain-until-date`, `x-amz-object-lock-legal-hold`
- Privileged delete: `x-hcp-privileged: reason-text`

### Useful for Frontend
- Content-Type auto-detection on PUT
- Response header overrides: `response-content-type`, `response-content-disposition` (inline vs attachment)
- Byte range requests: `Range: bytes=start-end`
- Conditional requests: `If-None-Match`, `If-Modified-Since` for caching
- Custom metadata: `x-amz-meta-*` headers (max 2KB per object)
- Server-side copy: `PUT` with `x-amz-copy-source` header
- Multipart upload: initiate/upload parts/complete/abort
