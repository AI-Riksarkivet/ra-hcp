# HCP Admin Console — New Feature Plan

> Covers all missing tenant-admin functionality. System-admin endpoints are out of scope.

---

## Current State

The frontend covers core CRUD for namespaces, users, buckets, objects, search, and basic tenant settings. Below is everything that the backend supports but the frontend does not yet expose.

---

## Phase 1: Namespace Detail Expansion

**Where:** `/namespaces/[namespace]` — extend the existing detail page with new sections/tabs.

**Why:** Namespaces are the central management unit in HCP. Compliance, retention, and per-namespace statistics are essential for any archival or regulatory use case. Admins currently have to use the native HCP console or raw API calls for these.

### 1.1 Per-Namespace Statistics

**Endpoints:**
- `GET /tenants/{tenant}/namespaces/{ns}/statistics` — object count, storage used, ingested volume, shred count
- `GET /tenants/{tenant}/namespaces/{ns}/chargebackReport` — time-series usage with reads, writes, deletes, bytes in/out

**Implementation:**
- Add `get_ns_statistics` and `get_ns_chargeback` queries to `namespaces.remote.ts`
- New section on the namespace detail page with stat cards (reuse `StatCard` component)
- Show: object count, storage used, ingested volume
- Optional: chargeback breakdown table for time-range usage

**Complexity:** Low — read-only, reuses existing StatCard and formatBytes patterns.

### 1.2 Compliance Settings

**Endpoints:**
- `GET /tenants/{tenant}/namespaces/{ns}/complianceSettings` — WORM rules
- `POST /tenants/{tenant}/namespaces/{ns}/complianceSettings` — update WORM rules

**Fields:** `retentionDefault`, `minimumRetentionAfterInitialUnspecified`, `shreddingDefault`, `customMetadataChanges`, `dispositionEnabled`

**Implementation:**
- Add `get_ns_compliance` query and `update_ns_compliance` command to `namespaces.remote.ts`
- New "Compliance" card/section on namespace detail page
- Form with: retention default (input), shredding default (select/switch), custom metadata changes policy (select), disposition toggle (switch)
- Follow the existing settings pattern: `$state` local values, `$effect` sync, `$derived` dirty check, `SaveButton`

**Why it matters:** Compliance controls whether objects can be deleted or modified. This is the core regulatory feature of HCP — without it, admins can't configure WORM policies from the console.

**Complexity:** Medium — form with multiple fields, needs careful dirty tracking.

### 1.3 Retention Classes

**Endpoints:**
- `GET /tenants/{tenant}/namespaces/{ns}/retentionClasses` — list names
- `PUT /tenants/{tenant}/namespaces/{ns}/retentionClasses` — create (name, value, description, allowDisposition)
- `GET /tenants/{tenant}/namespaces/{ns}/retentionClasses/{name}` — get details
- `POST /tenants/{tenant}/namespaces/{ns}/retentionClasses/{name}` — update
- `DELETE /tenants/{tenant}/namespaces/{ns}/retentionClasses/{name}` — delete

**Implementation:**
- Add retention class queries/commands to `namespaces.remote.ts`
- New "Retention Classes" section on namespace detail page
- DataTable listing retention classes (name, value/duration, description, disposition)
- Create dialog: name, value (duration input), description, allow disposition toggle
- Row actions: edit (dialog), delete (confirm dialog)
- Reuse existing `DeleteConfirmDialog` and `DataTableActions` patterns

**Why it matters:** Retention classes define named policies (e.g. "7-year-hold", "permanent") applied to objects. They work with compliance settings to enforce how long data must be kept.

**Complexity:** Medium — full CRUD with DataTable, but follows established patterns.

### 1.4 Protocol Configuration

**Endpoints:**
- `GET /tenants/{tenant}/namespaces/{ns}/protocols/{protocol}` — get individual protocol config
- `POST /tenants/{tenant}/namespaces/{ns}/protocols/http` — update HTTP/S3 settings
- `POST /tenants/{tenant}/namespaces/{ns}/protocols/cifs` — update CIFS/SMB settings
- `POST /tenants/{tenant}/namespaces/{ns}/protocols/nfs` — update NFS settings
- `POST /tenants/{tenant}/namespaces/{ns}/protocols/smtp` — update SMTP settings

