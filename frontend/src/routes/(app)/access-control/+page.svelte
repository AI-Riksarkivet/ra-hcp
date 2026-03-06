<script lang="ts">
	import { goto } from '$app/navigation';
	import { Shield, Search } from 'lucide-svelte';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import PageHeader from '$lib/components/ui/page-header.svelte';
	import { get_buckets, get_bucket_acl, type AclGrant, type AclData } from '$lib/buckets.remote.js';
	import {
		DataTable,
		DataTableCheckbox,
		DataTableHeaderButton,
		createSvelteTable,
		getCoreRowModel,
		getSortedRowModel,
		getPaginationRowModel,
		renderSnippet,
		renderComponent,
	} from '$lib/components/ui/data-table/index.js';
	import type { ColumnDef, SortingState, PaginationState } from '@tanstack/table-core';
	import { SvelteMap } from 'svelte/reactivity';

	type BucketAclRow = {
		name: string;
		owner: string;
		grants: AclGrant[];
		grantCount: number;
		permissions: string[];
	};

	// --- Data fetching ---
	let bucketData = get_buckets();
	let buckets = $derived(
		(bucketData.current?.buckets ?? []) as { name: string; creation_date: string }[]
	);

	// Fetch ACL for each bucket using a reactive map
	let bucketAcls = $derived.by(() => {
		const map = new SvelteMap<string, ReturnType<typeof get_bucket_acl>>();
		for (const b of buckets) {
			map.set(b.name, get_bucket_acl({ bucket: b.name }));
		}
		return map;
	});

	// Derive table rows from fetched ACLs
	let rows = $derived.by((): BucketAclRow[] => {
		const result: BucketAclRow[] = [];
		for (const b of buckets) {
			const aclQuery = bucketAcls.get(b.name);
			const acl = (aclQuery?.current ?? { owner: null, grants: [] }) as AclData;
			const grants = acl.grants ?? [];
			const permissions = [...new Set(grants.map((g) => g.Permission ?? '').filter(Boolean))];
			result.push({
				name: b.name,
				owner: acl.owner?.DisplayName || acl.owner?.ID || '',
				grants,
				grantCount: grants.length,
				permissions,
			});
		}
		return result;
	});

	// --- Search filter ---
	let search = $state('');
	let filteredRows = $derived(
		rows.filter((r) => {
			if (search && !r.name.toLowerCase().includes(search.toLowerCase())) return false;
			return true;
		})
	);

	// --- Permission helpers ---
	function permissionColor(p: string): 'default' | 'secondary' | 'destructive' | 'outline' {
		if (p === 'FULL_CONTROL') return 'destructive';
		if (p === 'WRITE' || p === 'WRITE_ACP') return 'default';
		return 'secondary';
	}

	function permissionLabel(p: string): string {
		const labels: Record<string, string> = {
			FULL_CONTROL: 'Full Control',
			READ: 'Read',
			WRITE: 'Write',
			READ_ACP: 'Read ACP',
			WRITE_ACP: 'Write ACP',
		};
		return labels[p] ?? p;
	}

	// --- TanStack Table state ---
	let sorting = $state<SortingState>([]);
	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 20 });
	let rowSelection = $state<Record<string, boolean>>({});

	let selectedCount = $derived(Object.values(rowSelection).filter(Boolean).length);

	// --- TanStack Table columns ---
	let columns = $derived.by((): ColumnDef<BucketAclRow>[] => [
		{
			id: 'select',
			header: ({ table }) =>
				renderComponent(DataTableCheckbox, {
					checked: table.getIsAllPageRowsSelected(),
					onCheckedChange: (val: boolean) => table.toggleAllPageRowsSelected(!!val),
				}),
			cell: ({ row }) =>
				renderComponent(DataTableCheckbox, {
					checked: row.getIsSelected(),
					onCheckedChange: (val: boolean) => row.toggleSelected(!!val),
				}),
			meta: { headerClass: 'w-10', cellClass: 'px-4 py-3' },
		},
		{
			accessorKey: 'name',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Bucket',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => renderSnippet(bucketNameCell, row.original),
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			accessorKey: 'owner',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Owner',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => (row.original.owner || '-') as string,
			meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'grants',
			header: 'Grants',
			cell: ({ row }) => renderSnippet(grantsCell, row.original),
			meta: { cellClass: 'px-4 py-3' },
		},
		{
			id: 'permissions',
			header: 'Permissions',
			cell: ({ row }) => renderSnippet(permissionsCell, row.original),
			meta: { cellClass: 'px-4 py-3' },
		},
		{
			id: 'actions',
			header: '',
			cell: ({ row }) => renderSnippet(actionsCell, row.original),
			meta: { headerClass: 'w-28', cellClass: 'px-4 py-3' },
		},
	]);

	let table = $derived(
		createSvelteTable({
			get data() {
				return filteredRows;
			},
			get columns() {
				return columns;
			},
			state: {
				get sorting() {
					return sorting;
				},
				get pagination() {
					return pagination;
				},
				get rowSelection() {
					return rowSelection;
				},
			},
			onSortingChange: (updater) => {
				sorting = typeof updater === 'function' ? updater(sorting) : updater;
			},
			onPaginationChange: (updater) => {
				pagination = typeof updater === 'function' ? updater(pagination) : updater;
			},
			onRowSelectionChange: (updater) => {
				rowSelection = typeof updater === 'function' ? updater(rowSelection) : updater;
			},
			getCoreRowModel: getCoreRowModel(),
			getSortedRowModel: getSortedRowModel(),
			getPaginationRowModel: getPaginationRowModel(),
			enableRowSelection: true,
		})
	);

	let noResultsMessage = $derived(
		buckets.length === 0 ? 'No buckets found.' : `No results matching "${search}"`
	);
