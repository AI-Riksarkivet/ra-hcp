<script lang="ts">
	import { Plus, Trash2, Search } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { get_buckets, create_bucket, delete_bucket } from '$lib/buckets.remote.js';

	let bucketData = get_buckets();

	let search = $state('');
	let buckets = $derived(
		(bucketData.current?.buckets ?? []) as { name: string; creation_date: string }[]
	);

	let filteredBuckets = $derived(
		buckets.filter((b) => b.name.toLowerCase().includes(search.toLowerCase()))
	);

	let selected = $state<Set<string>>(new Set());
	let allSelected = $derived(
		filteredBuckets.length > 0 && filteredBuckets.every((b) => selected.has(b.name))
	);

	function toggleAll() {
		if (allSelected) {
			selected = new Set();
		} else {
			selected = new Set(filteredBuckets.map((b) => b.name));
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

	let deleteTarget = $state<string | null>(null);
	let bulkDeleteOpen = $state(false);
	let deleting = $state(false);

	async function confirmDelete() {
		if (!deleteTarget) return;
		deleting = true;
		try {
			await delete_bucket({ bucket: deleteTarget }).updates(bucketData);
			toast.success(`Deleted bucket "${deleteTarget}"`);
		} catch {
			toast.error('Failed to delete bucket');
		} finally {
			deleting = false;
			deleteTarget = null;
		}
	}

	async function confirmBulkDelete() {
		deleting = true;
		const names = [...selected];
		let successCount = 0,
			failCount = 0;
		for (let i = 0; i < names.length; i++) {
			try {
				const call = delete_bucket({ bucket: names[i] });
				if (i === names.length - 1) {
					await call.updates(bucketData);
				} else {
					await call;
				}
				successCount++;
			} catch {
				failCount++;
			}
		}
		if (successCount > 0)
			toast.success(`Deleted ${successCount} bucket${successCount !== 1 ? 's' : ''}`);
		if (failCount > 0)
			toast.error(`Failed to delete ${failCount} bucket${failCount !== 1 ? 's' : ''}`);
		selected = new Set();
		deleting = false;
		bulkDeleteOpen = false;
	}

	let createOpen = $state(false);
	let createError = $state('');
	let creating = $state(false);

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		const form = e.currentTarget as HTMLFormElement;
		const formData = new FormData(form);
		const name = formData.get('bucket') as string;
		if (!name) return;
		creating = true;
		createError = '';
		try {
			await create_bucket({ bucket: name }).updates(bucketData);
			toast.success('Bucket created successfully');
			createOpen = false;
			form.reset();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create bucket';
		} finally {
			creating = false;
		}
	}
</script>

<svelte:head>
	<title>Buckets - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-2xl font-bold">Buckets</h2>
			<p class="mt-1 text-sm text-muted-foreground">Manage S3 buckets on your HCP system</p>
		</div>
		<Button onclick={() => (createOpen = true)}>
			<Plus class="h-4 w-4" />
			Create Bucket
		</Button>
	</div>

	<Dialog.Root bind:open={createOpen}>
		<Dialog.Content class="sm:max-w-md">
			<Dialog.Header><Dialog.Title>Create Bucket</Dialog.Title></Dialog.Header>
			<form onsubmit={handleCreate} class="space-y-4">
				{#if createError}
					<div
						class="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
					>
						{createError}
					</div>
				{/if}
				<div class="space-y-2">
					<Label for="bucket-name">Bucket Name</Label>
					<Input id="bucket-name" name="bucket" placeholder="my-bucket" required />
				</div>
				<Dialog.Footer>
					<Button variant="ghost" type="button" onclick={() => (createOpen = false)}>Cancel</Button>
					<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
				</Dialog.Footer>
			</form>
		</Dialog.Content>
	</Dialog.Root>

	{#await bucketData}
		<TableSkeleton rows={5} columns={4} />
	{:then _}
		<div class="relative">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<Input type="text" bind:value={search} placeholder="Search buckets..." class="pl-10" />
		</div>

		{#if selected.size > 0}
			<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
				<span class="text-sm font-medium">{selected.size} selected</span>
				<Button variant="destructive" size="sm" onclick={() => (bulkDeleteOpen = true)}>
					<Trash2 class="h-3.5 w-3.5" />Delete Selected
				</Button>
				<Button variant="ghost" size="sm" onclick={() => (selected = new Set())}
					>Deselect All</Button
				>
			</div>
		{/if}

		<div class="overflow-x-auto rounded-lg border">
			<table class="w-full text-left text-sm">
				<thead class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
					<tr>
						<th class="w-10 px-4 py-3"
							><input
								type="checkbox"
								checked={allSelected}
								onchange={toggleAll}
								class="h-4 w-4 rounded border-input"
								disabled={filteredBuckets.length === 0}
							/></th
						>
						<th class="px-4 py-3 font-medium">Name</th>
						<th class="px-4 py-3 font-medium">Created</th>
						<th class="w-16 px-4 py-3 font-medium"></th>
					</tr>
				</thead>
				<tbody class="divide-y">
					{#if buckets.length === 0}
						<tr
							><td colspan="4" class="px-4 py-8 text-center text-muted-foreground"
								>No buckets found. Create one to get started.</td
							></tr
						>
					{:else if filteredBuckets.length === 0}
						<tr
							><td colspan="4" class="px-4 py-8 text-center text-muted-foreground"
								>No results matching "{search}"</td
							></tr
						>
					{:else}
						{#each filteredBuckets as bucket (bucket.name)}
							<tr
								class="cursor-pointer bg-card transition-colors hover:bg-accent/50"
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
										class="h-4 w-4 rounded border-input"
									/>
								</td>
								<td class="px-4 py-3 font-medium">{bucket.name}</td>
								<td class="px-4 py-3 text-muted-foreground">{formatDate(bucket.creation_date)}</td>
								<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
								<td class="px-4 py-3" onclick={(e: MouseEvent) => e.stopPropagation()}>
									<Tooltip.Root>
										<Tooltip.Trigger>
											{#snippet child({ props })}
												<button
													type="button"
													onclick={() => (deleteTarget = bucket.name)}
													class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
													{...props}
												>
													<Trash2 class="h-4 w-4" />
												</button>
											{/snippet}
										</Tooltip.Trigger>
										<Tooltip.Content>Delete bucket</Tooltip.Content>
									</Tooltip.Root>
								</td>
							</tr>
						{/each}
					{/if}
				</tbody>
			</table>
		</div>
	{/await}
</div>

<AlertDialog.Root
	open={deleteTarget !== null}
	onOpenChange={(open) => {
		if (!open) deleteTarget = null;
	}}
>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete Bucket</AlertDialog.Title>
			<AlertDialog.Description
				>Are you sure you want to delete bucket "<strong>{deleteTarget}</strong>"? This action
				cannot be undone.</AlertDialog.Description
			>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel disabled={deleting}>Cancel</AlertDialog.Cancel>
			<Button variant="destructive" onclick={confirmDelete} disabled={deleting}
				>{deleting ? 'Deleting...' : 'Delete'}</Button
			>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>

<AlertDialog.Root bind:open={bulkDeleteOpen}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title
				>Delete {selected.size} Bucket{selected.size !== 1 ? 's' : ''}</AlertDialog.Title
			>
			<AlertDialog.Description
				>Are you sure you want to delete {selected.size} bucket{selected.size !== 1 ? 's' : ''}?
				This action cannot be undone.</AlertDialog.Description
			>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel disabled={deleting}>Cancel</AlertDialog.Cancel>
			<Button variant="destructive" onclick={confirmBulkDelete} disabled={deleting}
				>{deleting
					? 'Deleting...'
					: `Delete ${selected.size} Bucket${selected.size !== 1 ? 's' : ''}`}</Button
			>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
