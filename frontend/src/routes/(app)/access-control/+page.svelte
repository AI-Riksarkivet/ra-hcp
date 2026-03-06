<script lang="ts">
	import { goto } from '$app/navigation';
	import { Shield, Search, Loader2, Plus } from 'lucide-svelte';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import PageHeader from '$lib/components/ui/page-header.svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_buckets,
		get_bucket_acl,
		put_bucket_acl,
		type AclGrant,
		type AclData,
	} from '$lib/buckets.remote.js';
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

	const PERMISSIONS: { value: string; label: string }[] = [
		{ value: 'FULL_CONTROL', label: 'Full Control' },
		{ value: 'READ', label: 'Read' },
		{ value: 'WRITE', label: 'Write' },
		{ value: 'READ_ACP', label: 'Read ACP' },
		{ value: 'WRITE_ACP', label: 'Write ACP' },
	];

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
	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 25 });
	let rowSelection = $state<Record<string, boolean>>({});

	let selectedCount = $derived(Object.values(rowSelection).filter(Boolean).length);

	// --- TanStack Table columns ---
	let columns = $derived.by((): ColumnDef<BucketAclRow>[] => [
		{
			id: 'select',
			header: ({ table: tbl }) =>
				renderComponent(DataTableCheckbox, {
					checked: tbl.getIsAllPageRowsSelected(),
					onCheckedChange: (val: boolean) => tbl.toggleAllPageRowsSelected(!!val),
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

	// --- Grant Access dialog state ---
	let grantOpen = $state(false);
	let granteeType = $state('CanonicalUser');
	let granteeId = $state('');
	let grantPermission = $state('READ');
	let granting = $state(false);
	let grantBucketSelection = $state<Record<string, boolean>>({});

	// Pre-populate from table selection when opening
	function openGrantDialog() {
		const selected = Object.entries(rowSelection)
			.filter(([, v]) => v)
			.map(([idx]) => table.getCoreRowModel().rows[Number(idx)]?.original.name)
			.filter(Boolean) as string[];

		grantBucketSelection = {};
		if (selected.length > 0) {
			for (const name of selected) {
				grantBucketSelection[name] = true;
			}
		}
		granteeType = 'CanonicalUser';
		granteeId = '';
		grantPermission = 'READ';
		grantOpen = true;
	}

	let grantBuckets = $derived(
		Object.entries(grantBucketSelection)
			.filter(([, v]) => v)
			.map(([name]) => name)
	);

	let allGrantBucketsSelected = $derived(
		buckets.length > 0 && buckets.every((b) => grantBucketSelection[b.name])
	);

	function toggleAllGrantBuckets(checked: boolean) {
		const next: Record<string, boolean> = {};
		if (checked) {
			for (const b of buckets) {
				next[b.name] = true;
			}
		}
		grantBucketSelection = next;
	}

	async function handleGrant() {
		if (grantBuckets.length === 0 || !granteeId) return;
		granting = true;
		try {
			for (const bucketName of grantBuckets) {
				const aclQuery = bucketAcls.get(bucketName);
				const currentAcl = (aclQuery?.current ?? { owner: null, grants: [] }) as AclData;
				const newGrant = {
					Grantee: {
						Type: granteeType,
						...(granteeType === 'CanonicalUser' ? { ID: granteeId } : { URI: granteeId }),
					},
					Permission: grantPermission,
				};
				await put_bucket_acl({
					bucket: bucketName,
					owner: currentAcl.owner
						? { ID: currentAcl.owner.ID, DisplayName: currentAcl.owner.DisplayName }
						: undefined,
					grants: [
						...currentAcl.grants.map((g) => ({
							Grantee: g.Grantee,
							Permission: g.Permission,
						})),
						newGrant,
					],
				});
			}
			toast.success(
				`Granted ${permissionLabel(grantPermission)} to ${grantBuckets.length} bucket(s)`
			);
			grantOpen = false;
			// Reset form
			granteeId = '';
			grantBucketSelection = {};
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to grant access');
		} finally {
			granting = false;
		}
	}
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
			<div class="flex items-center gap-2">
				<Shield class="h-5 w-5 text-muted-foreground" />
				<Button size="sm" onclick={openGrantDialog}>
					<Plus class="h-4 w-4" />
					Grant Access
				</Button>
			</div>
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
				<Button variant="outline" size="sm" onclick={openGrantDialog}>
					<Plus class="h-3.5 w-3.5" />
					Grant Access to Selected
				</Button>
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

<!-- Grant Access Dialog -->
<Dialog.Root bind:open={grantOpen}>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Grant Access</Dialog.Title>
			<Dialog.Description>
				Add an ACL grant to one or more buckets. The new grant will be appended to each bucket's
				existing ACL.
			</Dialog.Description>
		</Dialog.Header>

		<div class="space-y-4">
			<!-- Bucket selection -->
			<div class="space-y-2">
				<Label>Buckets</Label>
				<div class="max-h-40 space-y-1 overflow-y-auto rounded-md border p-3">
					<div class="flex items-center gap-2 border-b pb-2 mb-1">
						<Checkbox
							checked={allGrantBucketsSelected}
							onCheckedChange={(val) => toggleAllGrantBuckets(!!val)}
						/>
						<span class="text-sm font-medium">Select all ({buckets.length})</span>
					</div>
					{#each buckets as b (b.name)}
						<div class="flex items-center gap-2">
							<Checkbox
								checked={grantBucketSelection[b.name] ?? false}
								onCheckedChange={(val) => {
									grantBucketSelection = { ...grantBucketSelection, [b.name]: !!val };
								}}
							/>
							<span class="text-sm">{b.name}</span>
						</div>
					{/each}
				</div>
				{#if grantBuckets.length > 0}
					<p class="text-xs text-muted-foreground">
						{grantBuckets.length} bucket(s) selected
					</p>
				{/if}
			</div>

			<!-- Grantee Type -->
			<div class="space-y-2">
				<Label>Grantee Type</Label>
				<Select.Root type="single" bind:value={granteeType}>
					<Select.Trigger>
						{granteeType === 'CanonicalUser' ? 'User (Canonical ID)' : 'Group (URI)'}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="CanonicalUser">User (Canonical ID)</Select.Item>
						<Select.Item value="Group">Group (URI)</Select.Item>
					</Select.Content>
				</Select.Root>
			</div>

			<!-- Grantee ID -->
			<div class="space-y-2">
				<Label>
					{#if granteeType === 'CanonicalUser'}
						Canonical User ID
					{:else}
						Group URI
					{/if}
				</Label>
				<Input
					bind:value={granteeId}
					placeholder={granteeType === 'CanonicalUser'
						? 'HCP user canonical ID'
						: 'e.g. http://acs.amazonaws.com/groups/global/AllUsers'}
				/>
				{#if granteeType === 'Group'}
					<p class="text-xs text-muted-foreground">
						Common groups: <code class="rounded bg-muted px-1">AllUsers</code> (public),
						<code class="rounded bg-muted px-1">AuthenticatedUsers</code> (any logged-in user).
					</p>
				{/if}
			</div>

			<!-- Permission -->
			<div class="space-y-2">
				<Label>Permission</Label>
				<Select.Root type="single" bind:value={grantPermission}>
					<Select.Trigger>
						<Badge variant={permissionColor(grantPermission)} class="pointer-events-none">
							{permissionLabel(grantPermission)}
						</Badge>
					</Select.Trigger>
					<Select.Content>
						{#each PERMISSIONS as p (p.value)}
							<Select.Item value={p.value}>
								<Badge variant={permissionColor(p.value)}>{p.label}</Badge>
							</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>
		</div>

		<Dialog.Footer>
			<Button variant="ghost" onclick={() => (grantOpen = false)} disabled={granting}>
				Cancel
			</Button>
			<Button onclick={handleGrant} disabled={granting || grantBuckets.length === 0 || !granteeId}>
				{#if granting}
					<Loader2 class="h-4 w-4 animate-spin" />
					Granting...
				{:else}
					Grant Access
				{/if}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
