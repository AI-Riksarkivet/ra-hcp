# HCP Platform - Gap Analysis & Implementation TODO

Generated: 2026-03-13

**Required skills for all work:** `fastapi-templates`, `shadcn-svelte-skill`, `hcp-backend`, `hcp-frontend`

---

## Part 1: S3 Gaps (Backend + Frontend)

### 1.1 S3 Bucket CORS (backend: 3 endpoints + frontend: new UI)

**Backend:**
- [ ] `PUT /bucket?cors` - Set bucket CORS configuration
- [ ] `GET /bucket?cors` - Get bucket CORS configuration
- [ ] `DELETE /bucket?cors` - Delete bucket CORS configuration

**Frontend:**
- [ ] Add "CORS" tab to bucket detail page (alongside Objects, Versions, ACL tabs)
- [ ] CORS rules list view showing AllowedOrigins, AllowedMethods, AllowedHeaders, MaxAgeSeconds
- [ ] Add CORS rule form (AllowedOrigins, AllowedMethods checkboxes, AllowedHeaders, MaxAgeSeconds, ExposeHeaders)
- [ ] Edit/delete individual CORS rules
- [ ] "Quick setup" preset for common patterns (e.g. browser upload CORS with PUT + ETag)
- [ ] Link from upload dialog's CORS warning to the CORS config tab

**Backend files:**
- `backend/app/services/storage/protocol.py` - Add method signatures
- `backend/app/services/storage/adapters/_boto3_ops.py` - Implement in Boto3Operations + Boto3Forwarder
- `backend/app/services/storage/adapters/generic_boto3.py` - MinIO override if needed
- `backend/app/api/v1/endpoints/s3/buckets.py` - Add CORS endpoints
- `backend/app/schemas/s3.py` - Add CorsRule, CorsConfiguration schemas
- `backend/mock_server/s3_service.py` - Add mock CORS storage

**Frontend files:**
- `frontend/src/routes/(app)/buckets/[bucket]/+page.svelte` - Add CORS tab
- `frontend/src/routes/(app)/buckets/[bucket]/sections/bucket-cors.svelte` - New CORS management component
- `frontend/src/lib/remote/buckets.remote.ts` - Add get_bucket_cors, put_bucket_cors, delete_bucket_cors

---

### 1.2 S3 Multipart Upload Management (backend: 1 endpoint + frontend: new UI)

**Backend:**
- [ ] `GET /bucket?uploads` - List in-progress multipart uploads

**Frontend:**
- [ ] Add "Uploads" tab to bucket detail page (or section within Objects tab)
- [ ] List in-progress multipart uploads with: key, upload ID, initiated date, size
- [ ] "Abort" button per upload to clean up stale/failed uploads
- [ ] Bulk abort for cleanup
- [ ] Status indicators showing upload age (warning for stale uploads)

**Backend files:**
- `backend/app/services/storage/protocol.py` - Add list_multipart_uploads signature
- `backend/app/services/storage/adapters/_boto3_ops.py` - Implement
- `backend/app/api/v1/endpoints/s3/buckets.py` - Add list uploads endpoint
- `backend/app/schemas/s3.py` - Add MultipartUploadInfo, ListMultipartUploadsResponse
- `backend/mock_server/s3_service.py` - Add mock list

**Frontend files:**
- `frontend/src/routes/(app)/buckets/[bucket]/+page.svelte` - Add Uploads tab
- `frontend/src/routes/(app)/buckets/[bucket]/sections/bucket-uploads.svelte` - New uploads list component
- `frontend/src/lib/remote/buckets.remote.ts` - Add list_multipart_uploads

---

### 1.3 S3 Create Folder (backend: 1 endpoint + frontend: button)

**Backend:**
- [ ] `PUT /folder/` - Create folder (empty object with trailing slash or Content-Type: x-directory)