</script>

{#snippet bucketNameCell(row: BucketAclRow)}
	<a
		href="/buckets/{row.name}"
		class="text-primary underline-offset-4 hover:underline"
		onclick={(e) => {
			e.stopPropagation();
		}}
	>
		{row.name}
	</a>
{/snippet}

{#snippet grantsCell(row: BucketAclRow)}
	<Badge variant="outline">{row.grantCount}</Badge>
{/snippet}

{#snippet permissionsCell(row: BucketAclRow)}
	{#if row.permissions.length > 0}
		<div class="flex flex-wrap gap-1">
			{#each row.permissions as perm (perm)}
				<Badge variant={permissionColor(perm)}>{permissionLabel(perm)}</Badge>
			{/each}
		</div>
	{:else}
		<span class="text-muted-foreground">-</span>
	{/if}
{/snippet}

{#snippet actionsCell(row: BucketAclRow)}
	<Button
		variant="ghost"
		size="sm"
		onclick={(e) => {
			e.stopPropagation();
			goto(`/buckets/${row.name}`);
		}}
	>
		View Details
	</Button>
{/snippet}

<svelte:head>
	<title>Access Control - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<PageHeader title="Access Control" description="Overview of S3 bucket access control lists">
		{#snippet actions()}
			<Shield class="h-5 w-5 text-muted-foreground" />
		{/snippet}
	</PageHeader>

	{#await bucketData}
		<TableSkeleton rows={5} columns={6} />
	{:then}
		<div class="space-y-2">
			<div class="relative">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<Input bind:value={search} placeholder="Search buckets..." class="pl-10" />
			</div>
			<div class="flex items-center">
				<span class="ml-auto text-xs text-muted-foreground">
					{filteredRows.length} of {rows.length} buckets
				</span>
			</div>
		</div>

		{#if selectedCount > 0}
			<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
				<span class="text-sm font-medium">{selectedCount} selected</span>
				<Button variant="ghost" size="sm" onclick={() => (rowSelection = {})}>Deselect All</Button>
			</div>
		{/if}

		<DataTable {table} onrowclick={(row) => goto(`/buckets/${row.name}`)} {noResultsMessage}>
			{#snippet footer()}
				{#if selectedCount > 0}
					{selectedCount} of {filteredRows.length} row(s) selected.
				{/if}
			{/snippet}
		</DataTable>
	{/await}
</div>
