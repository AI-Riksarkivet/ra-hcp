<script lang="ts">
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { Plus, Trash2, Search } from 'lucide-svelte';
	import { AlertDialog, Dialog, Tooltip } from 'bits-ui';
	import Button from '$lib/components/ui/Button.svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import { formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from '$lib/stores/toast.svelte.js';

	let { data, form } = $props();

	// Search
	let search = $state('');
	let filteredBuckets = $derived(
		data.buckets.filter((b: { name: string }) =>
			b.name.toLowerCase().includes(search.toLowerCase())
		)
	);

	// Multi-select
	let selected = $state<Set<string>>(new Set());
	let allSelected = $derived(
		filteredBuckets.length > 0 && filteredBuckets.every((b: { name: string }) => selected.has(b.name))
	);

	function toggleAll() {
		if (allSelected) {
			selected = new Set();
		} else {
			selected = new Set(filteredBuckets.map((b: { name: string }) => b.name));
		}
	}

	function toggleOne(name: string) {
		const next = new Set(selected);
		if (next.has(name)) {
			next.delete(name);
		} else {
			next.add(name);
		}
		selected = next;
	}

	// Delete confirmation
	let deleteTarget = $state<string | null>(null);
	let bulkDeleteOpen = $state(false);
	let deleting = $state(false);

	async function confirmDelete() {
		if (!deleteTarget) return;
		deleting = true;
		try {
			const res = await fetch(`/api/v1/buckets/${encodeURIComponent(deleteTarget)}`, {
				method: 'DELETE'
			});
			if (res.ok) {
				toast.success(`Deleted bucket "${deleteTarget}"`);
				await invalidateAll();
			} else {
				toast.error('Failed to delete bucket');
			}
		} finally {
			deleting = false;
			deleteTarget = null;
		}
	}

	async function confirmBulkDelete() {
		deleting = true;
		const names = [...selected];
		let successCount = 0;
		let failCount = 0;
		for (const name of names) {
			try {
				const res = await fetch(`/api/v1/buckets/${encodeURIComponent(name)}`, {
					method: 'DELETE'
				});
				if (res.ok) {
					successCount++;
				} else {
					failCount++;
				}
			} catch {
				failCount++;
			}
		}
		if (successCount > 0) toast.success(`Deleted ${successCount} bucket${successCount !== 1 ? 's' : ''}`);
		if (failCount > 0) toast.error(`Failed to delete ${failCount} bucket${failCount !== 1 ? 's' : ''}`);
		selected = new Set();
		deleting = false;
		bulkDeleteOpen = false;
		await invalidateAll();
	}

	// Create bucket modal
	let createOpen = $state(false);
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
		<Button onclick={() => (createOpen = true)}>
			<Plus class="h-4 w-4" />
			Create Bucket
		</Button>
	</div>

	{#if form?.error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{form.error}
		</div>
	{/if}

	<!-- Create Bucket Modal -->
	<Dialog.Root bind:open={createOpen}>
		<Dialog.Portal>
			<Dialog.Overlay class="fixed inset-0 z-50 bg-black/50" />
			<Dialog.Content class="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-surface-200 bg-white p-6 shadow-xl dark:border-surface-800 dark:bg-surface-900">
				<Dialog.Title class="mb-4 text-lg font-semibold text-surface-900 dark:text-surface-100">
					Create Bucket
				</Dialog.Title>
				<form method="POST" action="?/create" use:enhance={() => {
					return async ({ result, update }) => {
						if (result.type === 'success') {
							toast.success('Bucket created successfully');
							createOpen = false;
							await invalidateAll();
						} else {
							await update();
						}
					};
				}} class="space-y-4">
					<Input name="bucket" label="Bucket Name" placeholder="my-bucket" required />
					<div class="flex justify-end gap-2">
						<Button variant="ghost" onclick={() => (createOpen = false)}>Cancel</Button>
						<Button type="submit">Create</Button>
					</div>
				</form>
			</Dialog.Content>
		</Dialog.Portal>
	</Dialog.Root>

	<!-- Search -->
	<div class="relative">
		<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-surface-400" />
		<input
			type="text"
			bind:value={search}
			placeholder="Search buckets..."
			class="w-full rounded-lg border border-surface-300 bg-white py-2 pl-10 pr-3 text-sm shadow-sm transition-colors placeholder:text-surface-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 dark:border-surface-700 dark:bg-surface-900 dark:text-surface-100 dark:placeholder:text-surface-600"
		/>
	</div>

	<!-- Bulk action bar -->
	{#if selected.size > 0}
		<div class="flex items-center gap-3 rounded-lg border border-surface-200 bg-surface-50 px-4 py-2 dark:border-surface-800 dark:bg-surface-900">
			<span class="text-sm font-medium text-surface-700 dark:text-surface-300">
				{selected.size} selected
			</span>
			<Button variant="danger" size="sm" onclick={() => (bulkDeleteOpen = true)}>
				<Trash2 class="h-3.5 w-3.5" />
				Delete Selected
			</Button>
			<Button variant="ghost" size="sm" onclick={() => (selected = new Set())}>
				Deselect All
			</Button>
		</div>
	{/if}

	<div class="overflow-x-auto rounded-lg border border-surface-200 dark:border-surface-800">
		<table class="w-full text-left text-sm">
			<thead class="border-b border-surface-200 bg-surface-50 text-xs uppercase tracking-wide text-surface-500 dark:border-surface-800 dark:bg-surface-900 dark:text-surface-400">
				<tr>
					<th class="w-10 px-4 py-3">
						<input
							type="checkbox"
							checked={allSelected}
							onchange={toggleAll}
							class="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500 dark:border-surface-600"
							disabled={filteredBuckets.length === 0}
						/>
					</th>
					<th class="px-4 py-3 font-medium">Name</th>
					<th class="px-4 py-3 font-medium">Created</th>
					<th class="w-16 px-4 py-3 font-medium"></th>
				</tr>
			</thead>
			<tbody class="divide-y divide-surface-100 dark:divide-surface-800">
				{#if data.buckets.length === 0}
					<tr>
						<td colspan="4" class="px-4 py-8 text-center text-surface-500">
							No buckets found. Create one to get started.
						</td>
					</tr>
				{:else if filteredBuckets.length === 0}
					<tr>
						<td colspan="4" class="px-4 py-8 text-center text-surface-500">
							No results matching "{search}"
						</td>
					</tr>
				{:else}
					{#each filteredBuckets as bucket}
						<tr
							class="cursor-pointer bg-white transition-colors hover:bg-surface-50 dark:bg-surface-900 dark:hover:bg-surface-800"
							onclick={() => goto(`/buckets/${bucket.name}`)}
							onkeydown={(e) => e.key === 'Enter' && goto(`/buckets/${bucket.name}`)}
							role="button"
							tabindex="0"
						>
							<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
							<td class="px-4 py-3" onclick={(e: MouseEvent) => e.stopPropagation()}>
								<input
									type="checkbox"
									checked={selected.has(bucket.name)}
									onchange={() => toggleOne(bucket.name)}
									class="h-4 w-4 rounded border-surface-300 text-primary-600 focus:ring-primary-500 dark:border-surface-600"
								/>
							</td>
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
										<button
											type="button"
											onclick={() => (deleteTarget = bucket.name)}
											class="rounded-lg p-1.5 text-surface-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400"
										>
											<Trash2 class="h-4 w-4" />
										</button>
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

<!-- Single delete confirmation -->
<AlertDialog.Root
	open={deleteTarget !== null}
	onOpenChange={(open) => { if (!open) deleteTarget = null; }}
>
	<AlertDialog.Portal>
		<AlertDialog.Overlay class="fixed inset-0 z-50 bg-black/50" />
		<AlertDialog.Content class="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-surface-200 bg-white p-6 shadow-xl dark:border-surface-800 dark:bg-surface-900">
			<AlertDialog.Title class="text-lg font-semibold text-surface-900 dark:text-surface-100">
				Delete Bucket
			</AlertDialog.Title>
			<AlertDialog.Description class="mt-2 text-sm text-surface-500 dark:text-surface-400">
				Are you sure you want to delete bucket "<strong class="text-surface-700 dark:text-surface-300">{deleteTarget}</strong>"? This action cannot be undone.
			</AlertDialog.Description>
			<div class="mt-4 flex justify-end gap-2">
				<AlertDialog.Cancel>
					<Button variant="ghost" disabled={deleting}>Cancel</Button>
				</AlertDialog.Cancel>
				<AlertDialog.Action>
					<Button variant="danger" onclick={confirmDelete} disabled={deleting}>
						{deleting ? 'Deleting...' : 'Delete'}
					</Button>
				</AlertDialog.Action>
			</div>
		</AlertDialog.Content>
	</AlertDialog.Portal>
</AlertDialog.Root>

<!-- Bulk delete confirmation -->
<AlertDialog.Root bind:open={bulkDeleteOpen}>
	<AlertDialog.Portal>
		<AlertDialog.Overlay class="fixed inset-0 z-50 bg-black/50" />
		<AlertDialog.Content class="fixed left-1/2 top-1/2 z-50 w-full max-w-md -translate-x-1/2 -translate-y-1/2 rounded-xl border border-surface-200 bg-white p-6 shadow-xl dark:border-surface-800 dark:bg-surface-900">
			<AlertDialog.Title class="text-lg font-semibold text-surface-900 dark:text-surface-100">
				Delete {selected.size} Bucket{selected.size !== 1 ? 's' : ''}
			</AlertDialog.Title>
			<AlertDialog.Description class="mt-2 text-sm text-surface-500 dark:text-surface-400">
				Are you sure you want to delete {selected.size} bucket{selected.size !== 1 ? 's' : ''}? This action cannot be undone.
			</AlertDialog.Description>
			<div class="mt-4 flex justify-end gap-2">
				<AlertDialog.Cancel>
					<Button variant="ghost" disabled={deleting}>Cancel</Button>
				</AlertDialog.Cancel>
				<AlertDialog.Action>
					<Button variant="danger" onclick={confirmBulkDelete} disabled={deleting}>
						{deleting ? 'Deleting...' : `Delete ${selected.size} Bucket${selected.size !== 1 ? 's' : ''}`}
					</Button>
				</AlertDialog.Action>
			</div>
		</AlertDialog.Content>
	</AlertDialog.Portal>
</AlertDialog.Root>
