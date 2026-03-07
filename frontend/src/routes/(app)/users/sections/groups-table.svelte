<script lang="ts">
	import { Plus } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { get_groups } from '$lib/users.remote.js';
	import { type GroupAccount, getGroupName, getGroupRoles } from '$lib/constants.js';
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

	let {
		tenant,
		oncreate,
	}: {
		tenant: string;
		oncreate: () => void;
	} = $props();

	let groupsData = $derived(get_groups({ tenant }));
	let groups = $derived((groupsData?.current ?? []) as GroupAccount[]);

	// TanStack state
	let groupSorting = $state<SortingState>([]);
	let groupPagination = $state<PaginationState>({ pageIndex: 0, pageSize: 25 });

	let groupColumns = $derived.by((): ColumnDef<GroupAccount>[] => [
		{
			id: 'groupName',
			accessorFn: (row) => getGroupName(row),
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Group Name',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => renderSnippet(groupNameCell, row.original),
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			id: 'description',
			accessorFn: (row) => row.description || '—',
			header: 'Description',
			meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'roles',
			header: 'Roles',
			cell: ({ row }) => renderSnippet(groupRolesCell, row.original),
			meta: { cellClass: 'px-4 py-3' },
		},
	]);

	let groupsTable = $derived(
		createSvelteTable({
			get data() {
				return groups;
			},
			get columns() {
				return groupColumns;
			},
			state: {
				get sorting() {
					return groupSorting;
				},
				get pagination() {
					return groupPagination;
				},
			},
			onSortingChange: (updater) => {
				groupSorting = typeof updater === 'function' ? updater(groupSorting) : updater;
			},
			onPaginationChange: (updater) => {
				groupPagination = typeof updater === 'function' ? updater(groupPagination) : updater;
			},
			getCoreRowModel: getCoreRowModel(),
			getSortedRowModel: getSortedRowModel(),
			getPaginationRowModel: getPaginationRowModel(),
		})
	);
</script>

{#snippet groupNameCell(group: GroupAccount)}
	<a
		href="/users/groups/{getGroupName(group)}"
		class="text-primary underline-offset-4 hover:underline"
	>
		{getGroupName(group)}
	</a>
{/snippet}

{#snippet groupRolesCell(group: GroupAccount)}
	{#each getGroupRoles(group) as role (role)}
		<Badge variant="secondary" class="mr-1">{role}</Badge>
	{/each}
	{#if getGroupRoles(group).length === 0}
		<span class="text-muted-foreground">—</span>
	{/if}
{/snippet}

{#await groupsData}
	<TableSkeleton rows={3} columns={3} />
{:then}
	<div class="flex items-center justify-end">
		<Button size="sm" onclick={oncreate}>
			<Plus class="h-4 w-4" />
			Create Group
		</Button>
	</div>
	<DataTable table={groupsTable} noResultsMessage="No groups found." />
{/await}
