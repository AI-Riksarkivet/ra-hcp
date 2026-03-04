<script lang="ts">
	import { page } from '$app/state';
	import { Plus, Trash2, Search } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { toast } from 'svelte-sonner';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import {
		get_namespaces,
		create_namespace,
		delete_namespace,
		type Namespace,
	} from '$lib/namespaces.remote.js';

	let tenant = $derived(page.data.tenant as string | undefined);

	let nsData = $derived(tenant ? get_namespaces({ tenant }) : undefined);

	let search = $state('');
	let namespaces = $derived((nsData?.current ?? []) as Namespace[]);
	let filteredNamespaces = $derived(
		namespaces.filter((n) => n.name.toLowerCase().includes(search.toLowerCase()))
	);

	let selected = $state<Set<string>>(new Set());
	let allSelected = $derived(
		filteredNamespaces.length > 0 && filteredNamespaces.every((n) => selected.has(n.name))
	);

	function toggleAll() {
		if (allSelected) {
			selected = new Set();
		} else {
			selected = new Set(filteredNamespaces.map((n) => n.name));
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
		if (!deleteTarget || !tenant || !nsData) return;
		deleting = true;
		try {
			await delete_namespace({ tenant, name: deleteTarget }).updates(nsData);
			toast.success(`Deleted namespace "${deleteTarget}"`);
		} catch {
			toast.error('Failed to delete namespace');
		} finally {
			deleting = false;
			deleteTarget = null;
		}
	}

	async function confirmBulkDelete() {
		if (!tenant || !nsData) return;
		deleting = true;
		const names = [...selected];
		let successCount = 0,
			failCount = 0;
		for (let i = 0; i < names.length; i++) {
			try {
				const call = delete_namespace({ tenant, name: names[i] });
				if (i === names.length - 1) {
					await call.updates(nsData);
				} else {
					await call;
				}
				successCount++;
			} catch {
				failCount++;
			}
		}
		if (successCount > 0)
			toast.success(`Deleted ${successCount} namespace${successCount !== 1 ? 's' : ''}`);
		if (failCount > 0)
			toast.error(`Failed to delete ${failCount} namespace${failCount !== 1 ? 's' : ''}`);
		selected = new Set();
		deleting = false;
		bulkDeleteOpen = false;
	}

	let createOpen = $state(false);
	let createError = $state('');
	let creating = $state(false);

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		if (!tenant || !nsData) return;
		const form = e.currentTarget as HTMLFormElement;
		const formData = new FormData(form);
		const name = formData.get('namespace') as string;
		if (!name) return;
		creating = true;
		createError = '';
		try {
			await create_namespace({ tenant, name }).updates(nsData);
			toast.success('Namespace created successfully');
			createOpen = false;
			form.reset();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create namespace';
		} finally {
			creating = false;
		}
	}
</script>

