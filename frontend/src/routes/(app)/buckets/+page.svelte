<script lang="ts">
	import { page } from '$app/state';
	import { Plus, Trash2, Search } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import {
		formatDate,
		formatBytes,
		parseQuotaBytes,
		buildStorageMap,
		calcQuotaPercent,
		matchesDateFilter,
	} from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { useDelete } from '$lib/utils/use-delete.svelte.js';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import BulkDeleteDialog from '$lib/components/ui/bulk-delete-dialog.svelte';
	import PageHeader from '$lib/components/ui/page-header.svelte';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import StorageProgressBar from '$lib/components/ui/storage-progress-bar.svelte';
	import { get_buckets, create_bucket, delete_bucket } from '$lib/buckets.remote.js';
	import {
		get_tenant,
		get_tenant_statistics,
		get_tenant_chargeback,
	} from '$lib/tenant-info.remote.js';
	import { get_namespaces, type Namespace } from '$lib/namespaces.remote.js';
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
	import DataTableActions from './data-table/data-table-actions.svelte';

	type BucketRow = { name: string; creation_date: string };

	let tenant = $derived(page.data.tenant as string | undefined);
	let tenantInfo = $derived(tenant ? get_tenant({ tenant }) : undefined);
	let tenantStats = $derived(tenant ? get_tenant_statistics({ tenant }) : undefined);
	let chargebackData = $derived(tenant ? get_tenant_chargeback({ tenant }) : undefined);
	let nsData = $derived(tenant ? get_namespaces({ tenant }) : undefined);

	let tenantQuotaPercent = $derived(
		calcQuotaPercent(
			Number(tenantStats?.current?.storageCapacityUsed ?? 0),
			tenantInfo?.current?.hardQuota
		)
	);

	let chargeback = $derived(chargebackData?.current?.chargebackData ?? []);
	let namespaces = $derived((nsData?.current ?? []) as Namespace[]);

	let bucketStorageMap = $derived(buildStorageMap(chargeback));

	// Map bucket/namespace name -> hard quota from namespace info
	let bucketQuotaMap = $derived.by(() => {
		const map = new Map<string, string>();
		for (const ns of namespaces) {
			if (ns.hardQuota) map.set(ns.name, ns.hardQuota);
		}
		return map;
	});

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

	let search = $state('');
	let dateFilter = $state('');
	let buckets = $derived((bucketData.current?.buckets ?? []) as BucketRow[]);

	let filteredBuckets = $derived(
		buckets.filter((b) => {
			if (search && !b.name.toLowerCase().includes(search.toLowerCase())) return false;
			if (dateFilter && !matchesDateFilter(b.creation_date, dateFilter)) return false;
			return true;
		})
	);

	// --- TanStack Table state ---
	let sorting = $state<SortingState>([]);
	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 25 });
	let rowSelection = $state<Record<string, boolean>>({});

	let selectedKeys = $derived(
		Object.keys(rowSelection)
			.filter((k) => rowSelection[k])
			.map((k) => table.getCoreRowModel().rows[Number(k)]?.original.name)
			.filter(Boolean) as string[]
	);
	let selectedCount = $derived(selectedKeys.length);

	const del = useDelete({ entityName: 'bucket' });

	function onConfirmDelete() {
		del.confirmDelete(() => delete_bucket({ bucket: del.deleteTarget }).updates(bucketData));
	}

	function onConfirmBulkDelete() {
		del.confirmBulkDelete(
			selectedKeys,
			(name, isLast) => {
				const call = delete_bucket({ bucket: name });
				return isLast ? call.updates(bucketData) : call;
			},
			() => {
				rowSelection = {};
			}
		);
	}

	// --- TanStack Table columns ---
	let columns = $derived.by((): ColumnDef<BucketRow>[] => {
		const cols: ColumnDef<BucketRow>[] = [
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
						label: 'Name',
						onclick: column.getToggleSortingHandler(),
					}),
				meta: { cellClass: 'px-4 py-3 font-medium' },
			},
		];

		if (tenant) {
			cols.push({
				id: 'storage',
				header: 'Storage Used',
				cell: ({ row }) => renderSnippet(storageCell, row.original),
				meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
			});
		}

		cols.push(
			{
				id: 'owner',
				header: 'Owner',
				cell: () => (ownerName || '-') as string,
				meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
			},
			{
				id: 'created',
				accessorFn: (row) => row.creation_date,
				header: ({ column }) =>
					renderComponent(DataTableHeaderButton, {
						label: 'Created',
						onclick: column.getToggleSortingHandler(),
					}),
				cell: ({ row }) => formatDate(row.original.creation_date) as string,
				meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
			},
			{
				id: 'actions',
				header: '',
				cell: ({ row }) =>
					renderComponent(DataTableActions, {
						name: row.original.name,
						ondelete: () => del.requestDelete(row.original.name),
						onnavigate: () => goto(`/buckets/${row.original.name}`),
					}),
				meta: { headerClass: 'w-16', cellClass: 'px-4 py-3' },
			}
		);

		return cols;
	});

	let table = $derived(
		createSvelteTable({
			get data() {
				return filteredBuckets;
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
		buckets.length === 0
			? 'No buckets found. Create one to get started.'
			: `No results matching "${search}"`
	);

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
</script>

{#snippet storageCell(bucket: BucketRow)}
	{@const used = bucketStorageMap.get(bucket.name) ?? 0}
	{@const quotaStr = bucketQuotaMap.get(bucket.name)}
	{@const quota = quotaStr ? parseQuotaBytes(quotaStr) : null}
	{#if used > 0 || quota}
		<div class="flex flex-col gap-1">
			<span class="text-sm">{formatBytes(used)}{quota ? ` / ${quotaStr}` : ''}</span>
			{#if quota}
				{@const pct = Math.min(100, (used / quota) * 100)}
				<StorageProgressBar percent={pct} class="max-w-24" />
			{/if}
		</div>
	{:else}
		—
	{/if}
{/snippet}

<svelte:head>
	<title>Buckets - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<PageHeader title="Buckets" description="Manage S3 buckets on your HCP system">
		{#snippet actions()}
			<Button onclick={() => (createOpen = true)}>
				<Plus class="h-4 w-4" />
				Create Bucket
			</Button>
		{/snippet}
	</PageHeader>

	<Dialog.Root bind:open={createOpen}>
		<Dialog.Content class="sm:max-w-md">
			<Dialog.Header><Dialog.Title>Create Bucket</Dialog.Title></Dialog.Header>
			<form onsubmit={handleCreate} class="space-y-4">
				<ErrorBanner message={createError} />
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
	{:then}
		<div class="space-y-2">
			<div class="relative">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<Input bind:value={search} placeholder="Search buckets..." class="pl-10" />
			</div>
			<div class="flex flex-wrap items-center gap-2">
				{#if ownerName}
					<Badge variant="outline">Owner: {ownerName}</Badge>
				{/if}
				<select
					class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-8 w-auto min-w-[120px] items-center rounded-md border px-2 py-1 text-xs shadow-sm focus:outline-none focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
					bind:value={dateFilter}
				>
					<option value="">All dates</option>
					<option value="24h">Last 24 hours</option>
					<option value="7d">Last 7 days</option>
					<option value="30d">Last 30 days</option>
				</select>
				{#if dateFilter}
					<Button
						variant="ghost"
						size="sm"
						class="h-7 px-2 text-xs"
						onclick={() => (dateFilter = '')}
					>
						Clear filters
					</Button>
				{/if}
				<span class="ml-auto flex items-center gap-3 text-xs text-muted-foreground">
					{#if tenant}
						{#await tenantStats then stats}
							{#await tenantInfo then info}
								{#if tenantQuotaPercent !== null}
									<span class="flex items-center gap-1.5">
										<span
											>{formatBytes(Number(stats?.storageCapacityUsed ?? 0))} / {info?.hardQuota}</span
										>
										<StorageProgressBar percent={tenantQuotaPercent} class="inline-block w-16" />
									</span>
									<span class="text-border">|</span>
								{/if}
							{/await}
						{/await}
					{/if}
					{filteredBuckets.length} of {buckets.length} buckets
				</span>
			</div>
		</div>

		{#if selectedCount > 0}
			<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
				<span class="text-sm font-medium">{selectedCount} selected</span>
				<Button variant="destructive" size="sm" onclick={() => del.requestBulkDelete()}>
					<Trash2 class="h-3.5 w-3.5" />Delete Selected
				</Button>
				<Button variant="ghost" size="sm" onclick={() => (rowSelection = {})}>Deselect All</Button>
			</div>
		{/if}

		<DataTable {table} onrowclick={(row) => goto(`/buckets/${row.name}`)} {noResultsMessage}>
			{#snippet footer()}
				{#if selectedCount > 0}
					{selectedCount} of {filteredBuckets.length} row(s) selected.
				{/if}
			{/snippet}
		</DataTable>
	{/await}
</div>

<DeleteConfirmDialog
	bind:open={del.deleteDialogOpen}
	name={del.deleteTarget}
	itemType="bucket"
	loading={del.deleting}
	onconfirm={onConfirmDelete}
/>

<BulkDeleteDialog
	bind:open={del.bulkDeleteOpen}
	count={selectedCount}
	itemType="bucket"
	loading={del.deleting}
	onconfirm={onConfirmBulkDelete}
/>
