<script lang="ts">
	import { Plus, Trash2, Search } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { SvelteSet } from 'svelte/reactivity';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import BulkDeleteDialog from '$lib/components/ui/bulk-delete-dialog.svelte';
	import { get_buckets, create_bucket, delete_bucket } from '$lib/buckets.remote.js';

	let bucketData = get_buckets();
	let owner = $derived(
		bucketData.current?.owner as {
			display_name?: string;
			id?: string;
			DisplayName?: string;
			ID?: string;
		} | null
	);
	let ownerName = $derived(owner?.display_name ?? owner?.DisplayName ?? '');

	let search = $state('');
	let dateFilter = $state('');
	let buckets = $derived(
		(bucketData.current?.buckets ?? []) as { name: string; creation_date: string }[]
	);

	let filteredBuckets = $derived(
		buckets.filter((b) => {
			if (search && !b.name.toLowerCase().includes(search.toLowerCase())) return false;
			if (dateFilter) {
				const d = new Date(b.creation_date);
				const now = new Date();
				if (dateFilter === '24h' && now.getTime() - d.getTime() > 86400000) return false;
				if (dateFilter === '7d' && now.getTime() - d.getTime() > 604800000) return false;
				if (dateFilter === '30d' && now.getTime() - d.getTime() > 2592000000) return false;
			}
			return true;
		})
	);

	let selected = new SvelteSet<string>();
	let allSelected = $derived(
		filteredBuckets.length > 0 && filteredBuckets.every((b) => selected.has(b.name))
	);

	function toggleAll() {
		if (allSelected) {
			selected.clear();
		} else {
			for (const b of filteredBuckets) selected.add(b.name);
		}
	}

	function toggleOne(name: string) {
		if (selected.has(name)) {
			selected.delete(name);
		} else {
			selected.add(name);
		}
	}

	let deleteTarget = $state('');
	let deleteDialogOpen = $state(false);
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
			deleteDialogOpen = false;
			deleteTarget = '';
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
		selected.clear();
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
		<TableSkeleton rows={5} columns={5} />
	{:then _}
		<div class="space-y-2">
			<div class="relative">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<input
					type="text"
					bind:value={search}
					placeholder="Search buckets..."
					class="w-full rounded-lg border bg-background py-2 pl-10 pr-3 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20"
				/>
			</div>
			<div class="flex flex-wrap items-center gap-2">
				{#if ownerName}
					<Badge variant="outline">Owner: {ownerName}</Badge>
				{/if}
				<select bind:value={dateFilter} class="h-8 rounded-md border bg-background px-2 text-xs">
					<option value="">All dates</option>
					<option value="24h">Last 24 hours</option>
					<option value="7d">Last 7 days</option>
					<option value="30d">Last 30 days</option>
				</select>
				{#if dateFilter}
					<Button
						variant="ghost"
						size="sm"
						class="h-7 px-2 text-xs"
						onclick={() => (dateFilter = '')}
					>
						Clear filters
					</Button>
				{/if}
				<span class="ml-auto text-xs text-muted-foreground"
					>{filteredBuckets.length} of {buckets.length} buckets</span
				>
			</div>
		</div>

		{#if selected.size > 0}
			<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
				<span class="text-sm font-medium">{selected.size} selected</span>
				<Button variant="destructive" size="sm" onclick={() => (bulkDeleteOpen = true)}>
					<Trash2 class="h-3.5 w-3.5" />Delete Selected
				</Button>
				<Button variant="ghost" size="sm" onclick={() => selected.clear()}>Deselect All</Button>
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
						<th class="px-4 py-3 font-medium">Owner</th>
						<th class="px-4 py-3 font-medium">Created</th>
						<th class="w-16 px-4 py-3 font-medium"></th>
					</tr>
				</thead>
				<tbody class="divide-y">
					{#if buckets.length === 0}
						<tr
							><td colspan="5" class="px-4 py-8 text-center text-muted-foreground"
								>No buckets found. Create one to get started.</td
							></tr
						>
					{:else if filteredBuckets.length === 0}
						<tr
							><td colspan="5" class="px-4 py-8 text-center text-muted-foreground"
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
								<td class="px-4 py-3 text-muted-foreground">{ownerName || '-'}</td>
								<td class="px-4 py-3 text-muted-foreground">{formatDate(bucket.creation_date)}</td>
								<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
								<td class="px-4 py-3" onclick={(e: MouseEvent) => e.stopPropagation()}>
									<Tooltip.Root>
										<Tooltip.Trigger>
											{#snippet child({ props })}
												<button
													type="button"
													{...props}
													onclick={() => {
														deleteTarget = bucket.name;
														deleteDialogOpen = true;
													}}
													class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
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

<DeleteConfirmDialog
	bind:open={deleteDialogOpen}
	name={deleteTarget}
	itemType="bucket"
	loading={deleting}
	onconfirm={confirmDelete}
/>

<BulkDeleteDialog
	bind:open={bulkDeleteOpen}
	count={selected.size}
	itemType="bucket"
	loading={deleting}
	onconfirm={confirmBulkDelete}
/>
