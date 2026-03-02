<script lang="ts">
	import { ArrowLeft } from 'lucide-svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import type { ColumnDef } from '@tanstack/table-core';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';

	let { data } = $props();

	type Namespace = { name: string; description?: string; hardQuota?: string };

	const nsColumns: ColumnDef<Namespace, any>[] = [
		{ accessorKey: 'name', header: 'Name' },
		{ accessorKey: 'description', header: 'Description' },
		{ accessorKey: 'hardQuota', header: 'Hard Quota', size: 128 }
	];
</script>

<svelte:head>
	{#await data.tenant then tenant}
		<title>{tenant.name} - HCP Admin Console</title>
	{/await}
</svelte:head>

<div class="space-y-6">
	{#await data.tenant}
		<div class="flex items-center gap-4">
			<a
				href="/tenants"
				class="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
			>
				<ArrowLeft class="h-5 w-5" />
			</a>
			<div class="space-y-2">
				<Skeleton class="h-7 w-48" />
				<Skeleton class="h-4 w-32" />
			</div>
		</div>
	{:then tenant}
		<div class="flex items-center gap-4">
			<a
				href="/tenants"
				class="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-accent-foreground"
			>
				<ArrowLeft class="h-5 w-5" />
			</a>
			<div>
				<h2 class="text-2xl font-bold">
					{tenant.name}
				</h2>
				{#if tenant.systemVisibleDescription}
					<p class="mt-1 text-sm text-muted-foreground">
						{tenant.systemVisibleDescription}
					</p>
				{/if}
			</div>
		</div>

		<div class="grid gap-6 sm:grid-cols-2">
			<Card.Root>
				<Card.Content class="pt-6">
					<h3 class="mb-3 text-sm font-medium text-muted-foreground">Hard Quota</h3>
					<p class="text-lg font-semibold">
						{tenant.hardQuota ?? 'Unlimited'}
					</p>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Content class="pt-6">
					<h3 class="mb-3 text-sm font-medium text-muted-foreground">Soft Quota</h3>
					<p class="text-lg font-semibold">
						{tenant.softQuota ?? 'Unlimited'}
					</p>
				</Card.Content>
			</Card.Root>
		</div>
	{/await}

	{#await data.tenant}
		<div class="grid gap-6 sm:grid-cols-2">
			<CardSkeleton />
			<CardSkeleton />
		</div>
	{:then _}{/await}

	<div>
		<h3 class="mb-4 text-lg font-semibold">Namespaces</h3>
		{#await data.namespaces}
			<TableSkeleton rows={3} columns={3} />
		{:then namespaces}
			<DataTable
				columns={nsColumns}
				data={namespaces}
				emptyMessage="No namespaces found for this tenant"
			/>
		{/await}
	</div>
</div>
