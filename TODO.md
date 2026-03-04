## Active Tasks

1. **Implement bucket sync** — Build intra-tenant and cross-tenant sync endpoints backed by Redis Streams, as described in `plan_sync.md`. Includes transform pipeline, webhook support, atomic mode, and job status polling.

2. **Improve overview page** — Show more useful/accurate data on the tenant overview. Surface real statistics from the HCP backend (object counts, storage used per namespace, quota usage). Make the overview a proper dashboard.

3. **Add logs and better statistics** — Pull HCP system logs and richer statistics into the overview page. Show namespace-level breakdowns, ingress/egress data, chargeback info, and recent activity.

4. **Fix layouting + add tooltips in users/groups** — Improve spacing and layout in the users & groups list page and user detail page. Add tooltips or a description panel in `/users/<user>` to explain what each role checkbox means (ADMINISTRATOR, SECURITY, MONITOR, COMPLIANCE).

5. **Add tooltips and explanations for namespace settings** — In namespace detail, explain what each field/setting means (S3 optimized vs NFS, CIFS, SMTP protocols, hash schemes, compliance modes, etc.). Add inline help or a side panel with descriptions.

6. **Understand search and versioning settings** — Investigate what "search enabled" and "versioning enabled" actually do in HCP. Determine whether these are useful to expose in the frontend or if they should be hidden. Document findings.

7. **Investigate tenant admin capabilities** — The Settings page in the navbar currently shows read-only tenant settings. Understand from the backend what a tenant admin can actually change (permissions, namespace defaults, contact info, email notification, security settings). Either make the settings page editable or clarify what's possible.

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
- look over svelte code and be very svelte 5 and sveltekit 2 idiomatic — use snippets, remote functions, reactivity, stores, context API. Check if we are using routing and pages [id] in sveltekit 2
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
- fix dashboard
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
- check usage of snippets and make UI composable
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