**Frontend:**
- [ ] Add "Create Folder" button in object browser toolbar (next to "Upload Files")
- [ ] Simple dialog: folder name input, creates empty object with trailing `/`
- [ ] Folder appears immediately in the object browser

**Backend files:**
- `backend/app/api/v1/endpoints/s3/objects.py` - Add create folder endpoint
- `backend/mock_server/s3_service.py` - Handle folder creation

**Frontend files:**
- `frontend/src/routes/(app)/buckets/[bucket]/sections/bucket-object-browser.svelte` - Add Create Folder button
- `frontend/src/routes/(app)/buckets/[bucket]/components/create-folder-dialog.svelte` - New dialog component
- `frontend/src/lib/remote/buckets.remote.ts` - Add create_folder

---

### 1.4 S3 Other Backend Gaps

- [ ] `PUT /object?partNumber&uploadId` (with x-amz-copy-source) - Upload part by copying
- [ ] `POST /` (multipart/form-data) - Browser-based form upload
- [ ] Copy object should also support PUT with `x-amz-copy-source` header
- [ ] Explicit v1 vs v2 listing distinction

*(These are lower priority — no immediate frontend impact)*

---

## Part 2: Frontend Gaps - System-Level Administration

> **Sidebar architecture decision:** Create a new **"System"** sidebar group visible ONLY to `sys-admin` (not tenant-admin). Uses existing `accessLevel === 'sys-admin'` check. This keeps system infrastructure management cleanly separated from tenant administration.

### 2.0 System Sidebar Group + Navigation (prerequisite)
- [ ] Add "System" group to `AppSidebar.svelte` with `accessLevel === 'sys-admin'` guard
- [ ] System sidebar items: Network, Licenses, Nodes, Services, Logs, Health, Support, Replication, Erasure Coding, System Users, System Groups, Tenants
- [ ] Create `system.remote.ts` for system-level API calls
- [ ] Create `+layout.server.ts` guard for `/system/*` routes (sys-admin only)
- [ ] Create system section index page at `/system/+page.svelte` (dashboard overview)

**Frontend files:**
- `frontend/src/lib/components/layout/AppSidebar.svelte` - Add System group
- `frontend/src/lib/remote/system.remote.ts` - New remote functions file
- `frontend/src/routes/(app)/system/+layout.server.ts` - Access guard
- `frontend/src/routes/(app)/system/+page.svelte` - System dashboard/index

---

### 2.1 Network Settings
- [ ] Network settings page showing downstream DNS mode
- [ ] Toggle between ADVANCED and BASIC DNS modes
- [ ] Remote functions: get_network_settings, update_network_settings

**Frontend files:**
- `frontend/src/routes/(app)/system/network/+page.svelte`
- `frontend/src/routes/(app)/system/network/+page.server.ts`

---

### 2.2 License Management
- [ ] View current storage license details (serial, capacity, expiration)
- [ ] View license history table (verbose list)
- [ ] Upload new license key (file upload or text paste)
- [ ] Remote functions: get_licenses, upload_license

**Frontend files:**
- `frontend/src/routes/(app)/system/licenses/+page.svelte`
- `frontend/src/routes/(app)/system/licenses/+page.server.ts`

---

### 2.3 Node Statistics Dashboard
- [ ] Per-node statistics: CPU usage, bandwidth, HTTP connections, volume stats
- [ ] Visual dashboard with charts (LayerChart bar/line charts)
- [ ] Auto-refresh toggle (poll no more than once per hour per docs)
- [ ] Remote functions: get_node_statistics

**Frontend files:**
- `frontend/src/routes/(app)/system/nodes/+page.svelte`
- `frontend/src/routes/(app)/system/nodes/+page.server.ts`

---

### 2.4 Service Statistics Dashboard
- [ ] Per-service statistics: service state, objects examined/serviced/unable
- [ ] Visual dashboard with status indicators and charts
- [ ] Remote functions: get_service_statistics