**Implementation:**
- Add `get_ns_protocol` query and `update_ns_protocol_*` commands to `namespaces.remote.ts` (HTTP, CIFS, NFS, SMTP)
- Expand the existing protocol toggles on namespace detail into clickable cards/dialogs
- Each protocol gets its own settings dialog:
  - **HTTP:** REST enabled, HS3 (S3) enabled, WebDAV enabled, auth requirements, AD SSO
  - **CIFS:** case forcing (upper/lower/disabled), case sensitivity, auth required
  - **NFS:** UID, GID mapping
  - **SMTP:** email format (.eml/.mbox), email location, separate attachments
- All dialogs include IP restrictions (allowAddresses / denyAddresses)

**Why it matters:** Protocol configuration controls how data is accessed. Currently the UI only shows on/off toggles — admins need the detailed settings (auth, WebDAV, case sensitivity) to properly configure access.

**Complexity:** Medium-High — four separate protocol forms, each with different fields. Consider a shared layout with protocol-specific content.

### 1.5 Custom Metadata Indexing

**Endpoints:**
- `GET /tenants/{tenant}/namespaces/{ns}/customMetadataIndexingSettings`
- `POST /tenants/{tenant}/namespaces/{ns}/customMetadataIndexingSettings`

**Fields:** `contentClasses` (list of content class names), `fullIndexingEnabled`, `excludedAnnotations`

**Implementation:**
- Add queries/commands to `namespaces.remote.ts`
- New "Indexing" card on namespace detail page
- Form: full indexing toggle (switch), content classes (multi-select or tag input referencing available content classes), excluded annotations (text input)
- SaveButton with dirty tracking

**Why it matters:** Controls what metadata is searchable via the query/search page. Without this, admins can't tune which fields are indexed.

**Complexity:** Low-Medium — simple form, but content class multi-select needs the content classes list from Phase 4.

### 1.6 Namespace CORS

**Endpoints:**
- `GET /tenants/{tenant}/namespaces/{ns}/cors` — raw XML
- `PUT /tenants/{tenant}/namespaces/{ns}/cors` — set
- `DELETE /tenants/{tenant}/namespaces/{ns}/cors` — remove

**Implementation:**
- Add queries/commands to `namespaces.remote.ts`
- New "CORS" card on namespace detail page
- Textarea/code editor for CORS XML configuration
- Save and Delete buttons
- Consider a structured form (allowed origins, methods, headers) that builds the XML, with a raw XML toggle

**Why it matters:** Required for browser-based S3 access (e.g. JavaScript apps uploading directly to HCP).

**Complexity:** Low — essentially a textarea with save/delete. Higher if building a structured CORS editor.

### 1.7 Replication Collision Settings

**Endpoints:**
- `GET /tenants/{tenant}/namespaces/{ns}/replicationCollisionSettings`
- `POST /tenants/{tenant}/namespaces/{ns}/replicationCollisionSettings`

**Fields:** `action` (MOVE or RENAME), `deleteDays`, `deleteEnabled`

**Implementation:**
- Add queries/commands to `namespaces.remote.ts`
- Small card on namespace detail page
- Form: action select (MOVE/RENAME), delete enabled toggle, delete days input
- SaveButton with dirty tracking

**Why it matters:** Defines what happens when two replicated HCP systems write the same object simultaneously. Misconfiguration can cause data loss.

**Complexity:** Low — three fields, simple form.

---

## Phase 2: Bucket Browser Enhancements

**Where:** `/buckets/[bucket]` — extend the existing object browser.

**Why:** The bucket browser currently supports listing, deleting, and downloading via presigned URLs. Adding upload, copy, metadata viewing, versioning, and ACLs makes it a complete object management tool.

### 2.1 File Upload

**Endpoint:** `POST /buckets/{bucket}/objects/{key}` — multipart form upload

**Implementation:**
- Add `upload_object` command to `buckets.remote.ts`
- Upload button in the bucket toolbar (next to existing actions)
- File picker dialog with drag-and-drop zone
- Show upload progress (if possible via fetch streaming)
- After upload, invalidate object list query
- Support uploading into the current prefix (folder)

**Why it matters:** Currently users can only download from the browser. Upload is the most requested missing feature for a bucket browser.

**Complexity:** Medium — file handling, progress indication, prefix-awareness.

### 2.2 Object Metadata Panel

**Endpoint:** `HEAD /buckets/{bucket}/objects/{key}` — returns content_length, content_type, etag, last_modified

**Implementation:**
- Add `head_object` query to `buckets.remote.ts`
- Click on an object row → slide-out panel or dialog showing metadata
- Display: file name, size (formatBytes), content type, ETag, last modified
- Include existing download/delete actions in the panel

