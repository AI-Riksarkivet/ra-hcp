<script lang="ts">
	import { page } from '$app/state';
	import {
		type ColumnDef,
		type ColumnFiltersState,
		type PaginationState,
		type RowSelectionState,
		type SortingState,
		type VisibilityState,
		getCoreRowModel,
		getFilteredRowModel,
		getPaginationRowModel,
		getSortedRowModel,
	} from '@tanstack/table-core';
	import { createRawSnippet } from 'svelte';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import { Plus, Trash2, X } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import {
		FlexRender,
		createSvelteTable,
		renderComponent,
		renderSnippet,
	} from '$lib/components/ui/data-table/index.js';
	import DataTableCheckbox from '$lib/components/ui/data-table/data-table-checkbox.svelte';
	import DataTableHeaderButton from '$lib/components/ui/data-table/data-table-header-button.svelte';
	import DataTableActions from './data-table/data-table-actions.svelte';
	import DataTableTagCell from './data-table/data-table-tag-cell.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import ServiceTagBadge from '$lib/components/ui/service-tag-badge.svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
	import {
		get_namespaces,
		create_namespace,
		update_namespace,
		delete_namespace,
		type Namespace,
	} from '$lib/namespaces.remote.js';

	let tenant = $derived(page.data.tenant as string | undefined);
	let nsData = $derived(tenant ? get_namespaces({ tenant }) : undefined);

	type NsRow = {
		name: string;
		tags: string[];
		description: string;
		hardQuota: string;
		softQuota: string;
		hashScheme: string;
	};

	let data = $derived<NsRow[]>(
		((nsData?.current ?? []) as Namespace[]).map((ns) => ({
			name: ns.name,
			tags: ns.tags?.tag ?? [],
			description: ns.description ?? '',
			hardQuota: ns.hardQuota ?? '',
			softQuota: ns.softQuota != null ? `${ns.softQuota}%` : '',
			hashScheme: ns.hashScheme ?? '',
		}))
	);

	// ── Tag editing state ─────────────────────────────────────────
	let editingTagsNs = $state('');

	function startEditTags(name: string) {
		editingTagsNs = name;
	}

	async function saveTags(name: string, tags: string[]) {
		if (!tenant || !nsData) return;
		try {
			await update_namespace({
				tenant,
				name,
				body: { tags: { tag: tags } },
			}).updates(nsData);
			toast.success('Tags updated');
			editingTagsNs = '';
		} catch {
			toast.error('Failed to update tags');
		}
	}

	// ── Column definitions ─────────────────────────────────────────
	const columns: ColumnDef<NsRow>[] = [
		{
			id: 'select',
			header: ({ table }) =>
				renderComponent(DataTableCheckbox, {
					checked: table.getIsAllPageRowsSelected(),
					indeterminate: table.getIsSomePageRowsSelected() && !table.getIsAllPageRowsSelected(),
					onCheckedChange: (value: boolean) => table.toggleAllPageRowsSelected(!!value),
					'aria-label': 'Select all',
				}),
			cell: ({ row }) =>
				renderComponent(DataTableCheckbox, {
					checked: row.getIsSelected(),
					onCheckedChange: (value: boolean) => row.toggleSelected(!!value),
					'aria-label': 'Select row',
				}),
			enableSorting: false,
			enableHiding: false,
		},
		{
			accessorKey: 'name',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Name',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ name: string }]>((getName) => {
					const { name } = getName();
					return {
						render: () =>
							`<a href="/namespaces/${encodeURIComponent(name)}" class="font-medium text-primary underline-offset-4 hover:underline">${name}</a>`,
					};
				});
				return renderSnippet(s, { name: row.original.name });
			},
		},
		{
			accessorKey: 'tags',
			header: 'Tags',
			cell: ({ row }) =>
				renderComponent(DataTableTagCell, {
					tags: row.original.tags,
					editing: editingTagsNs === row.original.name,
					onsave: (tags: string[]) => saveTags(row.original.name, tags),
					onstartedit: () => startEditTags(row.original.name),
					oncanceledit: () => (editingTagsNs = ''),
				}),
			enableSorting: false,
		},
		{
			accessorKey: 'description',
			header: 'Description',
			cell: ({ row }) => {
				const s = createRawSnippet<[{ desc: string }]>((getDesc) => {
					const { desc } = getDesc();
					return {
						render: () => `<span class="text-muted-foreground">${desc || '—'}</span>`,
					};
				});
				return renderSnippet(s, { desc: row.original.description });
			},
		},
		{
			accessorKey: 'hardQuota',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Hard Quota',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: string }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () => `<span class="text-muted-foreground">${val || '—'}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.hardQuota });
			},
		},
		{
			accessorKey: 'softQuota',
			header: 'Soft Quota',
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: string }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () => `<span class="text-muted-foreground">${val || '—'}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.softQuota });
			},
		},
		{
			accessorKey: 'hashScheme',
			header: 'Hash Scheme',
			cell: ({ row }) => {
				const scheme = row.original.hashScheme;
				if (!scheme) {
					const s = createRawSnippet(() => ({
						render: () => `<span class="text-muted-foreground">—</span>`,
					}));
					return renderSnippet(s, undefined);
				}
				return renderComponent(Badge, {
					variant: 'secondary',
					children: createRawSnippet(() => ({ render: () => scheme })),
				});
			},
		},
		{
			id: 'actions',
			enableHiding: false,
			cell: ({ row }) =>
				renderComponent(DataTableActions, {
					name: row.original.name,
					ondelete: () => {
						deleteTarget = row.original.name;
						deleteDialogOpen = true;
					},
					onnavigate: () => goto(`/namespaces/${encodeURIComponent(row.original.name)}`),
					onedittags: () => startEditTags(row.original.name),
				}),
		},
	];

	// ── Table state ────────────────────────────────────────────────
	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 20 });
	let sorting = $state<SortingState>([]);
	let columnFilters = $state<ColumnFiltersState>([]);
	let rowSelection = $state<RowSelectionState>({});
	let columnVisibility = $state<VisibilityState>({});

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns,
		state: {
			get pagination() {
				return pagination;
			},
			get sorting() {
				return sorting;
			},
			get columnFilters() {
				return columnFilters;
			},
			get columnVisibility() {
				return columnVisibility;
			},
			get rowSelection() {
				return rowSelection;
			},
		},
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		onPaginationChange: (updater) => {
			pagination = typeof updater === 'function' ? updater(pagination) : updater;
		},
		onSortingChange: (updater) => {
			sorting = typeof updater === 'function' ? updater(sorting) : updater;
		},
		onColumnFiltersChange: (updater) => {
			columnFilters = typeof updater === 'function' ? updater(columnFilters) : updater;
		},
		onColumnVisibilityChange: (updater) => {
			columnVisibility = typeof updater === 'function' ? updater(columnVisibility) : updater;
		},
		onRowSelectionChange: (updater) => {
			rowSelection = typeof updater === 'function' ? updater(rowSelection) : updater;
		},
	});

	// ── Delete logic ───────────────────────────────────────────────
	let deleteTarget = $state('');
	let deleteDialogOpen = $state(false);
	let deleting = $state(false);

	async function confirmDelete() {
		if (!deleteTarget || !tenant || !nsData) return;
		deleting = true;
		try {
			await delete_namespace({ tenant, name: deleteTarget }).updates(nsData);
			toast.success(`Deleted namespace "${deleteTarget}"`);
		} catch {
			toast.error('Failed to delete namespace');
		} finally {
			deleting = false;
			deleteDialogOpen = false;
			deleteTarget = '';
		}
	}

	async function confirmBulkDelete() {
		if (!tenant || !nsData) return;
		deleting = true;
		const names = table.getFilteredSelectedRowModel().rows.map((r) => r.original.name);
		let successCount = 0,
			failCount = 0;
		for (let i = 0; i < names.length; i++) {
			try {
				const call = delete_namespace({ tenant, name: names[i] });
				if (i === names.length - 1) {
					await call.updates(nsData);
				} else {
					await call;
				}
				successCount++;
			} catch {
				failCount++;
			}
		}
		if (successCount > 0)
			toast.success(`Deleted ${successCount} namespace${successCount !== 1 ? 's' : ''}`);
		if (failCount > 0)
			toast.error(`Failed to delete ${failCount} namespace${failCount !== 1 ? 's' : ''}`);
		rowSelection = {};
		deleting = false;
		bulkDeleteOpen = false;
	}

	let bulkDeleteOpen = $state(false);

	// ── Create logic ───────────────────────────────────────────────
	let createOpen = $state(false);
	let createError = $state('');
	let creating = $state(false);
	let createTags = $state<string[]>([]);
	let tagInput = $state('');

	function addTag() {
		const t = tagInput.trim();
		if (t && !createTags.includes(t.toLowerCase())) {
			createTags = [...createTags, t.toLowerCase()];
		}
		tagInput = '';
	}

	function removeTag(t: string) {
		createTags = createTags.filter((x) => x !== t);
	}

	function handleTagKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addTag();
		}
	}

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		if (!tenant || !nsData) return;
		const form = e.currentTarget as HTMLFormElement;
		const formData = new FormData(form);
		const name = formData.get('namespace') as string;
		if (!name) return;
		creating = true;
		createError = '';
		try {
			const description = (formData.get('description') as string) || undefined;
			const hardQuota = (formData.get('hardQuota') as string) || undefined;
			const softQuotaStr = formData.get('softQuota') as string;
			const softQuota = softQuotaStr ? Number(softQuotaStr) : undefined;
			const hashScheme = (formData.get('hashScheme') as string) || undefined;
			const searchEnabled = formData.has('searchEnabled');
			const versioningEnabled = formData.has('versioningEnabled');
			await create_namespace({
				tenant,
				name,
				description,
				hardQuota,
				softQuota,
				hashScheme,
				searchEnabled,
				versioningEnabled,
				tags: createTags.length > 0 ? createTags : undefined,
			}).updates(nsData);
			toast.success('Namespace created successfully');
			createOpen = false;
			createTags = [];
			form.reset();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create namespace';
		} finally {
			creating = false;
		}
	}

	let selectedCount = $derived(table.getFilteredSelectedRowModel().rows.length);
</script>

<svelte:head>
	<title>Namespaces - HCP Admin Console</title>
</svelte:head>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-2xl font-bold">Namespaces</h2>
			<p class="mt-1 text-sm text-muted-foreground">Manage tenant namespaces</p>
		</div>
		{#if tenant}
			<Button onclick={() => (createOpen = true)}>
				<Plus class="h-4 w-4" />
				Create Namespace
			</Button>
		{/if}
	</div>

	<!-- Create Dialog -->
	<Dialog.Root bind:open={createOpen}>
		<Dialog.Content class="sm:max-w-lg">
			<Dialog.Header>
				<Dialog.Title>Create Namespace</Dialog.Title>
				<Dialog.Description>Configure a new namespace for this tenant.</Dialog.Description>
			</Dialog.Header>
			<form onsubmit={handleCreate} class="space-y-4">
				{#if createError}
					<div
						class="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
					>
						{createError}
					</div>
				{/if}
				<div class="space-y-2">
					<Label for="ns-name">Namespace Name</Label>
					<Input id="ns-name" name="namespace" placeholder="my-namespace" required />
				</div>
				<div class="space-y-2">
					<Label for="ns-desc">Description</Label>
					<Input id="ns-desc" name="description" placeholder="Optional description" />
				</div>
				<div class="grid grid-cols-2 gap-4">
					<div class="space-y-2">
						<Label for="ns-hard-quota">Hard Quota</Label>
						<Input id="ns-hard-quota" name="hardQuota" placeholder="e.g. 50 GB" />
					</div>
					<div class="space-y-2">
						<Label for="ns-soft-quota">Soft Quota (%)</Label>
						<Input
							id="ns-soft-quota"
							name="softQuota"
							type="number"
							min="10"
							max="95"
							placeholder="85"
						/>
					</div>
				</div>
				<div class="space-y-2">
					<Label for="ns-hash">Hash Scheme</Label>
					<select
						id="ns-hash"
						name="hashScheme"
						class="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
					>
						<option value="SHA-256">SHA-256</option>
						<option value="SHA-512">SHA-512</option>
						<option value="SHA-384">SHA-384</option>
						<option value="SHA-1">SHA-1</option>
						<option value="MD5">MD5</option>
					</select>
				</div>
				<div class="space-y-2">
					<Label for="ns-tags">Tags</Label>
					<div class="flex gap-2">
						<Input
							id="ns-tags"
							placeholder="e.g. lakefs, nfs, s3"
							bind:value={tagInput}
							onkeydown={handleTagKeydown}
						/>
						<Button type="button" variant="secondary" size="sm" onclick={addTag}>Add</Button>
					</div>
					{#if createTags.length > 0}
						<div class="flex flex-wrap gap-1 pt-1">
							{#each createTags as t (t)}
								<ServiceTagBadge tag={t} />
								<button
									type="button"
									class="-ml-1 mr-1 rounded-full p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
									onclick={() => removeTag(t)}
								>
									<X class="h-3 w-3" />
								</button>
							{/each}
						</div>
					{/if}
				</div>
				<div class="flex gap-6">
					<label class="flex items-center gap-2 text-sm">
						<input type="checkbox" name="searchEnabled" class="h-4 w-4 rounded border-input" />
						Enable Search
					</label>
					<label class="flex items-center gap-2 text-sm">
						<input type="checkbox" name="versioningEnabled" class="h-4 w-4 rounded border-input" />
						Enable Versioning
					</label>
				</div>
				<Dialog.Footer>
					<Button variant="ghost" type="button" onclick={() => (createOpen = false)}>Cancel</Button>
					<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
				</Dialog.Footer>
			</form>
		</Dialog.Content>
	</Dialog.Root>

	{#if tenant}
		{#await nsData}
			<TableSkeleton rows={5} columns={7} />
		{:then _}
			<!-- Toolbar -->
			<div class="flex items-center gap-2">
				<Input
					placeholder="Filter namespaces..."
					value={(table.getColumn('name')?.getFilterValue() as string) ?? ''}
					oninput={(e) => table.getColumn('name')?.setFilterValue(e.currentTarget.value)}
					class="max-w-sm"
				/>
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<Button {...props} variant="outline" class="ml-auto">
								Columns <ChevronDown class="ml-2 size-4" />
							</Button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="end">
						{#each table.getAllColumns().filter((col) => col.getCanHide()) as column (column.id)}
							<DropdownMenu.CheckboxItem
								class="capitalize"
								checked={column.getIsVisible()}
								onCheckedChange={(v) => column.toggleVisibility(!!v)}
							>
								{column.id}
							</DropdownMenu.CheckboxItem>
						{/each}
					</DropdownMenu.Content>
				</DropdownMenu.Root>
			</div>

			{#if selectedCount > 0}
				<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
					<span class="text-sm font-medium">{selectedCount} selected</span>
					<Button variant="destructive" size="sm" onclick={() => (bulkDeleteOpen = true)}>
						<Trash2 class="h-3.5 w-3.5" />Delete Selected
					</Button>
					<Button variant="ghost" size="sm" onclick={() => (rowSelection = {})}>Deselect All</Button
					>
				</div>
			{/if}

			<!-- Table -->
			<div class="rounded-md border">
				<Table.Root>
					<Table.Header>
						{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
							<Table.Row>
								{#each headerGroup.headers as header (header.id)}
									<Table.Head class="[&:has([role=checkbox])]:ps-3">
										{#if !header.isPlaceholder}
											<FlexRender
												content={header.column.columnDef.header}
												context={header.getContext()}
											/>
										{/if}
									</Table.Head>
								{/each}
							</Table.Row>
						{/each}
					</Table.Header>
					<Table.Body>
						{#each table.getRowModel().rows as row (row.id)}
							<Table.Row
								data-state={row.getIsSelected() && 'selected'}
								class="cursor-pointer"
								onclick={() => goto(`/namespaces/${encodeURIComponent(row.original.name)}`)}
							>
								{#each row.getVisibleCells() as cell (cell.id)}
									<Table.Cell
										class="[&:has([role=checkbox])]:ps-3 [&:has([role=menuitem])]:onclick-passthrough"
										onclick={(e) => {
											const target = e.target as HTMLElement;
											if (
												target.closest('[role=checkbox]') ||
												target.closest('[role=menuitem]') ||
												target.closest('button') ||
												target.closest('a') ||
												target.closest('input')
											) {
												e.stopPropagation();
											}
										}}
									>
										<FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
									</Table.Cell>
								{/each}
							</Table.Row>
						{:else}
							<Table.Row>
								<Table.Cell colspan={columns.length} class="h-24 text-center">
									No namespaces found. Create one to get started.
								</Table.Cell>
							</Table.Row>
						{/each}
					</Table.Body>
				</Table.Root>
			</div>

			<!-- Pagination -->
			<div class="flex items-center justify-end space-x-2">
				<div class="flex-1 text-sm text-muted-foreground">
					{table.getFilteredSelectedRowModel().rows.length} of
					{table.getFilteredRowModel().rows.length} namespace(s) selected.
				</div>
				<div class="space-x-2">
					<Button
						variant="outline"
						size="sm"
						onclick={() => table.previousPage()}
						disabled={!table.getCanPreviousPage()}
					>
						Previous
					</Button>
					<Button
						variant="outline"
						size="sm"
						onclick={() => table.nextPage()}
						disabled={!table.getCanNextPage()}
					>
						Next
					</Button>
				</div>
			</div>
		{/await}
	{:else}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to manage namespaces.</p>
		</div>
	{/if}
</div>

<DeleteConfirmDialog
	bind:open={deleteDialogOpen}
	name={deleteTarget}
	itemType="namespace"
	loading={deleting}
	onconfirm={confirmDelete}
/>

<Dialog.Root bind:open={bulkDeleteOpen}>
	<Dialog.Content class="sm:max-w-md">
		<Dialog.Header>
			<Dialog.Title>Delete {selectedCount} namespaces?</Dialog.Title>
			<Dialog.Description>This action cannot be undone.</Dialog.Description>
		</Dialog.Header>
		<Dialog.Footer>
			<Button variant="ghost" onclick={() => (bulkDeleteOpen = false)}>Cancel</Button>
			<Button variant="destructive" onclick={confirmBulkDelete} disabled={deleting}>
				{deleting ? 'Deleting...' : 'Delete All'}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