**Frontend files:**
- `frontend/src/routes/(app)/system/services/+page.svelte`
- `frontend/src/routes/(app)/system/services/+page.server.ts`

---

### 2.5 Log Management
- [ ] View log download status
- [ ] Mark logs with message (text input + submit)
- [ ] Prepare logs for download (date range picker)
- [ ] Download packaged logs (.zip) with progress indication
- [ ] Cancel log download
- [ ] Remote functions: get_log_status, mark_logs, prepare_logs, download_logs, cancel_log_download

**Frontend files:**
- `frontend/src/routes/(app)/system/logs/+page.svelte`
- `frontend/src/routes/(app)/system/logs/+page.server.ts`

---

### 2.6 Health Check Reports
- [ ] View health check report status
- [ ] Prepare health check reports (date range, exactTime toggle, collectCurrent toggle)
- [ ] Download health check reports (node selector, content type)
- [ ] Cancel health check report download
- [ ] Remote functions: get_health_status, prepare_health_report, download_health_report, cancel_health_report

**Frontend files:**
- `frontend/src/routes/(app)/system/health/+page.svelte`
- `frontend/src/routes/(app)/system/health/+page.server.ts`

---

### 2.7 Support Access Credentials
- [ ] View current support credentials (SSH key info)
- [ ] Upload new support SSH key package (.plk file)
- [ ] Remote functions: get_support_credentials, upload_support_credentials

**Frontend files:**
- `frontend/src/routes/(app)/system/support/+page.svelte`
- `frontend/src/routes/(app)/system/support/+page.server.ts`

---

### 2.8 System-Level User Accounts
- [ ] List system-level users in data table
- [ ] View system-level user details
- [ ] Change system-level user password (dialog)
- [ ] Remote functions: get_system_users, get_system_user, change_system_user_password

**Frontend files:**
- `frontend/src/routes/(app)/system/users/+page.svelte`
- `frontend/src/routes/(app)/system/users/+page.server.ts`
- `frontend/src/routes/(app)/system/users/[username]/+page.svelte`
- `frontend/src/routes/(app)/system/users/[username]/+page.server.ts`

---

### 2.9 System-Level Group Accounts
- [ ] List system-level groups in data table
- [ ] View system-level group details
- [ ] Remote functions: get_system_groups, get_system_group

**Frontend files:**
- `frontend/src/routes/(app)/system/groups/+page.svelte`
- `frontend/src/routes/(app)/system/groups/+page.server.ts`

---

### 2.10 Tenant Lifecycle Management
- [ ] List all tenants (for multi-tenant environments)
- [ ] Create new tenant form (name, quota, auth types, initial user/group)
- [ ] Delete tenant (with confirmation)
- [ ] Multi-tenant switcher in sidebar or header
- [ ] Remote functions: list_tenants, create_tenant, delete_tenant

**Frontend files:**
- `frontend/src/routes/(app)/system/tenants/+page.svelte`
- `frontend/src/routes/(app)/system/tenants/+page.server.ts`
- `frontend/src/routes/(app)/system/tenants/components/tenant-create-dialog.svelte`

---

### 2.11 Replication Management (complex)
- [ ] Replication service settings page (GET/POST /services/replication)
- [ ] Replication certificates list/upload/delete UI
- [ ] Replication server certificate download button
- [ ] Replication links list with status indicators
- [ ] Create replication link form (name, type, connection, compression, encryption, priority, failover)
- [ ] Link detail page with:
  - Link info and status
  - Action buttons: failover, failback, suspend, resume, begin/complete recovery
  - Content tab: manage tenants, directories, chained links
  - Candidates tab: browse local/remote eligible items
  - Schedule tab: configure time-based performance levels (HIGH/MEDIUM/LOW)
- [ ] Remote functions: full replication API coverage