**Why it matters:** Users currently have no way to inspect object details without downloading. Metadata is essential for debugging and verification.

**Complexity:** Low — single read-only endpoint, simple UI panel.

### 2.3 Copy Object

**Endpoint:** `POST /buckets/{bucket}/objects/{key}/copy` — body: `{ source_bucket, source_key }`

**Implementation:**
- Add `copy_object` command to `buckets.remote.ts`
- "Copy" action in the object row dropdown (DataTableActions)
- Dialog: destination bucket (select from bucket list), destination key (pre-filled, editable)
- After copy, invalidate destination bucket's object list

**Why it matters:** Copy is needed for reorganizing data, moving objects between namespaces/buckets, and creating backups.

**Complexity:** Low-Medium — dialog with bucket selector, but straightforward.

### 2.4 Bucket Versioning

**Endpoints:**
- `GET /buckets/{bucket}/versioning` — status (Enabled/Suspended/not set)
- `PUT /buckets/{bucket}/versioning` — set status to "Enabled" or "Suspended"

**Implementation:**
- Add `get_bucket_versioning` query and `set_bucket_versioning` command to `buckets.remote.ts`
- Show versioning status badge on the bucket detail page header
- Settings dialog or inline toggle to enable/suspend versioning

**Why it matters:** Versioning keeps historical copies of objects. It's a key data protection feature.

**Complexity:** Low — simple toggle with two states.

### 2.5 Bucket & Object ACLs

**Endpoints:**
- `GET /buckets/{bucket}/acl` — owner + grants list
- `PUT /buckets/{bucket}/acl` — set ACL policy
- `GET /buckets/{bucket}/objects/{key}/acl` — per-object ACL
- `PUT /buckets/{bucket}/objects/{key}/acl` — set per-object ACL

**ACL Model:** Owner (ID, DisplayName) + Grants (Grantee + Permission: FULL_CONTROL, READ, WRITE, READ_ACP, WRITE_ACP)

**Implementation:**
- Add ACL queries/commands to `buckets.remote.ts`
- Bucket-level: "ACL" tab or section on bucket detail page showing owner + grants table
- Object-level: ACL section in the object metadata panel (2.2)
- Edit: dialog with grant list (add/remove grantees, select permissions)

**Why it matters:** ACLs control who can read/write specific resources. Required for multi-user environments.

**Complexity:** Medium — ACL grant editor is non-trivial, needs a good UX for adding grantees.

---

## Phase 3: Tenant Settings Expansion

**Where:** `/settings` — extend the existing settings page with new cards.

**Why:** The settings page currently shows contact info, permissions, and namespace defaults. The missing settings (security, email, CORS, service plans) are needed for full tenant administration.

### 3.1 Console Security

**Endpoints:**
- `GET /tenants/{tenant}/consoleSecurity`
- `POST /tenants/{tenant}/consoleSecurity`

**Fields:** Password policies (min length, character requirements, reuse depth), account lockout (attempts, cooldown, auto-unlock), session timeout, login message, IP restrictions.

**Implementation:**
- Add `get_console_security` query and `update_console_security` command to `tenant-info.remote.ts`
- New card on settings page: "Console Security"
- Subsections: Password Policy (inputs for min length, character counts, reuse), Account Lockout (attempts, cooldown, auto-unlock duration), Session (inactive timeout), Login Message (textarea)
- Follow existing settings card pattern with SaveButton

**Why it matters:** Controls how users authenticate. Password policies and lockout rules are security fundamentals.

**Complexity:** Medium — many fields, but all simple inputs/numbers. Consider grouping into collapsible subsections.

### 3.2 Email Notifications

**Endpoints:**
- `GET /tenants/{tenant}/emailNotification`
- `POST /tenants/{tenant}/emailNotification`

**Fields:** `enabled`, `emailTemplate` (from, subject, body), `recipients` list (address, importance, severity, type)

**Implementation:**
- Add queries/commands to `tenant-info.remote.ts`
- New card: "Email Notifications"
- Enable toggle, template fields (from, subject, body inputs), recipients table (address, importance select, severity select)
- Add/remove recipients inline

**Why it matters:** Alerts on quota warnings, replication failures, and other events. Without this, admins get no proactive notifications.

**Complexity:** Medium — nested recipients list with add/remove.

### 3.3 Search Security

**Endpoints:**
- `GET /tenants/{tenant}/searchSecurity`
- `POST /tenants/{tenant}/searchSecurity`

