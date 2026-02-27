<script lang="ts">
	import { Building2 } from 'lucide-svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import { goto } from '$app/navigation';
	let { data } = $props();

	const columns = [
		{ key: 'name', label: 'Name' },
		{ key: 'systemVisibleDescription', label: 'Description' },
		{ key: 'hardQuota', label: 'Hard Quota', class: 'w-32' },
		{ key: 'softQuota', label: 'Soft Quota', class: 'w-32' }
	];
</script>

<svelte:head>
	<title>Tenants - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-100">Tenants</h2>
		<p class="mt-1 text-sm text-surface-500 dark:text-surface-400">
			Manage tenants in your HCP system
		</p>
	</div>

	<DataTable
		{columns}
		data={data.tenants}
		onrowclick={(tenant) => goto(`/tenants/${tenant.name}`)}
		emptyMessage="No tenants found"
	/>
</div>