**Frontend files:**
- `frontend/src/routes/(app)/system/replication/+page.svelte` - Links list
- `frontend/src/routes/(app)/system/replication/+page.server.ts`
- `frontend/src/routes/(app)/system/replication/[link]/+page.svelte` - Link detail
- `frontend/src/routes/(app)/system/replication/[link]/+page.server.ts`
- `frontend/src/routes/(app)/system/replication/certificates/+page.svelte` - Certificates
- `frontend/src/routes/(app)/system/replication/components/` - Dialogs, forms
- `frontend/src/lib/remote/replication.remote.ts` - Dedicated remote file (too many ops for system.remote.ts)

---

### 2.12 Erasure Coding Management
- [ ] EC topologies list page with status indicators
- [ ] Create EC topology form (name, description, type, links, delay, copy, min size, restore period)
- [ ] Edit/retire/delete EC topology
- [ ] Topology detail page:
  - View eligible tenants (candidates) vs conflicting candidates
  - Add/remove tenants
  - View eligible replication links
- [ ] Remote functions: full EC API coverage

**Frontend files:**
- `frontend/src/routes/(app)/system/erasure-coding/+page.svelte`
- `frontend/src/routes/(app)/system/erasure-coding/+page.server.ts`
- `frontend/src/routes/(app)/system/erasure-coding/[topology]/+page.svelte`
- `frontend/src/routes/(app)/system/erasure-coding/[topology]/+page.server.ts`
- `frontend/src/routes/(app)/system/erasure-coding/components/` - Dialogs, forms

---

## Part 3: Frontend Gaps - Tenant-Level Improvements

### 3.1 Console Security - IP Restrictions
- [ ] Add IP restriction section to `settings-console-security.svelte` (copy from search-security)
- [ ] IP whitelist management using existing `IpListEditor` component
- [ ] IP blacklist management using existing `IpListEditor` component
- [ ] AllowIfInBoth toggle switch
- [ ] Wire ipSettings to save handler

**Frontend files:**
- `frontend/src/routes/(app)/tenant-settings/sections/settings-console-security.svelte`

---

### 3.2 Search Security - IP Restrictions
- [x] Already implemented in `settings-search-security.svelte` (COMPLETE)

---

### 3.3 Chargeback Reports Enhancement
- [ ] Tenant-level chargeback CSV export/download button
- [ ] Namespace-level chargeback CSV export/download button
- [ ] Granularity controls (hour/day/total dropdown)
- [ ] Date range picker for reports

**Frontend files:**
- `frontend/src/routes/(app)/namespaces/[namespace]/sections/ns-chargeback.svelte`
- `frontend/src/routes/(app)/namespaces/+page.svelte`

---

### 3.4 Tenant Statistics Enhancement
- [ ] Historical/trending statistics view with time-series charts
- [ ] Comparison across namespaces

---

## Part 4: Frontend Gaps - Namespace-Level Improvements

### 4.1 Custom Metadata Indexing
- [ ] Full content property mapping UI
- [ ] Annotation exclusion configuration

### 4.2 Namespace Statistics
- [ ] Enhanced statistics dashboard with time-series charts

---

## Implementation Priority

### Phase 1: Quick Wins (low effort, high value)
1. **Console security IP restrictions** - Copy pattern from search-security, IpListEditor exists
2. **Chargeback CSV export** - Client-side CSV generation, add download button
3. **S3 bucket CORS** (backend + frontend) - Follow ACL pattern, add CORS tab to bucket detail
4. **S3 list multipart uploads** (backend + frontend) - One method + Uploads tab
5. **S3 create folder** (backend + frontend) - Simple dialog + button in object browser
6. **System sidebar group** - Prerequisite for all system pages

### Phase 2: Simple System Pages
7. **Network settings page** - 2 operations, simple form
8. **License management page** - GET list + file upload
9. **Support credentials page** - GET info + file upload
10. **System-level user accounts** - List + detail + password change
11. **System-level group accounts** - List + detail (read-only)