**Fields:** `ipSettings` (allowAddresses, denyAddresses, allowIfInBothLists)

**Implementation:**
- Add queries/commands to `tenant-info.remote.ts`
- New card: "Search Security"
- IP allow/deny list editor (tag-style input for IP addresses), toggle for allowIfInBothLists
- SaveButton

**Why it matters:** Controls which IPs can access the metadata query API. Important for network security.

**Complexity:** Low — IP list is the only content. Consider a shared `IpSettingsEditor` component (reusable in protocol and console security forms).

### 3.4 Tenant CORS

**Endpoints:**
- `GET /tenants/{tenant}/cors`
- `PUT /tenants/{tenant}/cors`
- `DELETE /tenants/{tenant}/cors`

**Implementation:**
- Add queries/commands to `tenant-info.remote.ts`
- New card: "CORS Configuration"
- Same pattern as namespace CORS (1.6) — textarea for XML, save/delete
- Shared component with namespace CORS if structured editor is built

**Why it matters:** Tenant-wide CORS defaults for browser-based S3 access.

**Complexity:** Low — same as 1.6.

### 3.5 Service Plans (Read-Only)

**Endpoints:**
- `GET /tenants/{tenant}/availableServicePlans` — list of plan names
- `GET /tenants/{tenant}/availableServicePlans/{name}` — plan details (name, description)

**Implementation:**
- Add `get_service_plans` query to `tenant-info.remote.ts`
- New card: "Available Service Plans"
- Simple list/table of plan names with descriptions
- Read-only — no edit needed (plans are defined at system level)

**Why it matters:** Shows which storage tiers are available when creating namespaces. Currently admins have to guess or check the native HCP console.

**Complexity:** Very low — read-only list.

---

## Phase 4: Group Accounts

**Where:** `/users` page — add a "Groups" tab alongside the existing user list.

**Why:** Groups assign shared permissions to multiple users. The backend and remote functions partially exist (`get_groups`, `create_group` in `users.remote.ts`) but there's no UI.

### 4.1 Group List & CRUD

**Endpoints:**
- `GET /tenants/{tenant}/groupAccounts` — list
- `PUT /tenants/{tenant}/groupAccounts` — create (groupname, externalGroupID, roles)
- `GET /tenants/{tenant}/groupAccounts/{name}` — get details
- `POST /tenants/{tenant}/groupAccounts/{name}` — update (roles, allowNamespaceManagement)
- `DELETE /tenants/{tenant}/groupAccounts/{name}` — delete

**Roles:** ADMINISTRATOR, COMPLIANCE, MONITOR, SECURITY, SERVICE, SEARCH

**Implementation:**
- Extend `users.remote.ts` with `get_group`, `update_group`, `delete_group` commands
- Add tab switcher on `/users` page: "Users" | "Groups" (or use a URL param)
- Groups tab: DataTable with columns (name, roles as badges, namespace management toggle)
- Create dialog: group name, external group ID, role checkboxes (same pattern as user creation)
- Row actions: edit, delete
- Detail page at `/users/groups/[groupname]` or inline expansion

**Why it matters:** Without group management, admins must set permissions individually on every user. Groups are the standard way to manage access at scale.

**Complexity:** Medium — follows user CRUD patterns closely. The DataTable, create dialog, and actions are all established patterns.

### 4.2 Group Data Access Permissions

**Endpoints:**
- `GET /tenants/{tenant}/groupAccounts/{name}/dataAccessPermissions`
- `POST /tenants/{tenant}/groupAccounts/{name}/dataAccessPermissions`

**Permissions per namespace:** BROWSE, READ, WRITE, DELETE, PURGE, SEARCH, PRIVILEGED, READ_ACL, WRITE_ACL, CHOWN

**Implementation:**
- Add group permission queries/commands to `users.remote.ts`
- Group detail page (or dialog): namespace permissions table
- Same pattern as user permissions in `/users/[username]` — DataTable with namespace name + permission badges
- Edit dialog: namespace selector + permission checkboxes

**Why it matters:** Groups without permissions are useless. This completes the group management feature.

**Complexity:** Medium — mirrors existing user permission patterns.

---

## Phase 5: Content Classes

**Where:** New route `/content-classes` or section in `/settings`.

**Why:** Content classes define metadata schemas for objects. They're used by the indexing system to know which fields to extract and make searchable. Without managing them, admins can't configure custom metadata search.

