<script lang="ts">
	import { Search, Trash2 } from 'lucide-svelte';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_buckets,
		get_bucket_acl,
		put_bucket_acl,
		type AclGrant,
		type AclData,
	} from '$lib/buckets.remote.js';
	import { get_users } from '$lib/users.remote.js';
	import type { User } from '$lib/constants.js';
	import {
		DataTable,
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

	interface Props {
		tenant?: string;
	}

	let { tenant }: Props = $props();

	type FlatGrantRow = {
		bucket: string;
		owner: string;
		granteeDisplay: string;
		granteeType: string;
		granteeId: string;
		permission: string;
	};

	// Data fetching
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

	// Fetch users for username resolution when tenant available
	let usersData = $derived(tenant ? get_users({ tenant }) : null);
	let guidToUsername = $derived.by(() => {
		const map = new SvelteMap<string, string>();
		const users = (usersData?.current ?? []) as User[];
		for (const u of users) {
			if (u.userGUID) {
				map.set(u.userGUID, u.username);
			}
		}
		return map;
	});

	function resolveGrantee(grant: AclGrant): {
		display: string;
		type: string;
		id: string;
	} {
		const g = grant.Grantee ?? {};
		const type = (g.Type as string) ?? 'CanonicalUser';
		if (type === 'Group') {
			const uri = (g.URI as string) ?? '';
			const label = uri.split('/').pop() || uri || 'Unknown';
			return { display: label, type: 'Group', id: uri };
		}
		const id = (g.ID as string) || '';
		const displayName = (g.DisplayName as string) || '';
		// Try to resolve the canonical ID to a username
		const username = guidToUsername.get(id);
		if (username) {
			return { display: username, type: 'CanonicalUser', id };
		}
		return { display: displayName || id || 'Unknown', type: 'CanonicalUser', id };
	}

	// Derive flat grant rows
	let rows = $derived.by((): FlatGrantRow[] => {
		const result: FlatGrantRow[] = [];
		for (const b of buckets) {
			const aclQuery = bucketAcls.get(b.name);
			const acl = (aclQuery?.current ?? { owner: null, grants: [] }) as AclData;
			const owner = acl.owner?.DisplayName || acl.owner?.ID || '';
			for (const grant of acl.grants ?? []) {
				const { display, type, id } = resolveGrantee(grant);
				result.push({
					bucket: b.name,
					owner,
					granteeDisplay: display,
					granteeType: type,
					granteeId: id,
					permission: grant.Permission ?? '',
				});
			}
		}
		return result;
	});

	// Filters
	let searchBucket = $state('');
	let searchGrantee = $state('');
	let filterPermission = $state('');

	let filteredRows = $derived(
		rows.filter((r) => {
			if (searchBucket && !r.bucket.toLowerCase().includes(searchBucket.toLowerCase()))
				return false;
			if (searchGrantee && !r.granteeDisplay.toLowerCase().includes(searchGrantee.toLowerCase()))
				return false;
			if (filterPermission && r.permission !== filterPermission) return false;
			return true;
		})
	);

	let allPermissions = $derived([...new Set(rows.map((r) => r.permission).filter(Boolean))].sort());

	// Permission helpers
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

	function granteeTypeLabel(t: string): string {
		return t === 'Group' ? 'Group' : 'User';
	}

	// Revoke handler
	let revoking = $state<string | null>(null);

	function revokeKey(row: FlatGrantRow): string {
		return `${row.bucket}:${row.granteeId}:${row.permission}`;
	}

	async function handleRevoke(row: FlatGrantRow) {
		const key = revokeKey(row);
		revoking = key;
		try {
			const aclQuery = bucketAcls.get(row.bucket);
			const currentAcl = (aclQuery?.current ?? { owner: null, grants: [] }) as AclData;

			// Filter out the matching grant
			let removed = false;
			const remainingGrants = currentAcl.grants.filter((g) => {
				if (removed) return true;
				const { id } = resolveGrantee(g);
				if (id === row.granteeId && g.Permission === row.permission) {
					removed = true;
					return false;
				}
				return true;
			});

			const result = put_bucket_acl({
				bucket: row.bucket,
				owner: currentAcl.owner
					? { ID: currentAcl.owner.ID, DisplayName: currentAcl.owner.DisplayName }
					: undefined,
				grants: remainingGrants.map((g) => ({
					Grantee: g.Grantee,
					Permission: g.Permission,
				})),
			});
			if (aclQuery) await result.updates(aclQuery);
			else await result;

			toast.success(`Revoked ${permissionLabel(row.permission)} on ${row.bucket}`);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to revoke grant');
		} finally {
			revoking = null;
		}
	}

	// TanStack Table state
	let sorting = $state<SortingState>([]);
	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 25 });

	let columns = $derived.by((): ColumnDef<FlatGrantRow>[] => [
		{
			accessorKey: 'bucket',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Bucket',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => renderSnippet(bucketNameCell, row.original),
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			accessorKey: 'granteeDisplay',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Grantee',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => renderSnippet(granteeCell, row.original),
			meta: { cellClass: 'px-4 py-3' },
		},
		{
			accessorKey: 'granteeType',
			header: 'Type',
			cell: ({ row }) => renderSnippet(typeCell, row.original),
			meta: { cellClass: 'px-4 py-3' },
		},
		{
			accessorKey: 'permission',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Permission',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => renderSnippet(permissionCell, row.original),
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
			},
			onSortingChange: (updater) => {
				sorting = typeof updater === 'function' ? updater(sorting) : updater;
			},
			onPaginationChange: (updater) => {
				pagination = typeof updater === 'function' ? updater(pagination) : updater;
			},
			getCoreRowModel: getCoreRowModel(),
			getSortedRowModel: getSortedRowModel(),
			getPaginationRowModel: getPaginationRowModel(),
		})
	);

	let noResultsMessage = $derived(
		rows.length === 0 ? 'No grants found.' : 'No results matching current filters'
	);
