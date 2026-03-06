<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import {
		Plus,
		X,
		FileBox,
		HardDrive,
		Boxes,
		Users,
		ChartPie,
		Trash2,
		Search,
		ChevronLeft,
		ChevronRight,
	} from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { toast } from 'svelte-sonner';
	import { useDelete } from '$lib/utils/use-delete.svelte.js';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import StatCard from '$lib/components/ui/stat-card.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import BulkDeleteDialog from '$lib/components/ui/bulk-delete-dialog.svelte';
	import {
		get_namespaces,
		create_namespace,
		update_namespace,
		delete_namespace,
		type Namespace,
	} from '$lib/namespaces.remote.js';
	import {
		get_tenant,
		get_tenant_statistics,
		get_tenant_chargeback,
	} from '$lib/tenant-info.remote.js';
	import { get_users } from '$lib/users.remote.js';
	import {
		formatBytes,
		parseQuotaBytes,
		buildStorageMap,
		calcQuotaPercent,
		type ChargebackEntry,
	} from '$lib/utils/format.js';
	import PageHeader from '$lib/components/ui/page-header.svelte';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import StorageProgressBar from '$lib/components/ui/storage-progress-bar.svelte';
	import NoTenantPlaceholder from '$lib/components/ui/no-tenant-placeholder.svelte';
	import ServiceTagBadge from '$lib/components/ui/service-tag-badge.svelte';
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
	import DataTableTagCell from './data-table/data-table-tag-cell.svelte';

	let tenant = $derived(page.data.tenant as string | undefined);

	let nsData = $derived(tenant ? get_namespaces({ tenant }) : undefined);

	// Tenant stats
	let tenantInfo = $derived(tenant ? get_tenant({ tenant }) : undefined);
	let tenantStats = $derived(tenant ? get_tenant_statistics({ tenant }) : undefined);
	let chargebackData = $derived(tenant ? get_tenant_chargeback({ tenant }) : undefined);
	let usersData = $derived(tenant ? get_users({ tenant }) : undefined);

	let chargeback = $derived((chargebackData?.current?.chargebackData ?? []) as ChargebackEntry[]);
	let users = $derived((usersData?.current ?? []) as { username: string }[]);

	// Map namespace name -> storage used from chargeback
	let nsStorageMap = $derived(buildStorageMap(chargeback));

	let quotaPercent = $derived(
		calcQuotaPercent(
			Number(tenantStats?.current?.storageCapacityUsed ?? 0),
			tenantInfo?.current?.hardQuota
		)
	);

	// Total quota allocated across all namespaces
	let totalAllocatedBytes = $derived.by(() => {
		let total = 0;
		for (const ns of namespaces) {
			if (ns.hardQuota) {
				const bytes = parseQuotaBytes(ns.hardQuota);
				if (bytes) total += bytes;
			}
		}
		return total;
	});

	let allocatedPercent = $derived(
		calcQuotaPercent(totalAllocatedBytes, tenantInfo?.current?.hardQuota)
	);

	let search = $state('');
	let namespaces = $derived((nsData?.current ?? []) as Namespace[]);
	let filteredNamespaces = $derived(
		namespaces.filter((n) => n.name.toLowerCase().includes(search.toLowerCase()))
	);

	// TanStack Table state
	let sorting = $state<SortingState>([]);
	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 20 });
	let rowSelection = $state<Record<string, boolean>>({});

	let selectedKeys = $derived(
		Object.keys(rowSelection)
			.filter((k) => rowSelection[k])
			.map((k) => filteredNamespaces[Number(k)]?.name)
			.filter(Boolean) as string[]
	);
	let selectedCount = $derived(selectedKeys.length);

	const del = useDelete({ entityName: 'namespace' });

	function onConfirmDelete() {
		del.confirmDelete(() =>
			delete_namespace({ tenant: tenant!, name: del.deleteTarget }).updates(nsData!)
		);
	}

	function onConfirmBulkDelete() {
		del.confirmBulkDelete(
			selectedKeys,
			(name, isLast) => {
				const call = delete_namespace({ tenant: tenant!, name });
				return isLast ? call.updates(nsData!) : call;
			},
			() => (rowSelection = {})
		);
	}

	let createOpen = $state(false);
	let createError = $state('');
	let creating = $state(false);
	let createHashScheme = $state('SHA-256');
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

	// Tag editing for existing namespaces
	let editingTagsNs = $state('');

	function startEditTags(ns: Namespace) {
		editingTagsNs = ns.name;
	}

	async function handleSaveTags(nsName: string, tags: string[]) {
		if (!tenant || !nsData) return;
		try {
			await update_namespace({
				tenant,
				name: nsName,
				body: { tags: { tag: tags } },
			}).updates(nsData);
			toast.success('Tags updated');
			editingTagsNs = '';
		} catch {
			toast.error('Failed to update tags');
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

	// --- TanStack Table ---
	let nsColumns = $derived.by((): ColumnDef<Namespace>[] => [
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
			meta: { headerClass: 'w-10 px-4 py-3', cellClass: 'px-4 py-3' },
		},
		{
			accessorKey: 'name',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Name',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => renderSnippet(nameCellSnippet, row.original),
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			id: 'storage',
			header: 'Storage Used',
			cell: ({ row }) => renderSnippet(storageCellSnippet, row.original),
			meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'tags',
			header: 'Tags',
			cell: ({ row }) =>
				renderComponent(DataTableTagCell, {
					tags: row.original.tags?.tag ?? [],
					editing: editingTagsNs === row.original.name,
					onsave: (tags: string[]) => handleSaveTags(row.original.name, tags),
					onstartedit: () => startEditTags(row.original),
					oncanceledit: () => (editingTagsNs = ''),
				}),
		},
		{
			accessorKey: 'description',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Description',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => (row.original.description ?? '—') as string,
			meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			accessorKey: 'hardQuota',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Hard Quota',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => (row.original.hardQuota ?? '—') as string,
			meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'softQuota',
			header: 'Soft Quota',
			cell: ({ row }) =>
				(row.original.softQuota != null ? `${row.original.softQuota}%` : '—') as string,
			meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'hashScheme',
			header: 'Hash Scheme',
			cell: ({ row }) => renderSnippet(hashSchemeCellSnippet, row.original),
		},
		{
			id: 'actions',
			header: '',
			cell: ({ row }) =>
				renderComponent(DataTableActions, {
					name: row.original.name,
					ondelete: () => del.requestDelete(row.original.name),
					onnavigate: () => goto(`/namespaces/${row.original.name}`),
					onedittags: () => startEditTags(row.original),
				}),
			meta: { headerClass: 'w-16 px-4 py-3', cellClass: 'px-4 py-3' },
		},
	]);

	let nsTable = $derived(
		createSvelteTable({
			get data() {
				return filteredNamespaces;
			},
			get columns() {
				return nsColumns;
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
</script>

{#snippet nameCellSnippet(ns: Namespace)}
	<a
		href="/namespaces/{ns.name}"
		class="text-primary underline-offset-4 hover:underline"
		onclick={(e: MouseEvent) => e.stopPropagation()}
	>
		{ns.name}
	</a>
{/snippet}

{#snippet storageCellSnippet(ns: Namespace)}
	{@const used = nsStorageMap.get(ns.name) ?? 0}
	{@const quota = ns.hardQuota ? parseQuotaBytes(ns.hardQuota) : null}
	{#if used > 0 || quota}
		<div class="flex flex-col gap-1">
			<span class="text-sm">{formatBytes(used)}{quota ? ` / ${ns.hardQuota}` : ''}</span>
			{#if quota}
				{@const pct = Math.min(100, (used / quota) * 100)}
				<StorageProgressBar percent={pct} class="max-w-24" />
			{/if}
		</div>
	{:else}
		—
	{/if}
{/snippet}

{#snippet hashSchemeCellSnippet(ns: Namespace)}
	{#if ns.hashScheme}
		<Badge variant="secondary">{ns.hashScheme}</Badge>
	{:else}
		<span class="text-muted-foreground">—</span>
	{/if}
{/snippet}

<svelte:head>
	<title>Namespaces - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<PageHeader title="Namespaces" description="Manage tenant namespaces">
		{#snippet actions()}
			{#if tenant}
				<Button onclick={() => (createOpen = true)}>
					<Plus class="h-4 w-4" />
					Create Namespace
				</Button>
			{/if}
		{/snippet}
	</PageHeader>

	<Dialog.Root bind:open={createOpen}>
		<Dialog.Content class="sm:max-w-lg">
			<Dialog.Header>
				<Dialog.Title>Create Namespace</Dialog.Title>
				<Dialog.Description>Configure a new namespace for this tenant.</Dialog.Description>
			</Dialog.Header>
			<form onsubmit={handleCreate} class="space-y-4">
				<ErrorBanner message={createError} />
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
					<Select.Root type="single" bind:value={createHashScheme}>
						<Select.Trigger class="h-9 w-full">{createHashScheme}</Select.Trigger>
						<Select.Content>
							<Select.Item value="SHA-256">SHA-256</Select.Item>
							<Select.Item value="SHA-512">SHA-512</Select.Item>
							<Select.Item value="SHA-384">SHA-384</Select.Item>
							<Select.Item value="SHA-1">SHA-1</Select.Item>
							<Select.Item value="MD5">MD5</Select.Item>
						</Select.Content>
					</Select.Root>
					<input type="hidden" name="hashScheme" value={createHashScheme} />
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
					<div class="flex items-center gap-2">
						<Checkbox id="ns-search" name="searchEnabled" />
						<Label for="ns-search">Enable Search</Label>
					</div>
					<div class="flex items-center gap-2">
						<Checkbox id="ns-versioning" name="versioningEnabled" />
						<Label for="ns-versioning">Enable Versioning</Label>
					</div>
				</div>
				<Dialog.Footer>
					<Button variant="ghost" type="button" onclick={() => (createOpen = false)}>Cancel</Button>
					<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
				</Dialog.Footer>
			</form>
		</Dialog.Content>
	</Dialog.Root>

	{#if tenant}
		<!-- Tenant Stats -->
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
			{#await tenantStats}
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
			{:then stats}
				<StatCard label="Objects" value={(stats?.objectCount ?? 0).toLocaleString()} icon={FileBox}>
					<p class="mt-1 text-xs text-muted-foreground">
						{stats?.customMetadataCount ?? 0} with custom metadata
					</p>
				</StatCard>

				<StatCard
					label="Storage Used"
					value={formatBytes(Number(stats?.storageCapacityUsed ?? 0))}
					icon={HardDrive}
					delay="delay-75"
				>
					{#await tenantInfo then info}
						{#if quotaPercent !== null}
							<StorageProgressBar percent={quotaPercent} class="mt-2" />
							<p class="mt-1 text-xs text-muted-foreground">
								{formatBytes(Number(stats?.storageCapacityUsed ?? 0))} / {info?.hardQuota}
							</p>
						{:else}
							<p class="mt-1 text-xs text-muted-foreground">No quota limit</p>
						{/if}
					{/await}
				</StatCard>

				<StatCard
					label="Quota Allocated"
					value={formatBytes(totalAllocatedBytes)}
					icon={ChartPie}
					delay="delay-150"
				>
					{#await tenantInfo then info}
						{#if allocatedPercent !== null}
							<StorageProgressBar percent={allocatedPercent} class="mt-2" />
							<p class="mt-1 text-xs text-muted-foreground">
								{formatBytes(totalAllocatedBytes)} / {info?.hardQuota}
							</p>
						{:else}
							<p class="mt-1 text-xs text-muted-foreground">
								{namespaces.filter((n) => n.hardQuota).length} of {namespaces.length} with quotas
							</p>
						{/if}
					{/await}
				</StatCard>

				{#await nsData}
					<CardSkeleton />
				{:then}
					<StatCard
						label="Namespaces"
						value={String(namespaces.length)}
						icon={Boxes}
						delay="delay-200"
					/>
				{/await}

				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-300">
					{#await usersData}
						<CardSkeleton />
					{:then}
						<StatCard label="Users" value={String(users.length)} icon={Users}>
							<p class="mt-1 text-xs">
								<a href="/users" class="text-primary underline-offset-4 hover:underline">
									Manage &rarr;
								</a>
							</p>
						</StatCard>
					{/await}
				</div>
			{/await}
		</div>

		{#await nsData}
			<TableSkeleton rows={5} columns={5} />
		{:then}
			<div class="space-y-2">
				<div class="relative">
					<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
					<Input bind:value={search} placeholder="Search namespaces..." class="pl-10" />
				</div>
			</div>

			{#if selectedCount > 0}
				<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
					<span class="text-sm font-medium">{selectedCount} selected</span>
					<Button variant="destructive" size="sm" onclick={() => del.requestBulkDelete()}>
						<Trash2 class="h-3.5 w-3.5" />Delete Selected
					</Button>
					<Button variant="ghost" size="sm" onclick={() => (rowSelection = {})}>
						Deselect All
					</Button>
				</div>
			{/if}

			<DataTable
				table={nsTable}
				noResultsMessage={namespaces.length === 0
					? 'No namespaces found. Create one to get started.'
					: `No results matching "${search}"`}
			/>

			<div class="flex items-center justify-between py-2">
				<div class="text-sm text-muted-foreground">
					{#if selectedCount > 0}
						{selectedCount} of {filteredNamespaces.length} row(s) selected.
					{/if}
				</div>
				{#if nsTable.getPageCount() > 1}
					<div class="flex items-center gap-2">
						<span class="text-xs text-muted-foreground">
							Page {pagination.pageIndex + 1} of {nsTable.getPageCount()}
						</span>
						<Button
							variant="outline"
							size="icon"
							class="h-8 w-8"
							onclick={() => nsTable.previousPage()}
							disabled={!nsTable.getCanPreviousPage()}
						>
							<ChevronLeft class="h-4 w-4" />
						</Button>
						<Button
							variant="outline"
							size="icon"
							class="h-8 w-8"
							onclick={() => nsTable.nextPage()}
							disabled={!nsTable.getCanNextPage()}
						>
							<ChevronRight class="h-4 w-4" />
						</Button>
					</div>
				{/if}
			</div>
		{/await}
	{:else}
		<NoTenantPlaceholder message="Log in with a tenant to manage namespaces." />
	{/if}
</div>

<DeleteConfirmDialog
	bind:open={del.deleteDialogOpen}
	name={del.deleteTarget}
	itemType="namespace"
	loading={del.deleting}
	onconfirm={onConfirmDelete}
/>

<BulkDeleteDialog
	bind:open={del.bulkDeleteOpen}
	count={selectedCount}
	itemType="namespace"
	loading={del.deleting}
	onconfirm={onConfirmBulkDelete}
/>