### 5.1 Content Class CRUD

**Endpoints:**
- `GET /tenants/{tenant}/contentClasses` — list names
- `PUT /tenants/{tenant}/contentClasses` — create (name, contentProperties, namespaces)
- `GET /tenants/{tenant}/contentClasses/{name}` — get details
- `POST /tenants/{tenant}/contentClasses/{name}` — update
- `DELETE /tenants/{tenant}/contentClasses/{name}` — delete

**Content Property Model:** `{ name, expression (XPath/JSONPath), type, multivalued, format }`

**Implementation:**
- New `content-classes.remote.ts` with full CRUD queries/commands
- Add "Content Classes" to the sidebar under Tenant group
- New route `/content-classes` with DataTable (name, property count, assigned namespaces)
- Create/edit dialog: name, content properties list (add/remove rows with name, expression, type select, multivalued toggle), namespace assignment (multi-select)
- Row actions: edit, delete

**Why it matters:** Content classes power the metadata search system. They define what custom metadata gets indexed and how. This bridges the gap between namespace indexing settings (1.5) and the search page.

**Complexity:** Medium-High — the content property editor (dynamic list of rows with multiple fields) is the most complex form in this plan.

---

## Shared Components to Build

Several features share common UI patterns. Building these as reusable components reduces duplication:

| Component | Used By | Description |
|---|---|---|
| `IpSettingsEditor` | Console security (3.1), search security (3.3), all protocol forms (1.4) | Allow/deny IP list editor with tag-style inputs |
| `CorsEditor` | Namespace CORS (1.6), tenant CORS (3.4) | Textarea or structured CORS XML editor |
| `PermissionCheckboxGrid` | Group permissions (4.2), user permissions (existing) | Namespace × permission matrix |
| `FileDropZone` | Upload (2.1) | Drag-and-drop file upload area |

---

## Implementation Order & Dependencies

```
Phase 1.1 (ns stats)          ──► no deps, start here
Phase 1.2 (compliance)        ──► no deps
Phase 1.7 (repl collision)    ──► no deps
Phase 1.3 (retention classes) ──► benefits from 1.2 being done first
Phase 2.2 (object metadata)   ──► no deps
Phase 2.1 (upload)            ──► no deps
Phase 2.4 (versioning)        ──► no deps
Phase 3.5 (service plans)     ──► no deps (read-only)
Phase 3.3 (search security)   ──► build IpSettingsEditor
Phase 3.1 (console security)  ──► reuses IpSettingsEditor
Phase 1.4 (protocols)         ──► reuses IpSettingsEditor
Phase 3.2 (email notif)       ──► no deps
Phase 1.6 (ns CORS)           ──► build CorsEditor
Phase 3.4 (tenant CORS)       ──► reuses CorsEditor
Phase 4.1 (groups CRUD)       ──► no deps
Phase 4.2 (group perms)       ──► needs 4.1
Phase 2.3 (copy object)       ──► no deps
Phase 2.5 (ACLs)              ──► no deps
Phase 1.5 (indexing)          ──► benefits from Phase 5
Phase 5.1 (content classes)   ──► no deps but most complex form
```

**Suggested sprint grouping:**

1. **Quick wins** (low complexity, high value): 1.1, 1.7, 2.2, 2.4, 3.5
2. **Core compliance**: 1.2, 1.3
3. **Bucket operations**: 2.1, 2.3
4. **Security & settings**: 3.1, 3.2, 3.3 (build IpSettingsEditor first)
5. **CORS**: 1.6, 3.4 (build CorsEditor)
6. **Protocols**: 1.4
7. **Groups**: 4.1, 4.2
8. **Content classes & indexing**: 5.1, 1.5
9. **ACLs**: 2.5

---

## Technical Notes

- **Remote functions pattern:** All new API calls follow the `query()` / `command()` pattern in `.remote.ts` files. Queries auto-refetch reactively. Commands use `.updates(queryRef)` to invalidate caches.
- **State management:** Local `$state` for form values, `$effect` to sync from server, `$derived` for dirty checks. `nsSyncVersion` counter pattern for re-syncing after saves.
- **Component library:** All UI uses shadcn-svelte (Button, Input, Dialog, Card, Badge, Switch, Checkbox, Select, DataTable). No raw HTML elements.
- **Error handling:** `ErrorBanner` for form errors, `toast` for success/failure notifications.
- **Skeletons:** `TableSkeleton` and `CardSkeleton` for loading states with `{#await}` blocks.
