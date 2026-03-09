# HCP Concepts

This page explains the core concepts of Hitachi Content Platform (HCP) that you'll encounter when using the HCP App.

## Object-Based Storage

HCP stores **objects** in a repository. Each object permanently associates data with metadata:

```mermaid
graph LR
    subgraph "Object"
        DATA["Fixed-Content Data<br/>(immutable once stored)"]
        SYS["System Metadata<br/>size · creation date · retention"]
        CUSTOM["Custom Metadata<br/>(optional annotations)"]
        ACL["Access Control List<br/>(optional permissions)"]
    end
```

| Component | Description |
|-----------|-------------|
| **Fixed-content data** | The actual file content. Once stored, it cannot be modified (WORM -- write once, read many). |
| **System metadata** | Automatically managed properties: size, creation date, retention policy, hash, etc. |
| **Custom metadata** | Optional user-provided annotations (XML or key-value pairs via `x-amz-meta-*` headers). |
| **ACL** | Optional access control list defining who can read, write, or manage the object. |

## Tenants

A **tenant** is an administrative entity that owns and manages a portion of the HCP repository. Tenants typically correspond to organizations, departments, or business units.

```mermaid
graph TD
    HCP["HCP System"] --> T1["Tenant: Finance"]
    HCP --> T2["Tenant: Engineering"]
    HCP --> T3["Tenant: Compliance"]
    T1 --> NS1["Namespace: invoices"]
    T1 --> NS2["Namespace: reports"]
    T2 --> NS3["Namespace: builds"]
    T2 --> NS4["Namespace: artifacts"]
    T3 --> NS5["Namespace: audit-logs"]
```

Each tenant has:

- **Quotas** -- hard and soft storage limits
- **User accounts** -- tenant-scoped credentials with role-based access
- **Configuration** -- console security, email notifications, namespace defaults
- **Statistics** -- storage usage and chargeback reporting

## Namespaces (Buckets)

A **namespace** (also called a **bucket** in S3 terminology) is a logical container for objects within a tenant. Objects in one namespace are not visible in any other namespace.

Namespaces provide:

- **Isolation** -- separate data for different applications or purposes
- **Protocol configuration** -- each namespace can enable/disable HTTP, S3, NFS, CIFS, SMTP independently
- **Compliance settings** -- retention policies, versioning, and hold rules per namespace
- **Search indexing** -- custom metadata indexing for the Metadata Query API

!!! tip "Buckets = Namespaces"
    In the S3 API, namespaces are called "buckets." The terms are interchangeable. When you create a bucket via S3, you're creating a namespace. When you manage namespaces via MAPI, you're managing buckets.

## Versioning

HCP can store **multiple versions** of an object, providing a history of changes over time. Each version is a separate object with its own metadata.

| Concept | Description |
|---------|-------------|
| **Version ID** | Integer identifier for each version (HCP uses integer IDs, not UUIDs like AWS S3). |
| **Delete marker** | When versioning is enabled, deleting an object creates a delete marker instead of removing data. |
| **Pruning** | Removing old versions of an object while keeping the current version. |
| **Purging** | Permanently removing all versions of an object, including the current version. |

Versioning is enabled per namespace and can be toggled between `Enabled` and `Suspended`.

## Retention & Compliance

HCP provides WORM (Write Once, Read Many) storage with configurable retention policies to prevent premature deletion.

### Retention Modes

| Mode | Value | Behavior |
|------|-------|----------|
| **Deletion Allowed** | `0` | Object can be deleted at any time. |
| **Deletion Prohibited** | `-1` | Object can never be deleted (permanent retention). |
| **Initial Unspecified** | `-2` | Retention not yet set -- can be set later. |
| **Fixed date** | datetime | Object cannot be deleted until the specified date. |
| **Offset** | `A+7y` | Retention calculated relative to ingest time (e.g., 7 years after creation). |
| **Retention class** | class name | Retention defined by a named class with a specific period. |

### S3 Object Lock

HCP also supports **S3 Object Lock** for applications using the S3 API:

- **Governance mode** -- most users cannot delete, but users with `BypassGovernanceRetention` permission can override.
- **Compliance mode** -- no one can delete until the retention period expires, not even administrators.
- **Legal holds** -- prevent deletion regardless of retention settings. Up to 100 labeled holds per object.