</script>

{#snippet bucketNameCell(row: FlatGrantRow)}
	<a
		href="/buckets/{row.bucket}"
		class="text-primary underline-offset-4 hover:underline"
		onclick={(e) => e.stopPropagation()}
	>
		{row.bucket}
	</a>
{/snippet}

{#snippet granteeCell(row: FlatGrantRow)}
	<div class="flex flex-col gap-0.5">
		<span>{row.granteeDisplay}</span>
		{#if row.granteeId && row.granteeDisplay !== row.granteeId}
			<span class="truncate font-mono text-[11px] text-muted-foreground" title={row.granteeId}>
				{row.granteeId}
			</span>
		{/if}
	</div>
{/snippet}

{#snippet typeCell(row: FlatGrantRow)}
	<Badge variant="outline">{granteeTypeLabel(row.granteeType)}</Badge>
{/snippet}

{#snippet permissionCell(row: FlatGrantRow)}
	<Badge variant={permissionColor(row.permission)}>{permissionLabel(row.permission)}</Badge>
{/snippet}

{#snippet actionsCell(row: FlatGrantRow)}
	<Button
		variant="ghost"
		size="sm"
		class="text-destructive hover:text-destructive"
		onclick={(e) => {
			e.stopPropagation();
			handleRevoke(row);
		}}
		disabled={revoking === revokeKey(row)}
	>
		<Trash2 class="h-3.5 w-3.5" />
		{revoking === revokeKey(row) ? 'Revoking...' : 'Revoke'}
	</Button>
{/snippet}

{#await bucketData}
	<TableSkeleton rows={5} columns={5} />
{:then}
	<div class="space-y-2">
		<div class="flex items-center gap-3">
			<div class="relative flex-1">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<Input bind:value={searchBucket} placeholder="Filter by bucket..." class="pl-10" />
			</div>
			<div class="relative flex-1">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<Input bind:value={searchGrantee} placeholder="Filter by grantee..." class="pl-10" />
			</div>
			<select
				class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-9 w-48 items-center rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1"
				bind:value={filterPermission}
			>
				<option value="">All permissions</option>
				{#each allPermissions as p (p)}
					<option value={p}>{permissionLabel(p)}</option>
				{/each}
			</select>
		</div>
		<div class="flex items-center">
			<span class="ml-auto text-xs text-muted-foreground">
				{filteredRows.length} of {rows.length} grants
			</span>
		</div>
	</div>

	<DataTable {table} {noResultsMessage}>
		{#snippet footer()}
			{filteredRows.length} grant(s) across {new Set(rows.map((r) => r.bucket)).size} buckets
		{/snippet}
	</DataTable>
{/await}
