<script lang="ts">
	import { page } from '$app/state';
	import {
		type ColumnDef,
		type ColumnFiltersState,
		type RowSelectionState,
		type SortingState,
		type VisibilityState,
		getCoreRowModel,
		getFilteredRowModel,
		getSortedRowModel,
	} from '@tanstack/table-core';
	import { createRawSnippet } from 'svelte';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import { Search, FileSearch, Activity, CircleHelp, Download, Trash2 } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import * as Card from '$lib/components/ui/card/index.js';
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
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { formatBytes, formatDate } from '$lib/utils/format.js';
	import {
		search_objects,
		search_operations,
		type QueryResultObject,
		type ObjectQueryResponse,
		type OperationQueryResponse,
	} from '$lib/search.remote.js';

	let tenant = $derived(page.data.tenant as string | undefined);

	// Search mode
	let mode = $state<'objects' | 'operations'>('objects');

	// ── Object search state ──────────────────────────────────────
	let objectQuery = $state('');
	let pageSize = 25;
	let objectOffset = $state(0);
	let objectResults = $state<ObjectQueryResponse | null>(null);
	let objectLoading = $state(false);
	let objectError = $state('');
	let objectSearched = $state(false);

	// Server-side sort state
	type SortField =
		| 'utf8Name'
		| 'namespace'
		| 'size'
		| 'contentType'
		| 'owner'
		| 'changeTimeMilliseconds';
	let sortField = $state<SortField | null>(null);
	let sortAsc = $state(true);

	// ── Operation search state ───────────────────────────────────
	let opTransactions = $state<string[]>([]);
	let opNamespace = $state('');
	let opResults = $state<OperationQueryResponse | null>(null);
	let opLoading = $state(false);
	let opError = $state('');
	let opSearched = $state(false);

	// Help panel
	let helpOpen = $state(false);

	// Pagination
	let objectTotalPages = $derived(
		objectResults ? Math.max(1, Math.ceil(objectResults.status.totalResults / pageSize)) : 0
	);
	let objectCurrentPage = $derived(Math.floor(objectOffset / pageSize) + 1);

	function displayPath(item: QueryResultObject): string {
		if (item.utf8Name) return item.utf8Name;
		try {
			return decodeURIComponent(item.urlName);
		} catch {
			return item.urlName;
		}
	}

	function formatMillis(ms: string | undefined): string {
		if (!ms) return '—';
		return formatDate(new Date(Number(ms)));
	}

	type BadgeVariant = 'default' | 'secondary' | 'destructive' | 'outline' | 'success' | 'warning';
	function operationVariant(op: string): BadgeVariant {
		switch (op.toUpperCase()) {
			case 'CREATED':
				return 'success';
			case 'DELETED':
				return 'destructive';
			case 'PURGED':
				return 'warning';
			default:
				return 'secondary';
		}
	}

	function buildSortParam(): string | undefined {
		if (!sortField) return undefined;
		return `${sortAsc ? '+' : '-'}${sortField}`;
	}

	function objectDownloadUrl(item: QueryResultObject): string {
		const ns = item.namespace ?? '';
		return `/api/v1/buckets/${encodeURIComponent(ns)}/objects/${encodeURIComponent(item.urlName)}`;
	}

	async function handleObjectSearch() {
		if (!tenant) return;
		objectLoading = true;
		objectError = '';
		objectSearched = true;
		objRowSelection = {};
		try {
			objectResults = await search_objects({
				tenant,
				query: objectQuery,
				count: pageSize,
				offset: objectOffset,
				verbose: true,
				sort: buildSortParam(),
			});
		} catch (err) {
			objectError = err instanceof Error ? err.message : 'Object query failed';
			objectResults = null;
		} finally {
			objectLoading = false;
		}
	}

	function objectPagePrev() {
		objectOffset = Math.max(0, objectOffset - pageSize);
		handleObjectSearch();
	}

	function objectPageNext() {
		objectOffset += pageSize;
		handleObjectSearch();
	}

	function searchFromStart() {
		if (mode === 'objects') {
			objectOffset = 0;
			handleObjectSearch();
		} else {
			handleOpSearch();
		}
	}

	function toggleServerSort(field: SortField) {
		if (sortField === field) {
			if (sortAsc) {
				sortAsc = false;
			} else {
				sortField = null;
				sortAsc = true;
			}
		} else {
			sortField = field;
			sortAsc = true;
		}
		if (objectSearched) {
			objectOffset = 0;
			handleObjectSearch();
		}
	}

	async function handleOpSearch() {
		if (!tenant) return;
		opLoading = true;
		opError = '';
		opSearched = true;
		try {
			opResults = await search_operations({
				tenant,
				count: 100,
				verbose: true,
				transactions: opTransactions.length > 0 ? opTransactions : undefined,
				namespaces: opNamespace ? [opNamespace] : undefined,
			});
		} catch (err) {
			opError = err instanceof Error ? err.message : 'Operation query failed';
			opResults = null;
		} finally {
			opLoading = false;
		}
	}

	function toggleTransaction(tx: string) {
		if (opTransactions.includes(tx)) {
			opTransactions = opTransactions.filter((t) => t !== tx);
		} else {
			opTransactions = [...opTransactions, tx];
		}
	}

	// ── Object results table ─────────────────────────────────────
	type ObjRow = {
		urlName: string;
		path: string;
		namespace: string;
		size: number | null;
		contentType: string;
		owner: string;
		changeTimeMilliseconds: string;
		_raw: QueryResultObject;
	};

	let objData = $derived<ObjRow[]>(
		(objectResults?.resultSet ?? []).map((item) => ({
			urlName: item.urlName,
			path: displayPath(item),
			namespace: item.namespace ?? '',
			size: item.size ?? null,
			contentType: item.contentType ?? '',
			owner: item.owner ?? '',
			changeTimeMilliseconds: item.changeTimeMilliseconds ?? '',
			_raw: item,
		}))
	);

	// Server-side sort header helper (renders sort arrow inline)
	function serverSortHeader(field: SortField, label: string) {
		return createRawSnippet(() => {
			const isActive = sortField === field;
			const arrow = isActive ? (sortAsc ? ' ↑' : ' ↓') : '';
			return {
				render: () =>
					`<button class="inline-flex items-center gap-1 hover:text-foreground"><span>${label}</span>${isActive ? `<span class="text-xs">${arrow}</span>` : '<svg class="ml-1 size-3.5 opacity-30" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="m7 15 5 5 5-5"/><path d="m7 9 5-5 5 5"/></svg>'}</button>`,
			};
		});
	}

	const objColumns: ColumnDef<ObjRow>[] = [
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
			accessorKey: 'path',
			header: () => serverSortHeader('utf8Name', 'Path'),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ path: string }]>((getP) => {
					const { path } = getP();
					return {
						render: () =>
							`<span class="max-w-xs truncate font-medium" title="${path}">${path}</span>`,
					};
				});
				return renderSnippet(s, { path: row.original.path });
			},
			enableSorting: false,
		},
		{
			accessorKey: 'namespace',
			header: () => serverSortHeader('namespace', 'Namespace'),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: string }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () => `<span class="text-muted-foreground">${val || '—'}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.namespace });
			},
			enableSorting: false,
		},
		{
			accessorKey: 'size',
			header: () => serverSortHeader('size', 'Size'),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: number | null }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () =>
							`<span class="text-right text-muted-foreground">${val != null ? formatBytes(val) : '—'}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.size });
			},
			enableSorting: false,
		},
		{
			accessorKey: 'contentType',
			header: () => serverSortHeader('contentType', 'Content Type'),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: string }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () => `<span class="text-muted-foreground">${val || '—'}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.contentType });
			},
			enableSorting: false,
		},
		{
			accessorKey: 'owner',
			header: () => serverSortHeader('owner', 'Owner'),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: string }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () => `<span class="text-muted-foreground">${val || '—'}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.owner });
			},
			enableSorting: false,
		},
		{
			accessorKey: 'changeTimeMilliseconds',
			header: () => serverSortHeader('changeTimeMilliseconds', 'Modified'),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: string }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () =>
							`<span class="whitespace-nowrap text-muted-foreground">${formatMillis(val)}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.changeTimeMilliseconds });
			},
			enableSorting: false,
		},
		{
			id: 'actions',
			enableHiding: false,
			cell: ({ row }) =>
				renderComponent(DataTableActions, {
					objectKey: row.original.path,
					downloadUrl: objectDownloadUrl(row.original._raw),
					namespace: row.original.namespace,
				}),
		},
	];

	let objRowSelection = $state<RowSelectionState>({});
	let objColumnFilters = $state<ColumnFiltersState>([]);
	let objColumnVisibility = $state<VisibilityState>({});

	const objTable = createSvelteTable({
		get data() {
			return objData;
		},
		columns: objColumns,
		state: {
			get rowSelection() {
				return objRowSelection;
			},
			get columnFilters() {
				return objColumnFilters;
			},
			get columnVisibility() {
				return objColumnVisibility;
			},
		},
		getCoreRowModel: getCoreRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		onRowSelectionChange: (updater) => {
			objRowSelection = typeof updater === 'function' ? updater(objRowSelection) : updater;
		},
		onColumnFiltersChange: (updater) => {
			objColumnFilters = typeof updater === 'function' ? updater(objColumnFilters) : updater;
		},
		onColumnVisibilityChange: (updater) => {
			objColumnVisibility = typeof updater === 'function' ? updater(objColumnVisibility) : updater;
		},
	});

	let objSelectedCount = $derived(objTable.getFilteredSelectedRowModel().rows.length);

	function downloadSelected() {
		const items = objTable.getFilteredSelectedRowModel().rows.map((r) => r.original._raw);
		if (items.length === 0) return;
		for (const item of items) {
			const a = document.createElement('a');
			a.href = objectDownloadUrl(item);
			a.download = '';
			document.body.appendChild(a);
			a.click();
			document.body.removeChild(a);
		}
		toast.success(`Started ${items.length} download${items.length !== 1 ? 's' : ''}`);
	}

	// ── Operation results table ──────────────────────────────────
	type OpRow = {
		urlName: string;
		path: string;
		operation: string;
		namespace: string;
		changeTimeMilliseconds: string;
	};

	let opData = $derived<OpRow[]>(
		(opResults?.resultSet ?? [])
			.map((item) => ({
				urlName: item.urlName,
				path: displayPath(item),
				operation: item.operation,
				namespace: item.namespace ?? '',
				changeTimeMilliseconds: item.changeTimeMilliseconds ?? '',
			}))
			.sort((a, b) => Number(b.changeTimeMilliseconds || 0) - Number(a.changeTimeMilliseconds || 0))
	);

	const opColumns: ColumnDef<OpRow>[] = [
		{
			accessorKey: 'path',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Path',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ path: string }]>((getP) => {
					const { path } = getP();
					return {
						render: () =>
							`<span class="max-w-xs truncate font-medium" title="${path}">${path}</span>`,
					};
				});
				return renderSnippet(s, { path: row.original.path });
			},
		},
		{
			accessorKey: 'operation',
			header: 'Operation',
			cell: ({ row }) =>
				renderComponent(Badge, {
					variant: operationVariant(row.original.operation),
					children: createRawSnippet(() => ({
						render: () => row.original.operation,
					})),
				}),
			enableSorting: false,
		},
		{
			accessorKey: 'namespace',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Namespace',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: string }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () => `<span class="text-muted-foreground">${val || '—'}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.namespace });
			},
		},
		{
			accessorKey: 'changeTimeMilliseconds',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Time',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: string }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () =>
							`<span class="whitespace-nowrap text-muted-foreground">${formatMillis(val)}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.changeTimeMilliseconds });
			},
			sortingFn: (a, b) =>
				Number(a.original.changeTimeMilliseconds || 0) -
				Number(b.original.changeTimeMilliseconds || 0),
		},
	];

	let opSorting = $state<SortingState>([]);
	let opColumnFilters = $state<ColumnFiltersState>([]);
	let opColumnVisibility = $state<VisibilityState>({});

	const opTable = createSvelteTable({
		get data() {
			return opData;
		},
		columns: opColumns,
		state: {
			get sorting() {
				return opSorting;
			},
			get columnFilters() {
				return opColumnFilters;
			},
			get columnVisibility() {
				return opColumnVisibility;
			},
		},
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		onSortingChange: (updater) => {
			opSorting = typeof updater === 'function' ? updater(opSorting) : updater;
		},
		onColumnFiltersChange: (updater) => {
			opColumnFilters = typeof updater === 'function' ? updater(opColumnFilters) : updater;
		},
		onColumnVisibilityChange: (updater) => {
			opColumnVisibility = typeof updater === 'function' ? updater(opColumnVisibility) : updater;
		},
	});
</script>

<svelte:head>
	<title>Search - HCP Admin Console</title>
</svelte:head>

<div class="space-y-4">
	<div>
		<h2 class="text-2xl font-bold">Search</h2>
		<p class="mt-1 text-sm text-muted-foreground">
			Query object metadata and audit operations across namespaces
		</p>
	</div>

	{#if tenant}
		<!-- Mode switch -->
		<div class="flex items-center gap-4">
			<div class="flex gap-1 rounded-lg border bg-muted/50 p-1">
				<button
					class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors {mode ===
					'objects'
						? 'bg-background text-foreground shadow-sm'
						: 'text-muted-foreground hover:text-foreground'}"
					onclick={() => (mode = 'objects')}
				>
					<FileSearch class="h-3.5 w-3.5" />
					Objects
				</button>
				<button
					class="flex items-center gap-1.5 rounded-md px-3 py-1.5 text-sm font-medium transition-colors {mode ===
					'operations'
						? 'bg-background text-foreground shadow-sm'
						: 'text-muted-foreground hover:text-foreground'}"
					onclick={() => (mode = 'operations')}
				>
					<Activity class="h-3.5 w-3.5" />
					Operations
				</button>
			</div>
			<button
				class="flex items-center gap-1 text-sm text-muted-foreground transition-colors hover:text-foreground"
				onclick={() => (helpOpen = !helpOpen)}
			>
				<CircleHelp class="h-4 w-4" />
				<span class="hidden sm:inline">How does this work?</span>
			</button>
		</div>

		<!-- Help panel -->
		{#if helpOpen}
			<Card.Root>
				<Card.Content class="py-4">
					{#if mode === 'objects'}
						<div class="space-y-3 text-sm">
							<p class="text-foreground">
								<strong>Object Search</strong> queries the HCP Metadata Query Engine. It searches indexed
								metadata for all objects stored across your namespaces.
							</p>
							<div class="grid gap-4 sm:grid-cols-2">
								<div>
									<p class="mb-1.5 font-medium text-foreground">Query syntax</p>
									<p class="mb-2 text-muted-foreground">
										Queries use <code class="rounded bg-muted px-1">field:value</code> Lucene
										syntax. Leading wildcards are not allowed. Combine with
										<code class="rounded bg-muted px-1">AND</code>,
										<code class="rounded bg-muted px-1">OR</code>,
										<code class="rounded bg-muted px-1">NOT</code>.
									</p>
									<ul class="space-y-1 text-muted-foreground">
										<li>
											<code class="rounded bg-muted px-1">namespace:documents</code> — filter by namespace
										</li>
										<li>
											<code class="rounded bg-muted px-1">contentType:application/pdf</code> — by MIME
											type
										</li>
										<li>
											<code class="rounded bg-muted px-1">owner:jdoe</code> — by object owner
										</li>
										<li>
											<code class="rounded bg-muted px-1">objectPath:reports/*</code> — path wildcard
										</li>
									</ul>
								</div>
								<div>
									<p class="mb-1.5 font-medium text-foreground">Range &amp; boolean queries</p>
									<ul class="space-y-1 text-muted-foreground">
										<li>
											<code class="rounded bg-muted px-1">size:[1024 TO *]</code> — larger than 1 KB
										</li>
										<li>
											<code class="rounded bg-muted px-1">size:[* TO 1048576]</code> — smaller than 1
											MB
										</li>
										<li>
											<code class="rounded bg-muted px-1">hold:true</code> — objects under legal hold
										</li>
										<li>
											<code class="rounded bg-muted px-1"
												>customMetadata:true AND namespace:logs</code
											>
										</li>
									</ul>
								</div>
							</div>
							<p class="text-xs text-muted-foreground">
								Click column headers to sort results server-side. Use the filter input to narrow
								results client-side within the current page.
							</p>
						</div>
					{:else}
						<div class="space-y-3 text-sm">
							<p class="text-foreground">
								<strong>Operation Search</strong> queries the HCP audit log for object lifecycle events.
								It shows when objects were created, deleted, or purged.
							</p>
							<p class="text-muted-foreground">
								Use the operation type checkboxes to filter by event type. Optionally filter to a
								specific namespace.
							</p>
						</div>
					{/if}
				</Card.Content>
			</Card.Root>
		{/if}

		{#if mode === 'objects'}
			<!-- Object search form -->
			<div class="flex flex-wrap items-end gap-3">
				<div class="min-w-0 flex-1">
					<Label for="obj-query" class="sr-only">Query</Label>
					<div class="relative">
						<Search
							class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
						/>
						<Input
							id="obj-query"
							bind:value={objectQuery}
							placeholder="objectPath:reports/* OR contentType:application/pdf"
							class="pl-9"
							onkeydown={(e) => e.key === 'Enter' && searchFromStart()}
						/>
					</div>
				</div>
				<Button onclick={searchFromStart} disabled={objectLoading || !objectQuery.trim()}>
					<Search class="h-4 w-4" />
					{objectLoading ? 'Searching...' : 'Search'}
				</Button>
			</div>

			<!-- Error -->
			{#if objectError}
				<div
					class="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
				>
					{objectError}
				</div>
			{/if}

			<!-- Results -->
			{#if objectLoading}
				<TableSkeleton rows={5} columns={7} />
			{:else if objectResults && objectResults.resultSet.length > 0}
				<!-- Toolbar -->
				<div class="flex items-center gap-2">
					<Input
						placeholder="Filter results..."
						value={(objTable.getColumn('path')?.getFilterValue() as string) ?? ''}
						oninput={(e) => objTable.getColumn('path')?.setFilterValue(e.currentTarget.value)}
						class="max-w-sm"
					/>
					<span class="text-sm text-muted-foreground">
						Showing {objectOffset + 1}–{Math.min(
							objectOffset + objectResults.resultSet.length,
							objectResults.status.totalResults
						)} of {objectResults.status.totalResults.toLocaleString()}
					</span>
					<DropdownMenu.Root>
						<DropdownMenu.Trigger>
							{#snippet child({ props })}
								<Button {...props} variant="outline" class="ml-auto">
									Columns <ChevronDown class="ml-2 size-4" />
								</Button>
							{/snippet}
						</DropdownMenu.Trigger>
						<DropdownMenu.Content align="end">
							{#each objTable
								.getAllColumns()
								.filter((col) => col.getCanHide()) as column (column.id)}
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

				{#if objSelectedCount > 0}
					<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
						<span class="text-sm font-medium">{objSelectedCount} selected</span>
						<Button size="sm" onclick={downloadSelected}>
							<Download class="h-3.5 w-3.5" />Download Selected
						</Button>
						<Button variant="ghost" size="sm" onclick={() => (objRowSelection = {})}
							>Deselect All</Button
						>
					</div>
				{/if}

				<!-- Table -->
				<div class="rounded-md border">
					<Table.Root>
						<Table.Header>
							{#each objTable.getHeaderGroups() as headerGroup (headerGroup.id)}
								<Table.Row>
									{#each headerGroup.headers as header (header.id)}
										<Table.Head class="[&:has([role=checkbox])]:ps-3">
											{#if !header.isPlaceholder}
												{@const field = {
													path: 'utf8Name',
													namespace: 'namespace',
													size: 'size',
													contentType: 'contentType',
													owner: 'owner',
													changeTimeMilliseconds: 'changeTimeMilliseconds',
												}[header.column.id] as SortField | undefined}
												{#if field}
													<button
														class="inline-flex items-center"
														onclick={() => toggleServerSort(field)}
													>
														<FlexRender
															content={header.column.columnDef.header}
															context={header.getContext()}
														/>
													</button>
												{:else}
													<FlexRender
														content={header.column.columnDef.header}
														context={header.getContext()}
													/>
												{/if}
											{/if}
										</Table.Head>
									{/each}
								</Table.Row>
							{/each}
						</Table.Header>
						<Table.Body>
							{#each objTable.getRowModel().rows as row (row.id)}
								<Table.Row data-state={row.getIsSelected() && 'selected'}>
									{#each row.getVisibleCells() as cell (cell.id)}
										<Table.Cell class="[&:has([role=checkbox])]:ps-3">
											<FlexRender
												content={cell.column.columnDef.cell}
												context={cell.getContext()}
											/>
										</Table.Cell>
									{/each}
								</Table.Row>
							{:else}
								<Table.Row>
									<Table.Cell colspan={objColumns.length} class="h-24 text-center">
										No results match your filter.
									</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>

				<!-- Server-side pagination -->
				{#if objectTotalPages > 1}
					<div class="flex items-center justify-end space-x-2">
						<div class="flex-1 text-sm text-muted-foreground">
							{objSelectedCount} of
							{objectResults.resultSet.length} row(s) selected.
						</div>
						<div class="flex items-center gap-4">
							<span class="text-sm text-muted-foreground">
								Page {objectCurrentPage} of {objectTotalPages}
							</span>
							<div class="space-x-2">
								<Button
									variant="outline"
									size="sm"
									onclick={objectPagePrev}
									disabled={objectOffset === 0}
								>
									Previous
								</Button>
								<Button
									variant="outline"
									size="sm"
									onclick={objectPageNext}
									disabled={objectCurrentPage >= objectTotalPages}
								>
									Next
								</Button>
							</div>
						</div>
					</div>
				{/if}
			{:else if objectSearched && !objectError}
				<div class="rounded-lg border border-dashed p-8 text-center">
					<FileSearch class="mx-auto h-10 w-10 text-muted-foreground/50" />
					<p class="mt-2 text-muted-foreground">No objects found matching your query.</p>
				</div>
			{:else if !objectSearched}
				<div class="rounded-lg border border-dashed p-8 text-center">
					<Search class="mx-auto h-10 w-10 text-muted-foreground/50" />
					<p class="mt-2 text-muted-foreground">Enter a query and click Search to find objects.</p>
				</div>
			{/if}
		{:else}
			<!-- Operation search form -->
			<div class="flex flex-wrap items-end gap-4">
				<div>
					<Label>Operation type</Label>
					<div class="mt-1.5 flex gap-4">
						{#each ['create', 'delete', 'purge'] as tx (tx)}
							<label class="flex items-center gap-2 text-sm">
								<input
									type="checkbox"
									checked={opTransactions.includes(tx)}
									onchange={() => toggleTransaction(tx)}
									class="h-4 w-4 rounded border-input"
								/>
								<span class="capitalize">{tx}</span>
							</label>
						{/each}
					</div>
				</div>
				<div class="min-w-0">
					<Label for="op-ns">Namespace</Label>
					<Input
						id="op-ns"
						bind:value={opNamespace}
						placeholder="All namespaces"
						class="mt-1.5 w-48"
						onkeydown={(e) => e.key === 'Enter' && handleOpSearch()}
					/>
				</div>
				<Button onclick={handleOpSearch} disabled={opLoading}>
					<Activity class="h-4 w-4" />
					{opLoading ? 'Searching...' : 'Search'}
				</Button>
			</div>

			<!-- Error -->
			{#if opError}
				<div
					class="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
				>
					{opError}
				</div>
			{/if}

			<!-- Results -->
			{#if opLoading}
				<TableSkeleton rows={5} columns={4} />
			{:else if opResults && opData.length > 0}
				<!-- Toolbar -->
				<div class="flex items-center gap-2">
					<Input
						placeholder="Filter operations..."
						value={(opTable.getColumn('path')?.getFilterValue() as string) ?? ''}
						oninput={(e) => opTable.getColumn('path')?.setFilterValue(e.currentTarget.value)}
						class="max-w-sm"
					/>
					<span class="text-sm text-muted-foreground">
						{opResults.status.totalResults.toLocaleString()} operations found
					</span>
					<DropdownMenu.Root>
						<DropdownMenu.Trigger>
							{#snippet child({ props })}
								<Button {...props} variant="outline" class="ml-auto">
									Columns <ChevronDown class="ml-2 size-4" />
								</Button>
							{/snippet}
						</DropdownMenu.Trigger>
						<DropdownMenu.Content align="end">
							{#each opTable
								.getAllColumns()
								.filter((col) => col.getCanHide()) as column (column.id)}
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

				<!-- Table -->
				<div class="rounded-md border">
					<Table.Root>
						<Table.Header>
							{#each opTable.getHeaderGroups() as headerGroup (headerGroup.id)}
								<Table.Row>
									{#each headerGroup.headers as header (header.id)}
										<Table.Head>
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
							{#each opTable.getRowModel().rows as row (row.id)}
								<Table.Row>
									{#each row.getVisibleCells() as cell (cell.id)}
										<Table.Cell>
											<FlexRender
												content={cell.column.columnDef.cell}
												context={cell.getContext()}
											/>
										</Table.Cell>
									{/each}
								</Table.Row>
							{:else}
								<Table.Row>
									<Table.Cell colspan={opColumns.length} class="h-24 text-center">
										No operations found.
									</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>

				<!-- Pagination -->
				<div class="flex items-center justify-end space-x-2">
					<div class="flex-1 text-sm text-muted-foreground">
						{opTable.getFilteredRowModel().rows.length} operation(s) shown.
					</div>
				</div>
			{:else if opSearched && !opError}
				<div class="rounded-lg border border-dashed p-8 text-center">
					<Activity class="mx-auto h-10 w-10 text-muted-foreground/50" />
					<p class="mt-2 text-muted-foreground">No operations found.</p>
				</div>
			{:else if !opSearched}
				<div class="rounded-lg border border-dashed p-8 text-center">
					<Activity class="mx-auto h-10 w-10 text-muted-foreground/50" />
					<p class="mt-2 text-muted-foreground">
						Select operation types and click Search to view audit events.
					</p>
				</div>
			{/if}
		{/if}
	{:else}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to search.</p>
		</div>
	{/if}
</div>
