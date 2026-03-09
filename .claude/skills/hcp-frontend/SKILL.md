---
name: hcp-frontend
description: >
  HCP frontend design patterns, component conventions, and architecture guide.
  Use when: writing Svelte components, adding features, refactoring, creating
  pages, working with remote functions, settings forms, dialogs, or any
  frontend code in this project.
---

# HCP Frontend — Patterns & Conventions

## Stack

- **SvelteKit 2** + **Svelte 5** (runes mode only)
- **shadcn-svelte** component library (Bits UI primitives)
- **Deno** as runtime + package manager
- **Tailwind CSS** for styling
- Quality: `make quality` runs deno fmt/lint + prettier + svelte-check

## Project Layout

```
frontend/src/
├── lib/
│   ├── components/ui/       # Reusable components (shadcn + custom)
│   ├── utils/               # Composables and helpers
│   ├── constants.ts         # Enums, role lists, shared constants
│   ├── *.remote.ts          # Remote functions (query/command)
│   └── tenant-info.remote.ts, users.remote.ts, etc.
├── routes/
│   ├── (app)/               # Authenticated app routes
│   │   ├── namespaces/      # Namespace list + detail pages
│   │   ├── buckets/         # S3 bucket pages
│   │   ├── users/           # User + group pages
│   │   ├── settings/        # Tenant settings
│   │   └── ...
│   └── login/
```

## Remote Functions

All API calls use SvelteKit remote functions in `*.remote.ts` files.

```typescript
// Read data (auto-cached, reactive)
export const get_thing = query(schema, async (params) => { ... });

// Mutate data
export const update_thing = command(schema, async (params) => { ... });
```

**In components:**
```svelte
let data = $derived(get_thing({ tenant, name }));
let current = $derived(data?.current as Thing);
```

**Mutations refresh queries:**
```typescript
await update_thing({ tenant, body }).updates(data);
```

## Settings Form Pattern

All settings/config forms follow this exact pattern using `useSave`:

```svelte
<script lang="ts">
  import SaveButton from '$lib/components/ui/save-button.svelte';
  import { useSave } from '$lib/utils/use-save.svelte.js';

  // 1. Query the data
  let data = $derived(get_something({ tenant }));
  let current = $derived((data?.current ?? {}) as SomeType);

  // 2. Create saver
  const saver = useSave({
    successMsg: 'Settings updated',
    errorMsg: 'Failed to update settings',
  });

  // 3. Local editable state
  let localField = $state('');

  // 4. Sync from server (re-runs on data change OR after save)
  $effect(() => {
    const c = current;
    void saver.syncVersion;     // <- triggers re-sync after save
    localField = c.field ?? '';
  });

  // 5. Dirty check
  let dirty = $derived(localField !== (current.field ?? ''));
</script>

<!-- 6. SaveButton with inline save logic -->
<SaveButton
  {dirty}
  saving={saver.saving}
  onclick={() =>
    saver.run(async () => {
      if (!data) return;
      await update_something({ tenant, body: { field: localField } })
        .updates(data);
    })}
/>
```

**Key rules:**
- `useSave` handles saving state, syncVersion increment, and toast messages
- The `$effect` MUST read `void saver.syncVersion` to re-sync after save
- The save logic goes inline in the `onclick` callback, NOT in a separate function
- Use `$state` for editable fields, `$derived` for dirty checks and query results

## Dialog Pattern

All create/edit dialogs use `FormDialog`:

```svelte
<script lang="ts">
  import FormDialog from '$lib/components/ui/form-dialog.svelte';
  import { toast } from 'svelte-sonner';

  let { open = $bindable(false) }: { open: boolean } = $props();
  let error = $state('');
  let loading = $state(false);

  async function handleSubmit(e: SubmitEvent) {
    e.preventDefault();
    loading = true;
    error = '';
    try {
      await create_thing({ ... }).updates(queryData);
      toast.success('Created successfully');
      open = false;
    } catch (err) {
      error = err instanceof Error ? err.message : 'Failed';
    } finally {
      loading = false;
    }
  }
</script>

<FormDialog bind:open title="Create Thing" {loading} {error} onsubmit={handleSubmit}>
  <!-- form fields here -->
</FormDialog>
```

## Reusable Components

Always check these before building new UI:

