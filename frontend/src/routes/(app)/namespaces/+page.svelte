<script lang="ts">
	import { page } from '$app/state';
	import { Plus } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import PageHeader from '$lib/components/ui/page-header.svelte';
	import NoTenantPlaceholder from '$lib/components/ui/no-tenant-placeholder.svelte';
	import NamespaceStats from './sections/namespace-stats.svelte';
	import NamespaceTable from './sections/namespace-table.svelte';
	import NamespaceCreateDialog from './sections/namespace-create-dialog.svelte';

	let tenant = $derived(page.data.tenant as string | undefined);

	let createOpen = $state(false);
</script>

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

	{#if tenant}
		<NamespaceStats {tenant} />
		<NamespaceTable {tenant} />
		<NamespaceCreateDialog {tenant} bind:open={createOpen} />
	{:else}
		<NoTenantPlaceholder message="Log in with a tenant to manage namespaces." />
	{/if}
</div>
