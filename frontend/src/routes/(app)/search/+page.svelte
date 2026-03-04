<script lang="ts">
	import { page } from '$app/state';
	import {
		Search,
		FileSearch,
		Activity,
		ChevronLeft,
		ChevronRight,
		ArrowUpDown,
		ArrowUp,
		ArrowDown,
		HelpCircle,
		X,
	} from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
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

	// ── Object search state ──
	let objectQuery = $state('*:*');
	let pageSize = 25;
	let objectOffset = $state(0);
	let objectResults = $state<ObjectQueryResponse | null>(null);
	let objectLoading = $state(false);
	let objectError = $state('');
	let objectSearched = $state(false);

	// Sort state
	type SortField =
		| 'utf8Name'
		| 'namespace'
		| 'size'
		| 'contentType'
		| 'owner'
		| 'changeTimeMilliseconds';
	let sortField = $state<SortField | null>(null);
	let sortAsc = $state(true);

	// Column filter state
	let filterNamespace = $state('');
	let filterContentType = $state('');
	let filterOwner = $state('');

	// ── Operation search state ──
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

	// Client-side filtering of results
	let filteredResults = $derived.by(() => {
		if (!objectResults) return [];
		let items = objectResults.resultSet;
		if (filterNamespace) {
			const f = filterNamespace.toLowerCase();
			items = items.filter((i) => (i.namespace ?? '').toLowerCase().includes(f));
		}
		if (filterContentType) {
			const f = filterContentType.toLowerCase();
			items = items.filter((i) => (i.contentType ?? '').toLowerCase().includes(f));
		}
		if (filterOwner) {
			const f = filterOwner.toLowerCase();
			items = items.filter((i) => (i.owner ?? '').toLowerCase().includes(f));
		}
		return items;
	});

	let hasActiveFilters = $derived(
		filterNamespace !== '' || filterContentType !== '' || filterOwner !== ''
	);

	// Operation results sorted latest first
	let sortedOpResults = $derived.by(() => {
		if (!opResults) return [];
		return [...opResults.resultSet].sort(
			(a, b) => Number(b.changeTimeMilliseconds ?? 0) - Number(a.changeTimeMilliseconds ?? 0)
		);
	});

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

	async function handleObjectSearch() {
		if (!tenant) return;
		objectLoading = true;
		objectError = '';
		objectSearched = true;
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

	function toggleSort(field: SortField) {
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

	function clearFilters() {
		filterNamespace = '';
		filterContentType = '';
		filterOwner = '';
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

	const SORT_COLUMNS: { field: SortField; label: string; align?: 'right' }[] = [
		{ field: 'utf8Name', label: 'Path' },
		{ field: 'namespace', label: 'Namespace' },
		{ field: 'size', label: 'Size', align: 'right' },
		{ field: 'contentType', label: 'Content Type' },
		{ field: 'owner', label: 'Owner' },
		{ field: 'changeTimeMilliseconds', label: 'Modified' },
	];
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
				<HelpCircle class="h-4 w-4" />
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
								metadata for all objects stored across your namespaces. Results include file paths, sizes,
								content types, owners, and timestamps.
							</p>
							<div class="grid gap-4 sm:grid-cols-2">
								<div>
									<p class="mb-1.5 font-medium text-foreground">Query syntax</p>
									<p class="mb-2 text-muted-foreground">
										Queries use <code class="rounded bg-muted px-1">field:value</code> format. Use
										<code class="rounded bg-muted px-1">*:*</code> to match everything. Combine with
										<code class="rounded bg-muted px-1">AND</code>,
										<code class="rounded bg-muted px-1">OR</code>,
										<code class="rounded bg-muted px-1">NOT</code> operators.
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
											<code class="rounded bg-muted px-1">size:[1024 TO *]</code> — objects larger than
											1 KB
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
											— combine conditions
										</li>
									</ul>
								</div>
							</div>
							<p class="text-xs text-muted-foreground">
								Click column headers to sort results server-side. Use the filter inputs below
								headers to narrow results client-side within the current page.
							</p>
						</div>
					{:else}
						<div class="space-y-3 text-sm">
							<p class="text-foreground">
								<strong>Operation Search</strong> queries the HCP audit log for object lifecycle events.
								It shows when objects were created, deleted, or purged across your namespaces. This is
								useful for auditing changes and tracking data modifications.
							</p>
							<p class="text-muted-foreground">
								Use the operation type checkboxes to filter by event type. Optionally filter to a
								specific namespace. Results are sorted with the most recent operations first.
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
							placeholder="*:*"
							class="pl-9"
							onkeydown={(e) => e.key === 'Enter' && searchFromStart()}
						/>
					</div>
				</div>
				<Button onclick={searchFromStart} disabled={objectLoading}>
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
				<TableSkeleton rows={5} columns={6} />
			{:else if objectResults && objectResults.resultSet.length > 0}
				<div class="flex items-center justify-between text-sm text-muted-foreground">
					<span>
						{#if hasActiveFilters}
							{filteredResults.length} filtered /
						{/if}
						Showing {objectOffset + 1}–{Math.min(
							objectOffset + objectResults.resultSet.length,
							objectResults.status.totalResults
						)} of {objectResults.status.totalResults.toLocaleString()} results
					</span>
					{#if hasActiveFilters}
						<button
							class="flex items-center gap-1 text-xs text-primary hover:underline"
							onclick={clearFilters}
						>
							<X class="h-3 w-3" />
							Clear filters
						</button>
					{/if}
				</div>
				<div class="overflow-x-auto rounded-lg border">
					<table class="w-full text-left text-sm">
						<thead
							class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground"
						>
							<tr>
								{#each SORT_COLUMNS as col (col.field)}
									<th class="px-4 py-3 font-medium {col.align === 'right' ? 'text-right' : ''}">
										<button
											class="inline-flex items-center gap-1 hover:text-foreground"
											onclick={() => toggleSort(col.field)}
										>
											{col.label}
											{#if sortField === col.field}
												{#if sortAsc}
													<ArrowUp class="h-3 w-3" />
												{:else}
													<ArrowDown class="h-3 w-3" />
												{/if}
											{:else}
												<ArrowUpDown class="h-3 w-3 opacity-30" />
											{/if}
										</button>
									</th>
								{/each}
							</tr>
							<tr class="border-b bg-muted/30">
								<td class="px-4 py-1.5"></td>
								<td class="px-4 py-1.5">
									<input
										type="text"
										bind:value={filterNamespace}
										placeholder="Filter..."
										class="h-6 w-full rounded border border-input bg-background px-2 text-xs"
									/>
								</td>
								<td class="px-4 py-1.5"></td>
								<td class="px-4 py-1.5">
									<input
										type="text"
										bind:value={filterContentType}
										placeholder="Filter..."
										class="h-6 w-full rounded border border-input bg-background px-2 text-xs"
									/>
								</td>
								<td class="px-4 py-1.5">
									<input
										type="text"
										bind:value={filterOwner}
										placeholder="Filter..."
										class="h-6 w-full rounded border border-input bg-background px-2 text-xs"
									/>
								</td>
								<td class="px-4 py-1.5"></td>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each filteredResults as item (item.urlName + (item.version ?? ''))}
								<tr class="bg-card transition-colors hover:bg-accent/50">
									<td class="max-w-xs truncate px-4 py-3 font-medium" title={displayPath(item)}>
										{displayPath(item)}
									</td>
									<td class="px-4 py-3 text-muted-foreground">{item.namespace ?? '—'}</td>
									<td class="px-4 py-3 text-right text-muted-foreground">
										{item.size != null ? formatBytes(item.size) : '—'}
									</td>
									<td class="px-4 py-3 text-muted-foreground">{item.contentType ?? '—'}</td>
									<td class="px-4 py-3 text-muted-foreground">{item.owner ?? '—'}</td>
									<td class="whitespace-nowrap px-4 py-3 text-muted-foreground">
										{formatMillis(item.changeTimeMilliseconds)}
									</td>
								</tr>
							{:else}
								<tr>
									<td colspan="6" class="px-4 py-6 text-center text-muted-foreground">
										No results match your filters.
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>

				<!-- Pagination -->
				{#if objectTotalPages > 1}
					<div class="flex items-center justify-center gap-4">
						<Button
							variant="outline"
							size="sm"
							onclick={objectPagePrev}
							disabled={objectOffset === 0}
						>
							<ChevronLeft class="h-4 w-4" />
							Previous
						</Button>
						<span class="text-sm text-muted-foreground">
							Page {objectCurrentPage} of {objectTotalPages}
						</span>
						<Button
							variant="outline"
							size="sm"
							onclick={objectPageNext}
							disabled={objectCurrentPage >= objectTotalPages}
						>
							Next
							<ChevronRight class="h-4 w-4" />
						</Button>
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
			{:else if opResults && sortedOpResults.length > 0}
				<div class="text-sm text-muted-foreground">
					{opResults.status.totalResults.toLocaleString()} operations found
				</div>
				<div class="overflow-x-auto rounded-lg border">
					<table class="w-full text-left text-sm">
						<thead
							class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground"
						>
							<tr>
								<th class="px-4 py-3 font-medium">Path</th>
								<th class="px-4 py-3 font-medium">Operation</th>
								<th class="px-4 py-3 font-medium">Namespace</th>
								<th class="px-4 py-3 font-medium">Time</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each sortedOpResults as item (item.urlName + item.changeTimeMilliseconds)}
								<tr class="bg-card transition-colors hover:bg-accent/50">
									<td class="max-w-xs truncate px-4 py-3 font-medium" title={displayPath(item)}>
										{displayPath(item)}
									</td>
									<td class="px-4 py-3">
										<Badge variant={operationVariant(item.operation)}>
											{item.operation}
										</Badge>
									</td>
									<td class="px-4 py-3 text-muted-foreground">
										{item.namespace ?? '—'}
									</td>
									<td class="whitespace-nowrap px-4 py-3 text-muted-foreground">
										{formatMillis(item.changeTimeMilliseconds)}
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
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
