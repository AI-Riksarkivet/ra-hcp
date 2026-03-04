<script lang="ts">
	import { page } from '$app/state';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import type { ColumnDef, CellContext } from '@tanstack/table-core';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { get_users, get_groups } from '$lib/users.remote.js';

	type User = { username: string; fullName?: string; enabled?: boolean; roles?: string[] };
	type Group = { name: string; description?: string };

	let tenant = $derived(page.data.tenant as string | undefined);
	let usersData = $derived(tenant ? get_users({ tenant }) : undefined);
	let groupsData = $derived(tenant ? get_groups({ tenant }) : undefined);

	const userColumns: ColumnDef<User, any>[] = [
		{ accessorKey: 'username', header: 'Username' },
		{ accessorKey: 'fullName', header: 'Full Name' },
		{
			accessorKey: 'enabled',
			header: 'Status',
			cell: (info: CellContext<User, unknown>) =>
				info.getValue() === false ? 'Disabled' : 'Active',
		},
		{
			accessorKey: 'roles',
			header: 'Roles',
			cell: (info: CellContext<User, unknown>) => {
				const roles = info.getValue() as string[] | undefined;
				return roles?.join(', ') ?? '';
			},
		},
	];

	const groupColumns: ColumnDef<Group, any>[] = [
		{ accessorKey: 'name', header: 'Group Name' },
		{ accessorKey: 'description', header: 'Description' },
	];
</script>

<svelte:head>
	<title>Users - HCP Admin Console</title>
</svelte:head>

<div class="space-y-8">
	<div>
		<h2 class="text-2xl font-bold">Users & Groups</h2>
		<p class="mt-1 text-sm text-muted-foreground">Manage user accounts and groups</p>
	</div>

	{#if tenant}
		<div>
			{#await usersData}
				<div class="mb-4 flex items-center gap-3">
					<h3 class="text-lg font-semibold">User Accounts</h3>
				</div>
				<TableSkeleton rows={5} columns={4} />
			{:then users}
				<div class="mb-4 flex items-center gap-3">
					<h3 class="text-lg font-semibold">User Accounts</h3>
					<Badge variant="secondary">{users.length}</Badge>
				</div>
				<DataTable columns={userColumns} data={users} emptyMessage="No user accounts found" />
			{/await}
		</div>

		<div>
			{#await groupsData}
				<div class="mb-4 flex items-center gap-3">
					<h3 class="text-lg font-semibold">Groups</h3>
				</div>
				<TableSkeleton rows={3} columns={2} />
			{:then groups}
				<div class="mb-4 flex items-center gap-3">
					<h3 class="text-lg font-semibold">Groups</h3>
					<Badge variant="secondary">{groups.length}</Badge>
				</div>
				<DataTable columns={groupColumns} data={groups} emptyMessage="No groups found" />
			{/await}
		</div>
	{:else}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to manage users and groups.</p>
		</div>
	{/if}
</div>
