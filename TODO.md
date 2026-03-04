## Active Tasks

1. **Implement bucket sync** — Build intra-tenant and cross-tenant sync endpoints backed by Redis Streams, as described in `plan_sync.md`. Includes transform pipeline, webhook support, atomic mode, and job status polling.

2. **Heavy refactor (phase 2)** — Remaining DRY work: save/dirty tracking composable (used 15+ times across settings, user detail, namespace detail), table abstraction component, create dialog pattern extraction. Phase 1 done (StatCard, DeleteConfirmDialog, BulkDeleteDialog, SearchToolbar).

3. **Build HCP Metadata Query API** — Backend has indexing config but no query endpoints. Need: `POST .../query` (object-based), `POST .../operationQuery` (operation/audit), Pydantic schemas, mock handlers, mock fixtures. Could power activity logs on overview page. See `docs/hcp_docs/hcp_search.md`.

4. **Multi-tenant login** — Add feature to manage multiple tenants, swap between them in the frontend, and view buckets across tenants. Good scaffold for the sync feature (task 1).

5. adding icon tags for certain serice (lakefs) or NFS. in bucket and namesapce view


5. improve auth with better auth?
6. missing instrucions to connect nfs and if we are using auth for nfs
7. how sign objects and generate auth tokens from api? s3?
8. missing better logging in backend who sent and aaked for what and what was reurned , fastspi skills
9. are we missing compileroptions async true? https://github.com/AI-Riksarkivet/hcp/blob/main/frontend/svelte.config.js , check svelt5 skills
---

## Done

- ~~**Improve overview page**~~ — Compact stat cards (objects, storage+quota, namespaces, users), chargeback activity table with I/O totals, quota progress bar.
- ~~**Add logs and better statistics**~~ — Chargeback/I/O data surfaced on overview. HCP has no queryable log API (only bulk download). Operation-based queries via Metadata Query API could fill the gap (see task 3).
- ~~**Fix layouting + add tooltips in users/groups**~~ — Role tooltips on user detail page (ADMINISTRATOR, SECURITY, MONITOR, COMPLIANCE).
- ~~**Add tooltips and explanations for namespace settings**~~ — Tooltips for protocols, hash scheme, compliance, versioning, search on namespace detail page.
- ~~**Understand search and versioning settings**~~ — Researched HCP Metadata Query API (object-based + operation-based queries). Versioning controls object version retention. Backend can configure indexing but query endpoints not yet built.
- ~~**Investigate tenant admin capabilities**~~ — Settings page fully editable: contact info, namespace defaults, tenant permissions with save/dirty tracking.
- ~~**Heavy refactor (phase 1)**~~ — Extracted reusable Svelte 5 components: `StatCard`, `DeleteConfirmDialog`, `BulkDeleteDialog`, `SearchToolbar`. Refactored namespaces, buckets, overview, and user detail pages.

---

## Backlog

- fix docs (zensical)
- better grouping of routes — tenant admin, hcp admin, etc. What are the boundaries?
- ~~Remove unused favicon.svg, index.ts, is-mobile hook; remove mobile sidebar support~~ done
- ~~utils.ts and cn.ts are used by 80+ UI components — keep~~ verified
- ~~static/ is the correct SvelteKit convention (not public/)~~ verified
- use remote functions for data loading. update skills to utilize it svelte-skills-kit
- add pr skills and force pr and block to main if not force
- ~~vsx https://open-vsx.org/extension/FastAPILabs/fastapi-vscode~~ done (added to .vscode/extensions.json)
- playwright for testing and also storybook
- use std@expect for testing (jest) from JSR
- ~~refactor: use SvelteKit $env/dynamic/private + centralized $lib/server/env.ts instead of process.env~~ done
- deno otel https://docs.deno.com/runtime/fundamentals/open_telemetry/, https://deno.com/blog/zero-config-debugging-deno-opentelemetry
- ~~look over svelte code and be very svelte 5 and sveltekit 2 idiomatic~~ done (snippets, remote functions, $props, $derived, $bindable used throughout)
- backend with namespaces
- buckets are under tenants, see minio UI for example
- ~~fix user and groups~~ done
- fix error handling in backend 500 and how to forward to frontend
- test so multipart upload is really working in frontend and in backend, and that it is atomic
- fix access control
- handle duplicate uploads?
- test how openfga would work
- fix nfs support
- fix what different users can see and do
- fix so we use superforms
- fix forms and add more padding to modals
- ~~fix dashboard~~ done (overview page redesigned)
- add more metadata of the uploaded file — a meta tab that opens from right sidebar, about the file, who uploaded, etc.
- search should be done on key, please verify
- add support for sync between 1:1 buckets between tenants (must auth for the other tenant) — can we use redis as layer between?
- add middleware
- modal for preview viewer for files in bucket is too big
- add support for viewing lance and parquet — see HF dataset viewer as example or lance viewer
- dagger build system
- dockerfiles
- helm chart
- use in kubernetes — s3fuse? or PVC static or NFS Subdir External Provisioner (dynamic PVCs)
- special marker if a bucket is lakefs
- mock more of backend but also a dev state for frontend
- research best practices for test suite with deno and sveltekit
- utilize more page and layout utils of sveltekit! and utilize sveltekit more in general
- use figma for designing UI
- ~~check usage of snippets and make UI composable~~ done (StatCard uses snippets, all new components use $props/$bindable)
- skills: figma, the other libs in frontend and backend we are using
- Playwright and vitest and storybook for testing
- ~~dotenx for .env~~ not needed (Deno 2 loads .env natively, SvelteKit has $env modules)
- ~~Clean up makefile~~ done
- ~~Remove old S3 shell tests (tests/s3, .aws)~~ done
- ~~Add prettier + prettier-plugin-svelte for .svelte formatting~~ done
- ~~Add Claude Code and git pre-commit hooks for auto-formatting~~ done
- ~~Add make fmt/lint/check targets~~ done
- ~~Format entire codebase (ruff, deno fmt, prettier)~~ done
- ~~Fix all deno lint and ruff lint issues~~ done
- ~~Add all VS Code extension recommendations~~ done
