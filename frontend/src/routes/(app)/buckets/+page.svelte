<script lang="ts">
	import { enhance } from '$app/forms';
	import { Plus, Trash2 } from 'lucide-svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import { formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	let { data, form } = $props();
	let showCreate = $state(false);

	const columns = [
		{ key: 'name', label: 'Name' },
		{
			key: 'creation_date',
			label: 'Created',
			render: (b: { creation_date: string }) => formatDate(b.creation_date)
		}
	];
</script>

<svelte:head>
	<title>Buckets - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-100">Buckets</h2>
			<p class="mt-1 text-sm text-surface-500 dark:text-surface-400">
				Manage S3 buckets on your HCP system
			</p>
		</div>
		<Button onclick={() => (showCreate = !showCreate)}>
			<Plus class="h-4 w-4" />
			Create Bucket
		</Button>
	</div>

	{#if form?.error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{form.error}
		</div>
	{/if}

	{#if showCreate}
		<Card>
			<form method="POST" action="?/create" use:enhance class="flex items-end gap-4">
				<div class="flex-1">
					<Input name="bucket" label="Bucket Name" placeholder="my-bucket" required />
				</div>
				<Button type="submit">Create</Button>
				<Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
			</form>
		</Card>
	{/if}

	<DataTable
		{columns}
		data={data.buckets}
		onrowclick={(bucket) => goto(`/buckets/${bucket.name}`)}
		emptyMessage="No buckets found. Create one to get started."
	/>

	{#if data.buckets.length > 0}
		<Card class="mt-4">
			<h3 class="mb-4 text-sm font-medium text-surface-700 dark:text-surface-300">
				Delete Bucket
			</h3>
			{#each data.buckets as bucket}
				<form
					method="POST"
					action="?/delete"
					use:enhance
					class="flex items-center justify-between border-b border-surface-100 py-2 last:border-0 dark:border-surface-800"
				>
					<input type="hidden" name="bucket" value={bucket.name} />
					<span class="text-sm text-surface-700 dark:text-surface-300">{bucket.name}</span>
					<button
						type="submit"
						class="rounded-lg p-1.5 text-surface-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400"
						title="Delete bucket"
					>
						<Trash2 class="h-4 w-4" />
					</button>
				</form>
			{/each}
		</Card>
	{/if}
</div>
