<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { get_lance_tables } from '$lib/remote/lance.remote.js';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import { Database, Table2, RefreshCw } from 'lucide-svelte';

	let {
		tenant,
		selectedBucket = $bindable(''),
		selectedPath = $bindable(''),
		selectedTable = $bindable(''),
	}: {
		tenant: string;
		selectedBucket: string;
		selectedPath: string;
		selectedTable: string;
	} = $props();

	let bucket = $state('');
	let path = $state('');

	let tablesData = $derived(
		selectedBucket
			? get_lance_tables({ bucket: selectedBucket, path: selectedPath || undefined })
			: undefined
	);
	let tables = $derived((tablesData?.current?.tables ?? []) as string[]);
	let error = $derived(tablesData?.current?.error ?? null);

	function connect() {
		selectedBucket = bucket;
		selectedPath = path;
		selectedTable = '';
	}

	function selectTable(name: string) {
		selectedTable = name;
	}
</script>

<div class="space-y-4">
	<Card.Root>
		<Card.Header>
			<Card.Title class="flex items-center gap-2">
				<Database class="h-4 w-4" />
				S3 Location
			</Card.Title>
		</Card.Header>
		<Card.Content class="space-y-3">
			<div class="space-y-1">
				<Label for="lance-bucket">Bucket</Label>
				<Input id="lance-bucket" bind:value={bucket} placeholder="my-bucket" />
			</div>
			<div class="space-y-1">
				<Label for="lance-path">Path (optional)</Label>
				<Input id="lance-path" bind:value={path} placeholder="data/lance" />
			</div>
			<Button class="w-full" onclick={connect} disabled={!bucket}>
				<RefreshCw class="mr-2 h-4 w-4" />
				Load Tables
			</Button>
		</Card.Content>
	</Card.Root>

	{#if selectedBucket && tables.length > 0}
		<Card.Root>
			<Card.Header>
				<Card.Title class="text-sm">Tables ({tables.length})</Card.Title>
			</Card.Header>
			<Card.Content class="space-y-1">
				{#each tables as name (name)}
					<button
						class="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm transition-colors
							{selectedTable === name ? 'bg-primary text-primary-foreground' : 'hover:bg-muted'}"
						onclick={() => selectTable(name)}
					>
						<Table2 class="h-4 w-4 shrink-0" />
						{name}
					</button>
				{/each}
			</Card.Content>
		</Card.Root>
	{/if}

	{#if error}
		<ErrorBanner message={String(error)} />
	{/if}
</div>