| Component | Import | Use for |
|---|---|---|
| `SaveButton` | `$lib/components/ui/save-button.svelte` | Settings form save (dirty + loading) |
| `FormDialog` | `$lib/components/ui/form-dialog.svelte` | Create/edit dialogs with form + error |
| `CopyableInput` | `$lib/components/ui/copyable-input.svelte` | Readonly value with copy button, optional secret |
| `CorsEditor` | `$lib/components/ui/cors-editor.svelte` | CORS XML editing with save/delete |
| `IpListEditor` | `$lib/components/ui/ip-list-editor.svelte` | IP allow/deny lists with badges |
| `TagInput` | `$lib/components/ui/tag-input.svelte` | Tag/chip editing with add/remove |
| `ErrorBanner` | `$lib/components/ui/error-banner.svelte` | Error message display |
| `StatCard` | `$lib/components/ui/stat-card.svelte` | Metric display (bytes, counts) |
| `StorageProgressBar` | `$lib/components/ui/storage-progress-bar.svelte` | Quota utilization bar |
| `CardSkeleton` | `$lib/components/ui/skeleton/card-skeleton.svelte` | Loading placeholder for cards |
| `BulkDeleteDialog` | `$lib/components/ui/bulk-delete-dialog.svelte` | Multi-item delete confirmation |
| `DeleteConfirmDialog` | `$lib/components/ui/delete-confirm-dialog.svelte` | Single-item delete confirmation |
| `PageHeader` | `$lib/components/ui/page-header.svelte` | Page title + description + actions |
| `BackButton` | `$lib/components/ui/back-button.svelte` | Navigation back link |

## Utilities

| Utility | Import | Use for |
|---|---|---|
| `useSave()` | `$lib/utils/use-save.svelte.js` | Settings save pattern (saving + syncVersion + toast) |
| `useDelete()` | `$lib/utils/use-delete.svelte.js` | Delete with confirmation + toast |
| `formatBytes()` | `$lib/utils/format.ts` | Human-readable byte sizes |
| `parseQuotaBytes()` | `$lib/utils/format.ts` | Parse "50 GB" to number |
| `calcQuotaPercent()` | `$lib/utils/format.ts` | Percentage for quota bars |

## Section Component Pattern

Namespace/settings pages use section components inside a grid:

```svelte
<!-- +page.svelte -->
<div class="grid gap-6 lg:grid-cols-2">
  <SectionA {tenant} {namespaceName} />
  <SectionB {tenant} {namespaceName} />
</div>
```

Each section is a self-contained Card that:
1. Fetches its own data via `$derived(get_something(...))`
2. Shows a loading skeleton via `{#await data}` block
3. Manages its own local state and save logic
4. Uses `Card.Root > Card.Header > Card.Content > Card.Footer` structure

## Svelte 5 Rules

- **Runes only** — no `$:`, no `export let`, no `on:click`, no `<slot>`
- `$state` for mutable reactive variables
- `$derived` for computed values (NOT `$effect` for derivations)
- `$effect` only for syncing from server or external side effects
- `$props()` with TypeScript types for component props
- `$bindable()` for two-way bound props (e.g., `open` in dialogs)
- `{#snippet}` + `{@render}` instead of slots
- `onclick={handler}` not `on:click={handler}`
- `page.data.tenant` from `$app/state` (NOT `$app/stores`)

## Naming Conventions

- Remote files: `*.remote.ts` (e.g., `namespaces.remote.ts`)
- Section components: `ns-*.svelte`, `settings-*.svelte`, `user-*.svelte`
- Dialog components: `*-dialog.svelte` (e.g., `bucket-create-dialog.svelte`)
- Utilities: `use-*.svelte.ts` for composables with reactive state
- Roles enum: `ADMINISTRATOR`, `SECURITY`, `MONITOR`, `COMPLIANCE`

## Anti-Patterns to Avoid

- **Don't duplicate save boilerplate** — use `useSave()` composable
- **Don't duplicate dialog boilerplate** — use `FormDialog` component
- **Don't import `toast` directly** in settings forms — `useSave` handles it
- **Don't use `$effect` to compute derived values** — use `$derived`
- **Don't fetch same data in multiple sibling components** — lift query to parent
- **Don't use `Record<string, unknown>`** for typed API responses — define types
- **Don't use `$app/stores`** — use `$app/state` for page data