### Retention Classes

Retention classes are named policies defined at the namespace level. They simplify management by letting you assign a class name instead of a specific date to each object. When you update a retention class, all objects using that class are updated automatically.

## Roles & Permissions

### Tenant Roles

User accounts within a tenant are assigned one or more roles:

| Role | Permissions |
|------|-------------|
| **ADMINISTRATOR** | Full tenant administration: namespaces, users, settings, protocols. |
| **SECURITY** | Manage console security, search security, and user accounts. |
| **MONITOR** | Read-only access to statistics, chargeback reports, and configuration. |
| **COMPLIANCE** | Manage compliance settings, retention classes, and content classes. |

### Data Access Permissions

In addition to roles, users can be granted **data access permissions** for individual namespaces:

| Permission | Description |
|------------|-------------|
| BROWSE | List namespace contents. |
| READ | View and retrieve objects and their metadata. |
| WRITE | Store, copy, and modify objects. |
| DELETE | Delete objects and versions. |
| PURGE | Permanently remove all versions. |
| SEARCH | Search objects via the Metadata Query API. |
| READ_ACL | View object and bucket ACLs. |
| WRITE_ACL | Modify object and bucket ACLs. |
| CHANGE_OWNER | Change object ownership. |
| PRIVILEGED | Delete objects under retention (privileged delete). |

## Protocols

HCP supports multiple access protocols, each configured independently per namespace:

| Protocol | Use Case |
|----------|----------|
| **S3** | Primary API for modern applications. RESTful, compatible with AWS S3 tools. |
| **REST** | HCP-native HTTP API with additional metadata features. |
| **NFS** | Legacy file system access (mount namespaces as directories). |
| **CIFS/SMB** | Windows file sharing access. |
| **SMTP** | Email ingestion (storing email as objects). |
| **WebDAV** | Web-based file management. |

!!! tip
    Objects stored through any protocol are immediately accessible through all other enabled protocols. The S3 and REST protocols are automatically enabled when you create a namespace via S3.

## Replication

HCP supports **cross-system replication** for data protection across geographically distributed systems.

```mermaid
graph LR
    DC1["HCP System<br/>Data Center 1"] <-->|"Replication Link"| DC2["HCP System<br/>Data Center 2"]
    DC1 <-->|"Replication Link"| DC3["HCP System<br/>Data Center 3"]
```

Key concepts:

- **Replication link** -- a connection between two HCP systems for data synchronization.
- **Active/active** -- both systems accept writes; changes replicate bidirectionally.
- **Failover/failback** -- redirect traffic to a surviving system during outages.
- **Geo-protection** -- data is stored in multiple geographic locations for disaster recovery.

## Metadata Query API

The **Metadata Query API** lets you search for objects based on their metadata. It supports:

- **Object-based queries** -- search current objects by system metadata, custom metadata, ACLs, and content properties using a Lucene-like query language.
- **Operation-based queries** -- search for create, delete, purge, and dispose events for audit trails.

The API returns metadata only (not object data). Results can be paginated and sorted.

### Query Syntax Examples

```
# Find large files in the finance namespace
namespace:finance AND size:[1048576 TO *]

# Find PDFs modified in 2025
contentType:application/pdf AND changeTimeString:[2025-01-01T00:00:00Z TO 2025-12-31T23:59:59Z]

# Find objects with specific custom metadata
customMetadataContent:"department.sales"

# Find objects on hold
hold:true
```

## Authentication

HCP uses a token-based authentication scheme:

| Type | Format | Description |
|------|--------|-------------|
| **HCP native** | `HCP base64(username):md5(password)` | Username is base64-encoded, password is MD5-hashed. |
| **Active Directory** | `AD username:password` | For AD-integrated environments. |

The HCP App wraps this in a JWT-based flow -- see [Authentication](../api/authentication.md) for details on how the API handles credential management.

## Content Classes

**Content classes** define custom metadata schemas for object classification. They map XML elements in custom metadata to named, typed properties that can be:

- Indexed for fast search via the Metadata Query API
- Used as facets for aggregate analysis
- Typed as string, integer, date, or boolean

Content classes are defined at the tenant level and associated with specific namespaces.
