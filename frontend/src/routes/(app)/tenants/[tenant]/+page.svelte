<script lang="ts">
	import { ArrowLeft } from 'lucide-svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';

	let { data } = $props();

	const nsColumns = [
		{ key: 'name', label: 'Name' },
		{ key: 'description', label: 'Description' },
		{ key: 'hardQuota', label: 'Hard Quota', class: 'w-32' }
	];
</script>

<svelte:head>
	<title>{data.tenant.name} - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center gap-4">
		<a
			href="/tenants"
			class="rounded-lg p-2 text-surface-500 transition-colors hover:bg-surface-100 hover:text-surface-700 dark:text-surface-400 dark:hover:bg-surface-800"
		>
			<ArrowLeft class="h-5 w-5" />
		</a>
		<div>
			<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-100">
				{data.tenant.name}
			</h2>
			{#if data.tenant.systemVisibleDescription}
				<p class="mt-1 text-sm text-surface-500 dark:text-surface-400">
					{data.tenant.systemVisibleDescription}
				</p>
			{/if}
		</div>
	</div>

	<div class="grid gap-6 sm:grid-cols-2">
		<Card>
			<h3 class="mb-3 text-sm font-medium text-surface-500 dark:text-surface-400">Hard Quota</h3>
			<p class="text-lg font-semibold text-surface-900 dark:text-surface-100">
				{data.tenant.hardQuota ?? 'Unlimited'}
			</p>
		</Card>
		<Card>
			<h3 class="mb-3 text-sm font-medium text-surface-500 dark:text-surface-400">Soft Quota</h3>
			<p class="text-lg font-semibold text-surface-900 dark:text-surface-100">
				{data.tenant.softQuota ?? 'Unlimited'}
			</p>
		</Card>
	</div>

	<div>
		<h3 class="mb-4 text-lg font-semibold text-surface-900 dark:text-surface-100">Namespaces</h3>
		<DataTable
			columns={nsColumns}
			data={data.namespaces}
			emptyMessage="No namespaces found for this tenant"
		/>
	</div>
</div>