### Phase 3: Medium System Pages
12. **Log management page** - 5 operations, date pickers, download flow
13. **Health check reports page** - 4 operations, similar to logs
14. **Node statistics dashboard** - Charts, auto-refresh
15. **Service statistics dashboard** - Status indicators, charts
16. **Tenant lifecycle management** - CRUD + multi-tenant switcher

### Phase 4: Complex Features
17. **Replication management** - Full suite (~30 ops, complex multi-page UI)
18. **Erasure coding management** - (~12 ops, topology visualization)
19. **S3 remaining gaps** - Copy part, form upload, v1 listing
20. **Tenant statistics trending** - Historical data visualization

---

## File Impact Summary

### Backend (S3 gaps only - MAPI is 100%)
- `backend/app/services/storage/protocol.py`
- `backend/app/services/storage/adapters/_boto3_ops.py`
- `backend/app/services/storage/adapters/generic_boto3.py`
- `backend/app/services/storage/adapters/hcp.py`
- `backend/app/api/v1/endpoints/s3/buckets.py`
- `backend/app/api/v1/endpoints/s3/multipart.py`
- `backend/app/api/v1/endpoints/s3/objects.py`
- `backend/app/schemas/s3.py`
- `backend/mock_server/s3_service.py`

### Frontend - New System Section
- `frontend/src/lib/components/layout/AppSidebar.svelte` - Add System sidebar group
- `frontend/src/lib/remote/system.remote.ts` - System admin remote functions
- `frontend/src/lib/remote/replication.remote.ts` - Replication remote functions
- `frontend/src/routes/(app)/system/+layout.server.ts` - sys-admin access guard
- `frontend/src/routes/(app)/system/+page.svelte` - System dashboard
- `frontend/src/routes/(app)/system/network/` - Network settings (2 files)
- `frontend/src/routes/(app)/system/licenses/` - License management (2 files)
- `frontend/src/routes/(app)/system/nodes/` - Node statistics (2 files)
- `frontend/src/routes/(app)/system/services/` - Service statistics (2 files)
- `frontend/src/routes/(app)/system/logs/` - Log management (2 files)
- `frontend/src/routes/(app)/system/health/` - Health check reports (2 files)
- `frontend/src/routes/(app)/system/support/` - Support credentials (2 files)
- `frontend/src/routes/(app)/system/users/` - System users (4 files)
- `frontend/src/routes/(app)/system/groups/` - System groups (2 files)
- `frontend/src/routes/(app)/system/tenants/` - Tenant lifecycle (3 files)
- `frontend/src/routes/(app)/system/replication/` - Replication (~6 files)
- `frontend/src/routes/(app)/system/erasure-coding/` - Erasure coding (~4 files)

### Frontend - S3 Enhancements
- `frontend/src/routes/(app)/buckets/[bucket]/+page.svelte` - Add CORS + Uploads tabs
- `frontend/src/routes/(app)/buckets/[bucket]/sections/bucket-cors.svelte` - New CORS component
- `frontend/src/routes/(app)/buckets/[bucket]/sections/bucket-uploads.svelte` - New uploads component
- `frontend/src/routes/(app)/buckets/[bucket]/sections/bucket-object-browser.svelte` - Add Create Folder button
- `frontend/src/routes/(app)/buckets/[bucket]/components/create-folder-dialog.svelte` - New dialog
- `frontend/src/lib/remote/buckets.remote.ts` - Add CORS, list uploads, create folder functions

### Frontend - Tenant Improvements
- `frontend/src/routes/(app)/tenant-settings/sections/settings-console-security.svelte` - Add IP restrictions
- `frontend/src/routes/(app)/namespaces/[namespace]/sections/ns-chargeback.svelte` - Add CSV export
- `frontend/src/routes/(app)/namespaces/+page.svelte` - Add CSV export

### Mock Server
- `backend/mock_server/s3_service.py` - CORS storage, list uploads, folder creation
- `backend/mock_server/mapi_state.py` - System-level route dispatching (/network, /storage/licenses, etc.)
