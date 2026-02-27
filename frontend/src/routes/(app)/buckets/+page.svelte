<script lang="ts">
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { Plus, Trash2 } from 'lucide-svelte';
	import { Tooltip } from 'bits-ui';
	import Card from '$lib/components/ui/Card.svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from '$lib/stores/toast.svelte.js';

	let { data, form } = $props();
	let showCreate = $state(false);
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
			<form method="POST" action="?/create" use:enhance={() => {
				return async ({ result, update }) => {
					if (result.type === 'success') {
						toast.success('Bucket created successfully');
						showCreate = false;
						await invalidateAll();
					} else {
						await update();
					}
				};
			}} class="flex items-end gap-4">
				<div class="flex-1">
					<Input name="bucket" label="Bucket Name" placeholder="my-bucket" required />
				</div>
				<Button type="submit">Create</Button>
				<Button variant="ghost" onclick={() => (showCreate = false)}>Cancel</Button>
			</form>
		</Card>
	{/if}

	<div class="overflow-x-auto rounded-lg border border-surface-200 dark:border-surface-800">
		<table class="w-full text-left text-sm">
			<thead class="border-b border-surface-200 bg-surface-50 text-xs uppercase tracking-wide text-surface-500 dark:border-surface-800 dark:bg-surface-900 dark:text-surface-400">
				<tr>
					<th class="px-4 py-3 font-medium">Name</th>
					<th class="px-4 py-3 font-medium">Created</th>
					<th class="w-16 px-4 py-3 font-medium"></th>
				</tr>
			</thead>
			<tbody class="divide-y divide-surface-100 dark:divide-surface-800">
				{#if data.buckets.length === 0}
					<tr>
						<td colspan="3" class="px-4 py-8 text-center text-surface-500">
							No buckets found. Create one to get started.
						</td>
					</tr>
				{:else}
					{#each data.buckets as bucket}
						<tr
							class="cursor-pointer bg-white transition-colors hover:bg-surface-50 dark:bg-surface-900 dark:hover:bg-surface-800"
							onclick={() => goto(`/buckets/${bucket.name}`)}
							onkeydown={(e) => e.key === 'Enter' && goto(`/buckets/${bucket.name}`)}
							role="button"
							tabindex="0"
						>
							<td class="px-4 py-3 font-medium text-surface-900 dark:text-surface-100">
								{bucket.name}
							</td>
							<td class="px-4 py-3 text-surface-500 dark:text-surface-400">
								{formatDate(bucket.creation_date)}
							</td>
							<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
							<td class="px-4 py-3" onclick={(e: MouseEvent) => e.stopPropagation()}>
								<Tooltip.Root>
									<Tooltip.Trigger class="cursor-default">
										<form method="POST" action="?/delete" use:enhance={() => {
											return async ({ result, update }) => {
												if (result.type === 'success') {
													toast.success(`Deleted bucket "${bucket.name}"`);
													await invalidateAll();
												} else {
													toast.error('Failed to delete bucket');
													await update();
												}
											};
										}}>
											<input type="hidden" name="bucket" value={bucket.name} />
											<button
												type="submit"
												class="rounded-lg p-1.5 text-surface-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400"
											>
												<Trash2 class="h-4 w-4" />
											</button>
										</form>
									</Tooltip.Trigger>
									<Tooltip.Portal>
										<Tooltip.Content
											sideOffset={8}
											class="z-50 rounded-lg border border-surface-200 bg-white px-3 py-1.5 text-sm shadow-lg dark:border-surface-700 dark:bg-surface-800"
										>
											Delete bucket
										</Tooltip.Content>
									</Tooltip.Portal>
								</Tooltip.Root>
							</td>
						</tr>
					{/each}
				{/if}
			</tbody>
		</table>
	</div>
</div>
