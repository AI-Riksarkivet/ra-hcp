<script lang="ts">
	import Badge from '$lib/components/ui/Badge.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';

	let { data } = $props();

	const userColumns = [
		{ key: 'username', label: 'Username' },
		{ key: 'fullName', label: 'Full Name' },
		{
			key: 'enabled',
			label: 'Status',
			render: (u: { enabled?: boolean }) =>
				u.enabled === false ? 'Disabled' : 'Active'
		},
		{
			key: 'roles',
			label: 'Roles',
			render: (u: { roles?: string[] }) => u.roles?.join(', ') ?? ''
		}
	];

	const groupColumns = [
		{ key: 'name', label: 'Group Name' },
		{ key: 'description', label: 'Description' }
	];
</script>

<svelte:head>
	<title>Users - HCP Admin Console</title>
</svelte:head>

<div class="space-y-8">
	<div>
		<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-100">Users & Groups</h2>
		<p class="mt-1 text-sm text-surface-500 dark:text-surface-400">
			Manage user accounts and groups
		</p>
	</div>

	<div>
		<div class="mb-4 flex items-center gap-3">
			<h3 class="text-lg font-semibold text-surface-900 dark:text-surface-100">User Accounts</h3>
			<Badge>{data.users.length}</Badge>
		</div>
		<DataTable
			columns={userColumns}
			data={data.users}
			emptyMessage="No user accounts found"
		/>
	</div>

	<div>
		<div class="mb-4 flex items-center gap-3">
			<h3 class="text-lg font-semibold text-surface-900 dark:text-surface-100">Groups</h3>
			<Badge>{data.groups.length}</Badge>
		</div>
		<DataTable
			columns={groupColumns}
			data={data.groups}
			emptyMessage="No groups found"
		/>
	</div>
</div>
