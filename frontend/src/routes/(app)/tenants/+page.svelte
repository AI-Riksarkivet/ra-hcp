<script lang="ts">
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import { goto } from '$app/navigation';
	import type { ColumnDef } from '@tanstack/table-core';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';

	let { data } = $props();

	type Tenant = { name: string; systemVisibleDescription?: string; hardQuota?: string; softQuota?: string };

	const columns: ColumnDef<Tenant, any>[] = [
		{ accessorKey: 'name', header: 'Name' },
		{ accessorKey: 'systemVisibleDescription', header: 'Description' },
		{ accessorKey: 'hardQuota', header: 'Hard Quota', size: 128 },
		{ accessorKey: 'softQuota', header: 'Soft Quota', size: 128 }
	];
</script>

<svelte:head>
	<title>Tenants - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h2 class="text-2xl font-bold">Tenants</h2>
		<p class="mt-1 text-sm text-muted-foreground">
			Manage tenants in your HCP system
		</p>
	</div>

	{#await data.tenants}
		<TableSkeleton rows={5} columns={4} />
	{:then tenants}
		<DataTable
			{columns}
			data={tenants}
			onrowclick={(tenant) => goto(`/tenants/${tenant.name}`)}
			emptyMessage="No tenants found"
		/>
	{/await}
</div>
