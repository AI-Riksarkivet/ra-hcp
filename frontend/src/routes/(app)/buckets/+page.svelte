<script lang="ts">
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
	import { Plus, Trash2 } from 'lucide-svelte';
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
	import DataTableActions from './data-table/data-table-actions.svelte';
	import DataTableHeaderButton from '$lib/components/ui/data-table/data-table-header-button.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import { formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { get_buckets, create_bucket, delete_bucket } from '$lib/buckets.remote.js';

	// ── Data fetching ──────────────────────────────────────────────
	let bucketData = get_buckets();
	let owner = $derived(
		bucketData.current?.owner as {
			display_name?: string;
			id?: string;
			DisplayName?: string;
			ID?: string;
		} | null
	);
	let ownerName = $derived(owner?.display_name ?? owner?.DisplayName ?? '');

	type BucketRow = { name: string; creation_date: string; owner: string };
	let data = $derived<BucketRow[]>(
		(bucketData.current?.buckets ?? []).map((b: { name: string; creation_date: string }) => ({
			name: b.name,
			creation_date: b.creation_date,
			owner: ownerName,
		}))
	);

	// ── Column definitions ─────────────────────────────────────────
	const columns: ColumnDef<BucketRow>[] = [
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
						render: () => `<span class="font-medium">${name}</span>`,
					};
				});
				return renderSnippet(s, { name: row.original.name });
			},
		},
		{
			accessorKey: 'owner',
			header: 'Owner',
			cell: ({ row }) => {
				const s = createRawSnippet<[{ owner: string }]>((getOwner) => {
					const { owner } = getOwner();
					return {
						render: () => `<span class="text-muted-foreground">${owner || '-'}</span>`,
					};
				});
				return renderSnippet(s, { owner: row.original.owner });
			},
		},
		{
			accessorKey: 'creation_date',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Created',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ date: string }]>((getDate) => {
					const { date } = getDate();
					const formatted = date ? formatDate(date) : '-';
					return {
						render: () => `<span class="text-muted-foreground">${formatted}</span>`,
					};
				});
				return renderSnippet(s, { date: row.original.creation_date });
			},
			sortingFn: (a, b) => {
				const da = new Date(a.original.creation_date).getTime();
				const db = new Date(b.original.creation_date).getTime();
				return da - db;
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
					onnavigate: () => goto(`/buckets/${row.original.name}`),
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
		if (!deleteTarget) return;
		deleting = true;
		try {
			await delete_bucket({ bucket: deleteTarget }).updates(bucketData);
			toast.success(`Deleted bucket "${deleteTarget}"`);
		} catch {
			toast.error('Failed to delete bucket');
		} finally {
			deleting = false;
			deleteDialogOpen = false;
			deleteTarget = '';
		}
	}

	async function confirmBulkDelete() {
		deleting = true;
		const names = table.getFilteredSelectedRowModel().rows.map((r) => r.original.name);
		let successCount = 0,
			failCount = 0;
		for (let i = 0; i < names.length; i++) {
			try {
				const call = delete_bucket({ bucket: names[i] });
				if (i === names.length - 1) {
					await call.updates(bucketData);
				} else {
					await call;
				}
				successCount++;
			} catch {
				failCount++;
			}
		}
		if (successCount > 0)
			toast.success(`Deleted ${successCount} bucket${successCount !== 1 ? 's' : ''}`);
		if (failCount > 0)
			toast.error(`Failed to delete ${failCount} bucket${failCount !== 1 ? 's' : ''}`);
		rowSelection = {};
		deleting = false;
		bulkDeleteOpen = false;
	}

	let bulkDeleteOpen = $state(false);

	// ── Create logic ───────────────────────────────────────────────
	let createOpen = $state(false);
	let createError = $state('');
	let creating = $state(false);

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		const form = e.currentTarget as HTMLFormElement;
		const formData = new FormData(form);
		const name = formData.get('bucket') as string;
		if (!name) return;
		creating = true;
		createError = '';
		try {
			await create_bucket({ bucket: name }).updates(bucketData);
			toast.success('Bucket created successfully');
			createOpen = false;
			form.reset();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create bucket';
		} finally {
			creating = false;
		}
	}

	let selectedCount = $derived(table.getFilteredSelectedRowModel().rows.length);
</script>

<svelte:head>
	<title>Buckets - HCP Admin Console</title>
</svelte:head>

<div class="space-y-4">
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-2xl font-bold">Buckets</h2>
			<p class="mt-1 text-sm text-muted-foreground">Manage S3 buckets on your HCP system</p>
		</div>
		<Button onclick={() => (createOpen = true)}>
			<Plus class="h-4 w-4" />
			Create Bucket
		</Button>
	</div>

	<!-- Create Dialog -->
	<Dialog.Root bind:open={createOpen}>
		<Dialog.Content class="sm:max-w-md">
			<Dialog.Header><Dialog.Title>Create Bucket</Dialog.Title></Dialog.Header>
			<form onsubmit={handleCreate} class="space-y-4">
				{#if createError}
					<div
						class="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
					>
						{createError}
					</div>
				{/if}
				<div class="space-y-2">
					<Label for="bucket-name">Bucket Name</Label>
					<Input id="bucket-name" name="bucket" placeholder="my-bucket" required />
				</div>
				<Dialog.Footer>
					<Button variant="ghost" type="button" onclick={() => (createOpen = false)}>Cancel</Button>
					<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
				</Dialog.Footer>
			</form>
		</Dialog.Content>
	</Dialog.Root>

	{#await bucketData}
		<TableSkeleton rows={5} columns={5} />
	{:then _}
		<!-- Toolbar -->
		<div class="flex items-center gap-2">
			<Input
				placeholder="Filter buckets..."
				value={(table.getColumn('name')?.getFilterValue() as string) ?? ''}
				oninput={(e) => table.getColumn('name')?.setFilterValue(e.currentTarget.value)}
				class="max-w-sm"
			/>
			{#if ownerName}
				<Badge variant="outline">Owner: {ownerName}</Badge>
			{/if}
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
				<Button variant="ghost" size="sm" onclick={() => (rowSelection = {})}>Deselect All</Button>
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
							onclick={() => goto(`/buckets/${row.original.name}`)}
						>
							{#each row.getVisibleCells() as cell (cell.id)}
								<Table.Cell
									class="[&:has([role=checkbox])]:ps-3 [&:has([role=menuitem])]:onclick-passthrough"
									onclick={(e) => {
										const target = e.target as HTMLElement;
										if (
											target.closest('[role=checkbox]') ||
											target.closest('[role=menuitem]') ||
											target.closest('button')
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
								No buckets found. Create one to get started.
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
				{table.getFilteredRowModel().rows.length} bucket(s) selected.
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
</div>

<DeleteConfirmDialog
	bind:open={deleteDialogOpen}
	name={deleteTarget}
	itemType="bucket"
	loading={deleting}
	onconfirm={confirmDelete}
/>

<Dialog.Root bind:open={bulkDeleteOpen}>
	<Dialog.Content class="sm:max-w-md">
		<Dialog.Header>
			<Dialog.Title>Delete {selectedCount} buckets?</Dialog.Title>
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
