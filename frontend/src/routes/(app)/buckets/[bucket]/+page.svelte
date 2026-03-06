<script lang="ts">
	import { page } from '$app/state';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import {
		Upload,
		Trash2,
		Download,
		Folder,
		FileText,
		Image,
		FileArchive,
		FileCode,
		Loader2,
		Search,
		ChevronLeft,
		ChevronRight,
	} from 'lucide-svelte';
	import type {
		ColumnDef,
		SortingState,
		PaginationState,
		ColumnFiltersState,
	} from '@tanstack/table-core';
	import FileViewer from '$lib/components/ui/FileViewer.svelte';
	import {
		formatBytes,
		formatDate,
		parseQuotaBytes,
		getStorageUsed,
		calcQuotaPercent,
	} from '$lib/utils/format.js';
	import type { ChargebackEntry } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import BackButton from '$lib/components/ui/back-button.svelte';
	import StorageProgressBar from '$lib/components/ui/storage-progress-bar.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import BulkDeleteDialog from '$lib/components/ui/bulk-delete-dialog.svelte';
	import {
		get_objects,
		delete_object,
		bulk_delete_objects,
		bulk_presign,
	} from '$lib/buckets.remote.js';
	import { get_tenant_chargeback } from '$lib/tenant-info.remote.js';
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
	import DataTableActions from './data-table/data-table-actions.svelte';
	import BucketUploadDialog from './sections/bucket-upload-dialog.svelte';
	import BucketShareDialog from './sections/bucket-share-dialog.svelte';
	import BucketCopyDialog from './sections/bucket-copy-dialog.svelte';
	import BucketVersioning from './sections/bucket-versioning.svelte';
	import BucketAcl from './sections/bucket-acl.svelte';

	let tenant = $derived(page.data.tenant as string | undefined);
	let chargebackData = $derived(tenant ? get_tenant_chargeback({ tenant }) : undefined);
	let nsData = $derived(tenant ? get_namespaces({ tenant }) : undefined);

	let bucket = $derived(page.params.bucket ?? '');

	let bucketStorageUsed = $derived(
		getStorageUsed((chargebackData?.current?.chargebackData ?? []) as ChargebackEntry[], bucket)
	);
	let bucketQuotaStr = $derived.by(() => {
		const nsList = (nsData?.current ?? []) as Namespace[];
		const ns = nsList.find((n) => n.name === bucket);
		return ns?.hardQuota ?? null;
	});
	let bucketQuotaBytes = $derived(bucketQuotaStr ? parseQuotaBytes(bucketQuotaStr) : null);
	let bucketQuotaPercent = $derived(calcQuotaPercent(bucketStorageUsed, bucketQuotaStr));

	// --- Server-side pagination with continuation tokens ---
	let prefix = $derived(page.url.searchParams.get('prefix') ?? '');
	let continuationToken = $state<string | undefined>(undefined);
	let tokenHistory = $state<string[]>([]);

	let objectData = $derived(get_objects({ bucket, prefix, continuation_token: continuationToken }));

	let isTruncated = $derived(objectData.current?.isTruncated ?? false);
	let nextToken = $derived(objectData.current?.nextToken ?? null);

	function loadNextPage() {
		if (!nextToken) return;
		tokenHistory = [...tokenHistory, continuationToken ?? ''];
		continuationToken = nextToken;
	}

	function loadPrevPage() {
		if (tokenHistory.length === 0) return;
		const prev = tokenHistory[tokenHistory.length - 1];
		tokenHistory = tokenHistory.slice(0, -1);
		continuationToken = prev || undefined;
	}

	function resetPagination() {
		continuationToken = undefined;
		tokenHistory = [];
	}

	// Reset server pagination when prefix changes
	$effect(() => {
		void prefix;
		resetPagination();
	});

	// --- S3 Object type ---
	interface S3Object {
		key: string;
		size: number;
		last_modified: string;
		etag: string;
		storage_class: string;
		owner: { display_name?: string; id?: string; DisplayName?: string; ID?: string } | null;
	}

	function getOwnerName(obj: S3Object): string {
		return obj.owner?.display_name ?? obj.owner?.DisplayName ?? '';
	}

	// --- Object list ---
	let rawObjects = $derived((objectData.current?.objects ?? []) as S3Object[]);
	let commonPrefixes = $derived((objectData.current?.commonPrefixes ?? []) as string[]);
	let folderEntries = $derived(
		commonPrefixes.map(
			(p): S3Object => ({
				key: p,
				size: 0,
				last_modified: '',
				etag: '',
				storage_class: '',
				owner: null,
			})
		)
	);
	let objects = $derived([...folderEntries, ...rawObjects]);

	function navigatePrefix(p: string) {
		goto(`/buckets/${bucket}?prefix=${encodeURIComponent(p)}`);
	}
	function downloadUrl(key: string): string {
		return `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${encodeURIComponent(key)}`;
	}
	function getDisplayName(key: string): string {
		return key.split('/').filter(Boolean).pop() ?? key;
	}
	function isObjFolder(obj: S3Object): boolean {
		return obj.size === 0 && obj.key.endsWith('/');
	}

	function getFileIcon(name: string) {
		const ext = name.split('.').pop()?.toLowerCase() ?? '';
		if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return Image;
		if (['zip', 'tar', 'gz', 'rar', '7z'].includes(ext)) return FileArchive;
		if (['js', 'ts', 'py', 'json', 'html', 'css', 'xml', 'yaml', 'yml', 'toml'].includes(ext))
			return FileCode;
		return FileText;
	}

	// --- Filters (client-side within the loaded page) ---
	let search = $state('');
	let ownerFilter = $state('');
	let sizeFilter = $state('');

	let uniqueOwners = $derived([...new Set(rawObjects.map(getOwnerName).filter(Boolean))]);

	let filteredObjects = $derived(
		objects.filter((obj) => {
			if (search) {
				const q = search.toLowerCase();
				if (
					!getDisplayName(obj.key).toLowerCase().includes(q) &&
					!obj.key.toLowerCase().includes(q)
				)
					return false;
			}
			if (ownerFilter && getOwnerName(obj) !== ownerFilter && !isObjFolder(obj)) return false;
			if (sizeFilter && !isObjFolder(obj)) {
				const s = obj.size;
				if (sizeFilter === '<1KB' && s >= 1024) return false;
				if (sizeFilter === '1KB-1MB' && (s < 1024 || s >= 1048576)) return false;
				if (sizeFilter === '1MB-100MB' && (s < 1048576 || s >= 104857600)) return false;
				if (sizeFilter === '>100MB' && s < 104857600) return false;
			}
			return true;
		})
	);

	let hasActiveFilters = $derived(!!ownerFilter || !!sizeFilter);
	function clearFilters() {
		ownerFilter = '';
		sizeFilter = '';
	}

	// --- TanStack Table with sorting + client pagination ---
	let sorting = $state<SortingState>([]);
	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 50 });

	let selectableObjects = $derived(filteredObjects.filter((obj) => !isObjFolder(obj)));

	// Row selection via TanStack
	let rowSelection = $state<Record<string, boolean>>({});

	let selectedKeys = $derived(
		Object.entries(rowSelection)
			.filter(([, v]) => v)
			.map(([idx]) => {
				const row = objTable.getRowModel().rows[Number(idx)];
				return row?.original.key;
			})
			.filter((k): k is string => !!k && !k.endsWith('/'))
	);

	let objColumns = $derived.by((): ColumnDef<S3Object>[] => [
		{
			id: 'select',
			header: ({ table }) =>
				renderComponent(DataTableCheckbox, {
					checked: table.getIsAllPageRowsSelected(),
					indeterminate: table.getIsSomePageRowsSelected() && !table.getIsAllPageRowsSelected(),
					onCheckedChange: (value: boolean) => table.toggleAllPageRowsSelected(!!value),
				}),
			cell: ({ row }) =>
				isObjFolder(row.original)
					? ('' as string)
					: renderComponent(DataTableCheckbox, {
							checked: row.getIsSelected(),
							onCheckedChange: (value: boolean) => row.toggleSelected(!!value),
						}),
			enableSorting: false,
			enableHiding: false,
			meta: { headerClass: 'w-10 px-4 py-3', cellClass: 'px-4 py-3' },
		},
		{
			id: 'name',
			accessorFn: (row) => getDisplayName(row.key),
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Name',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => renderSnippet(nameCellSnippet, row.original),
		},
		{
			id: 'key',
			header: 'Key',
			cell: ({ row }) => renderSnippet(keyCellSnippet, row.original),
			enableSorting: false,
		},
		{
			id: 'owner',
			accessorFn: (row) => getOwnerName(row),
			header: 'Owner',
			cell: ({ row }) =>
				(isObjFolder(row.original) ? '-' : getOwnerName(row.original) || '-') as string,
			meta: { headerClass: 'w-32 px-4 py-3', cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'size',
			accessorFn: (row) => row.size,
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Size',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) =>
				(isObjFolder(row.original) ? '-' : formatBytes(row.original.size)) as string,
			meta: { headerClass: 'w-32 px-4 py-3', cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'lastModified',
			accessorFn: (row) => row.last_modified,
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Modified',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) =>
				(row.original.last_modified ? formatDate(row.original.last_modified) : '-') as string,
			meta: { headerClass: 'w-48 px-4 py-3', cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'actions',
			header: '',
			cell: ({ row }) => renderSnippet(actionsCellSnippet, row.original),
			enableSorting: false,
			meta: { headerClass: 'w-16 px-4 py-3', cellClass: 'px-4 py-3' },
		},
	]);

	let objTable = $derived(
		createSvelteTable({
			get data() {
				return filteredObjects;
			},
			get columns() {
				return objColumns;
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
			enableRowSelection: (row) => !isObjFolder(row.original),
		})
	);

	let currentPage = $derived(pagination.pageIndex + 1);
	let totalPages = $derived(objTable.getPageCount());
	let serverPage = $derived(tokenHistory.length + 1);

	// --- Delete ---
	let deleteDialogOpen = $state(false);
	let deleteTarget = $state('');
	let deleting = $state(false);
	let bulkDeleteOpen = $state(false);

	function requestDelete(key: string) {
		deleteTarget = key;
		deleteDialogOpen = true;
	}

	async function handleConfirmDelete() {
		deleting = true;
		try {
			await delete_object({ bucket, key: deleteTarget }).updates(objectData);
			deleteDialogOpen = false;
			toast.success('Object deleted');
		} catch {
			toast.error('Failed to delete object');
		} finally {
			deleting = false;
		}
	}

	async function handleConfirmBulkDelete() {
		const keys = selectedKeys;
		if (keys.length === 0) return;
		deleting = true;
		try {
			await bulk_delete_objects({ bucket, keys }).updates(objectData);
			rowSelection = {};
			bulkDeleteOpen = false;
			toast.success(`Deleted ${keys.length} object${keys.length !== 1 ? 's' : ''}`);
		} catch {
			toast.error('Failed to delete objects');
		} finally {
			deleting = false;
		}
	}

	// --- Dialogs ---
	let uploadOpen = $state(false);
	let shareTarget = $state<string | null>(null);
	let copyTarget = $state<string | null>(null);
	let downloading = $state(false);

	async function bulkDownload() {
		const keys = selectedKeys;
		if (keys.length === 0) return;
		downloading = true;
		try {
			const result = await bulk_presign({ bucket, keys, expires_in: 3600 });
			for (const item of result.urls) {
				const a = document.createElement('a');
				a.href = item.url;
				a.download = item.key.split('/').pop() ?? item.key;
				a.style.display = 'none';
				document.body.appendChild(a);
				a.click();
				document.body.removeChild(a);
				await new Promise((r) => setTimeout(r, 150));
			}
			toast.success(
				`Started downloading ${result.urls.length} file${result.urls.length !== 1 ? 's' : ''}`
			);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to download objects');
		} finally {
			downloading = false;
		}
	}

	// --- File Viewer ---
	let viewerOpen = $state(false);
	let viewerIndex = $state(-1);

	let viewerObject = $derived(viewerIndex >= 0 ? selectableObjects[viewerIndex] : undefined);
	let viewerUrl = $derived(viewerObject ? downloadUrl(viewerObject.key) : '');
	let viewerFilename = $derived(viewerObject ? getDisplayName(viewerObject.key) : '');
	let viewerSize = $derived(viewerObject?.size ?? 0);
	let viewerHasPrev = $derived(viewerIndex > 0);
	let viewerHasNext = $derived(viewerIndex < selectableObjects.length - 1);

	function openViewer(obj: { key: string; size: number }) {
		viewerIndex = selectableObjects.findIndex((o) => o.key === obj.key);
		viewerOpen = true;
	}

	let parentPrefix = $derived.by(() => {
		if (!prefix) return '';
		const parts = prefix.replace(/\/$/, '').split('/');
		parts.pop();
		return parts.length > 0 ? parts.join('/') + '/' : '';
	});

	function handleRowClick(obj: S3Object) {
		if (isObjFolder(obj)) {
			navigatePrefix(obj.key);
		} else {
			openViewer(obj);
		}
	}
</script>

{#snippet nameCellSnippet(obj: S3Object)}
	<span class="flex items-center gap-2">
		{#if isObjFolder(obj)}
			<Folder class="h-4 w-4 text-amber-500" />
		{:else}
			{@const Icon = getFileIcon(obj.key)}
			<Icon class="h-4 w-4 text-muted-foreground" />
		{/if}
		<span class="font-medium">{getDisplayName(obj.key)}</span>
	</span>
{/snippet}

{#snippet keyCellSnippet(obj: S3Object)}
	<Tooltip.Root>
		<Tooltip.Trigger>
			{#snippet child({ props })}
				<span class="block max-w-xs truncate font-mono text-xs text-muted-foreground" {...props}
					>{obj.key}</span
				>
			{/snippet}
		</Tooltip.Trigger>
		<Tooltip.Content class="max-w-lg break-all font-mono text-xs">{obj.key}</Tooltip.Content>
	</Tooltip.Root>
{/snippet}

{#snippet actionsCellSnippet(obj: S3Object)}
	<span
		onclick={(e: MouseEvent) => e.stopPropagation()}
		onkeydown={(e: KeyboardEvent) => e.stopPropagation()}
		role="presentation"
	>
		{#if !isObjFolder(obj)}
			<DataTableActions
				objectKey={obj.key}
				downloadUrl={downloadUrl(obj.key)}
				ondelete={() => requestDelete(obj.key)}
				onshare={() => (shareTarget = obj.key)}
				onview={() => openViewer(obj)}
				oncopy={() => (copyTarget = obj.key)}
			/>
		{/if}
	</span>
{/snippet}

<svelte:head><title>{bucket} - HCP Admin Console</title></svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-4">
			<BackButton href="/buckets" label="Back to buckets" />
			<div>
				<h2 class="text-2xl font-bold">{bucket}</h2>
				{#if prefix}<p class="mt-1 text-sm text-muted-foreground">
						<code class="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{prefix}</code>
					</p>{/if}
			</div>
			{#await objectData then od}
				<Badge variant="secondary">{od.keyCount} objects</Badge>
			{/await}
			{#if tenant && (bucketStorageUsed > 0 || bucketQuotaBytes)}
				<Tooltip.Root>
					<Tooltip.Trigger>
						{#snippet child({ props })}
							<span class="flex items-center gap-1.5 text-xs text-muted-foreground" {...props}>
								<span
									>{formatBytes(bucketStorageUsed)}{bucketQuotaStr
										? ` / ${bucketQuotaStr}`
										: ''}</span
								>
								{#if bucketQuotaPercent !== null}
									<StorageProgressBar percent={bucketQuotaPercent} class="w-16" />
								{/if}
							</span>
						{/snippet}
					</Tooltip.Trigger>
					<Tooltip.Content>Bucket storage usage</Tooltip.Content>
				</Tooltip.Root>
			{/if}
			<BucketVersioning {bucket} />
		</div>
		<Button onclick={() => (uploadOpen = true)}><Upload class="h-4 w-4" />Upload Files</Button>
	</div>

	{#if prefix}<Button
			variant="link"
			class="h-auto gap-2 p-0 text-sm"
			onclick={() => navigatePrefix(parentPrefix)}
			><Folder class="h-4 w-4" />.. (parent directory)</Button
		>{/if}

	<!-- Object Table -->
	{#await objectData}
		<TableSkeleton rows={5} columns={7} />
	{:then}
		<div class="space-y-2">
			<div class="relative">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<Input bind:value={search} placeholder="Search objects..." class="pl-10" />
			</div>
			<div class="flex flex-wrap items-center gap-2">
				{#if uniqueOwners.length > 0}
					<Select.Root type="single" bind:value={ownerFilter}>
						<Select.Trigger class="h-8 w-auto min-w-[120px] px-2 text-xs">
							{ownerFilter || 'All owners'}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="">All owners</Select.Item>
							{#each uniqueOwners as o (o)}<Select.Item value={o}>{o}</Select.Item>{/each}
						</Select.Content>
					</Select.Root>
				{/if}
				<Select.Root type="single" bind:value={sizeFilter}>
					<Select.Trigger class="h-8 w-auto min-w-[120px] px-2 text-xs">
						{sizeFilter || 'All sizes'}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="">All sizes</Select.Item>
						<Select.Item value="<1KB">&lt; 1 KB</Select.Item>
						<Select.Item value="1KB-1MB">1 KB - 1 MB</Select.Item>
						<Select.Item value="1MB-100MB">1 MB - 100 MB</Select.Item>
						<Select.Item value=">100MB">&gt; 100 MB</Select.Item>
					</Select.Content>
				</Select.Root>
				{#if hasActiveFilters}
					<Button variant="ghost" size="sm" class="h-7 px-2 text-xs" onclick={clearFilters}>
						Clear filters
					</Button>
				{/if}
				<span class="ml-auto text-xs text-muted-foreground"
					>{filteredObjects.length} items{isTruncated ? ' (more available)' : ''}</span
				>
			</div>
		</div>

		{#if selectedKeys.length > 0}
			<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
				<span class="text-sm font-medium">{selectedKeys.length} selected</span>
				<Button size="sm" onclick={bulkDownload} disabled={downloading}
					>{#if downloading}<Loader2 class="h-3.5 w-3.5 animate-spin" />{:else}<Download
							class="h-3.5 w-3.5"
						/>{/if}Download Selected</Button
				>
				<Button variant="destructive" size="sm" onclick={() => (bulkDeleteOpen = true)}
					><Trash2 class="h-3.5 w-3.5" />Delete Selected</Button
				>
				<Button variant="ghost" size="sm" onclick={() => (rowSelection = {})}>Deselect All</Button>
			</div>
		{/if}

		<DataTable
			table={objTable}
			onrowclick={handleRowClick}
			noResultsMessage={objects.length === 0
				? 'No objects in this bucket'
				: `No results matching "${search}"`}
		/>

		<!-- Pagination controls -->
		<div class="flex items-center justify-between">
			<div class="text-sm text-muted-foreground">
				{#if objTable.getFilteredSelectedRowModel().rows.length > 0}
					{objTable.getFilteredSelectedRowModel().rows.length} of{' '}
					{objTable.getFilteredRowModel().rows.length} row(s) selected.
				{/if}
			</div>
			<div class="flex items-center gap-4">
				<!-- Client-side pagination within loaded data -->
				{#if totalPages > 1}
					<div class="flex items-center gap-2">
						<span class="text-xs text-muted-foreground">
							Page {currentPage} of {totalPages}
						</span>
						<Button
							variant="outline"
							size="icon"
							class="h-8 w-8"
							onclick={() => objTable.previousPage()}
							disabled={!objTable.getCanPreviousPage()}
						>
							<ChevronLeft class="h-4 w-4" />
						</Button>
						<Button
							variant="outline"
							size="icon"
							class="h-8 w-8"
							onclick={() => objTable.nextPage()}
							disabled={!objTable.getCanNextPage()}
						>
							<ChevronRight class="h-4 w-4" />
						</Button>
					</div>
				{/if}

				<!-- Server-side pagination (load more from S3) -->
				{#if isTruncated || tokenHistory.length > 0}
					<div class="flex items-center gap-2 border-l pl-4">
						<span class="text-xs text-muted-foreground">Batch {serverPage}</span>
						<Button
							variant="outline"
							size="sm"
							class="h-8"
							onclick={loadPrevPage}
							disabled={tokenHistory.length === 0}
						>
							Previous batch
						</Button>
						<Button
							variant="outline"
							size="sm"
							class="h-8"
							onclick={loadNextPage}
							disabled={!isTruncated}
						>
							Next batch
						</Button>
					</div>
				{/if}
			</div>
		</div>
	{/await}

	<!-- Bucket ACL -->
	<BucketAcl {bucket} />
</div>

<!-- Dialogs -->
<BucketUploadDialog
	bind:open={uploadOpen}
	{bucket}
	{prefix}
	onuploaded={() => objectData.refresh()}
/>

<BucketShareDialog {bucket} bind:target={shareTarget} />

<BucketCopyDialog {bucket} bind:target={copyTarget} oncopied={() => objectData.refresh()} />

{#if viewerOpen}<FileViewer
		bind:open={viewerOpen}
		url={viewerUrl}
		filename={viewerFilename}
		size={viewerSize}
		objectKey={viewerObject?.key}
		lastModified={viewerObject?.last_modified}
		etag={viewerObject?.etag}
		storageClass={viewerObject?.storage_class}
		hasPrev={viewerHasPrev}
		hasNext={viewerHasNext}
		onprev={() => {
			if (viewerHasPrev) viewerIndex--;
		}}
		onnext={() => {
			if (viewerHasNext) viewerIndex++;
		}}
		currentIndex={viewerIndex}
		totalCount={selectableObjects.length}
		onclose={() => (viewerOpen = false)}
	/>{/if}

<DeleteConfirmDialog
	bind:open={deleteDialogOpen}
	name={deleteTarget ? getDisplayName(deleteTarget) : ''}
	itemType="object"
	loading={deleting}
	onconfirm={handleConfirmDelete}
/>

<BulkDeleteDialog
	bind:open={bulkDeleteOpen}
	count={selectedKeys.length}
	itemType="object"
	loading={deleting}
	onconfirm={handleConfirmBulkDelete}
/>