<svelte:head>
	<title>Namespaces - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div>
			<h2 class="text-2xl font-bold">Namespaces</h2>
			<p class="mt-1 text-sm text-muted-foreground">Manage tenant namespaces</p>
		</div>
		{#if tenant}
			<Button onclick={() => (createOpen = true)}>
				<Plus class="h-4 w-4" />
				Create Namespace
			</Button>
		{/if}
	</div>

	<Dialog.Root bind:open={createOpen}>
		<Dialog.Content class="sm:max-w-md">
			<Dialog.Header><Dialog.Title>Create Namespace</Dialog.Title></Dialog.Header>
			<form onsubmit={handleCreate} class="space-y-4">
				{#if createError}
					<div
						class="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
					>
						{createError}
					</div>
				{/if}
				<div class="space-y-2">
					<Label for="ns-name">Namespace Name</Label>
					<Input id="ns-name" name="namespace" placeholder="my-namespace" required />
				</div>
				<Dialog.Footer>
					<Button variant="ghost" type="button" onclick={() => (createOpen = false)}>Cancel</Button>
					<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
				</Dialog.Footer>
			</form>
		</Dialog.Content>
	</Dialog.Root>

	{#if tenant}
		{#await nsData}
			<TableSkeleton rows={5} columns={5} />
		{:then _}
			<div class="relative">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<Input type="text" bind:value={search} placeholder="Search namespaces..." class="pl-10" />
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
									disabled={filteredNamespaces.length === 0}
								/></th
							>
							<th class="px-4 py-3 font-medium">Name</th>
							<th class="px-4 py-3 font-medium">Description</th>
							<th class="px-4 py-3 font-medium">Hard Quota</th>
							<th class="px-4 py-3 font-medium">Soft Quota</th>
							<th class="px-4 py-3 font-medium">Hash Scheme</th>
							<th class="w-16 px-4 py-3 font-medium"></th>
						</tr>
					</thead>
					<tbody class="divide-y">
						{#if namespaces.length === 0}
							<tr
								><td colspan="7" class="px-4 py-8 text-center text-muted-foreground"
									>No namespaces found. Create one to get started.</td
								></tr
							>
						{:else if filteredNamespaces.length === 0}
							<tr
								><td colspan="7" class="px-4 py-8 text-center text-muted-foreground"
									>No results matching "{search}"</td
								></tr
							>
						{:else}
							{#each filteredNamespaces as ns (ns.name)}
								<tr class="bg-card transition-colors hover:bg-accent/50">
									<td
										class="px-4 py-3"
										onclick={(e) => e.stopPropagation()}
										onkeydown={() => {}}
										role="cell"
									>
										<input
											type="checkbox"
											checked={selected.has(ns.name)}
											onchange={() => toggleOne(ns.name)}
											class="h-4 w-4 rounded border-input"
										/>
									</td>
									<td class="px-4 py-3 font-medium">{ns.name}</td>
									<td class="px-4 py-3 text-muted-foreground">{ns.description ?? '—'}</td>
									<td class="px-4 py-3 text-muted-foreground">{ns.hardQuota ?? '—'}</td>
									<td class="px-4 py-3 text-muted-foreground"
										>{ns.softQuota != null ? `${ns.softQuota}%` : '—'}</td
									>
									<td class="px-4 py-3">
										{#if ns.hashScheme}
											<Badge variant="secondary">{ns.hashScheme}</Badge>
										{:else}
											<span class="text-muted-foreground">—</span>
										{/if}
									</td>
									<td
										class="px-4 py-3"
										onclick={(e) => e.stopPropagation()}
										onkeydown={() => {}}
										role="cell"
									>
										<Tooltip.Root>
											<Tooltip.Trigger>
												{#snippet child({ props })}
													<button
														type="button"
														onclick={() => (deleteTarget = ns.name)}
														class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
														{...props}
													>
														<Trash2 class="h-4 w-4" />
													</button>
												{/snippet}
											</Tooltip.Trigger>
											<Tooltip.Content>Delete namespace</Tooltip.Content>
										</Tooltip.Root>
									</td>
								</tr>
							{/each}
						{/if}
					</tbody>
				</table>
			</div>
		{/await}
	{:else}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to manage namespaces.</p>
		</div>
	{/if}
</div>

<AlertDialog.Root
	open={deleteTarget !== null}
	onOpenChange={(open) => {
		if (!open) deleteTarget = null;
	}}
>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete Namespace</AlertDialog.Title>
			<AlertDialog.Description
				>Are you sure you want to delete namespace "<strong>{deleteTarget}</strong>"? This action
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
				>Delete {selected.size} Namespace{selected.size !== 1 ? 's' : ''}</AlertDialog.Title
			>
			<AlertDialog.Description
				>Are you sure you want to delete {selected.size} namespace{selected.size !== 1 ? 's' : ''}?
				This action cannot be undone.</AlertDialog.Description
			>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel disabled={deleting}>Cancel</AlertDialog.Cancel>
			<Button variant="destructive" onclick={confirmBulkDelete} disabled={deleting}
				>{deleting
					? 'Deleting...'
					: `Delete ${selected.size} Namespace${selected.size !== 1 ? 's' : ''}`}</Button
			>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
