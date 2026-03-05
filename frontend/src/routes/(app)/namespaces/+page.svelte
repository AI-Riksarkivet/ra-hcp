<script lang="ts">
	import { page } from '$app/state';
	import {
		Plus,
		Trash2,
		X,
		Pencil,
		FileBox,
		HardDrive,
		Boxes,
		Users,
		PieChart,
	} from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { toast } from 'svelte-sonner';
	import { SvelteSet } from 'svelte/reactivity';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import StatCard from '$lib/components/ui/stat-card.svelte';
	import SearchToolbar from '$lib/components/ui/search-toolbar.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import BulkDeleteDialog from '$lib/components/ui/bulk-delete-dialog.svelte';
	import {
		get_namespaces,
		create_namespace,
		update_namespace,
		delete_namespace,
		type Namespace,
	} from '$lib/namespaces.remote.js';
	import {
		get_tenant,
		get_tenant_statistics,
		get_tenant_chargeback,
		type ChargebackEntry,
	} from '$lib/tenant-info.remote.js';
	import { get_users } from '$lib/users.remote.js';
	import { formatBytes, parseQuotaBytes } from '$lib/utils/format.js';
	import ServiceTagBadge from '$lib/components/ui/service-tag-badge.svelte';

	let tenant = $derived(page.data.tenant as string | undefined);

	let nsData = $derived(tenant ? get_namespaces({ tenant }) : undefined);

	// Tenant stats
	let tenantInfo = $derived(tenant ? get_tenant({ tenant }) : undefined);
	let tenantStats = $derived(tenant ? get_tenant_statistics({ tenant }) : undefined);
	let chargebackData = $derived(tenant ? get_tenant_chargeback({ tenant }) : undefined);
	let usersData = $derived(tenant ? get_users({ tenant }) : undefined);

	let chargeback = $derived((chargebackData?.current?.chargebackData ?? []) as ChargebackEntry[]);
	let users = $derived((usersData?.current ?? []) as { username: string }[]);

	// Map namespace name → storage used from chargeback
	let nsStorageMap = $derived.by(() => {
		const map = new Map<string, number>();
		for (const entry of chargeback) {
			if (entry.namespaceName) map.set(entry.namespaceName, entry.storageCapacityUsed ?? 0);
		}
		return map;
	});

	// Parse tenant quota to bytes
	let tenantQuotaBytes = $derived.by(() => {
		const info = tenantInfo?.current;
		if (!info?.hardQuota) return null;
		return parseQuotaBytes(info.hardQuota);
	});

	let quotaPercent = $derived.by(() => {
		const stats = tenantStats?.current;
		if (!tenantQuotaBytes || !stats?.storageCapacityUsed) return null;
		return Math.min(100, (Number(stats.storageCapacityUsed) / tenantQuotaBytes) * 100);
	});

	// Total quota allocated across all namespaces
	let totalAllocatedBytes = $derived.by(() => {
		let total = 0;
		for (const ns of namespaces) {
			if (ns.hardQuota) {
				const bytes = parseQuotaBytes(ns.hardQuota);
				if (bytes) total += bytes;
			}
		}
		return total;
	});

	let allocatedPercent = $derived.by(() => {
		if (!tenantQuotaBytes || totalAllocatedBytes === 0) return null;
		return Math.min(100, (totalAllocatedBytes / tenantQuotaBytes) * 100);
	});

	let search = $state('');
	let namespaces = $derived((nsData?.current ?? []) as Namespace[]);
	let filteredNamespaces = $derived(
		namespaces.filter((n) => n.name.toLowerCase().includes(search.toLowerCase()))
	);

	let selected = new SvelteSet<string>();
	let allSelected = $derived(
		filteredNamespaces.length > 0 && filteredNamespaces.every((n) => selected.has(n.name))
	);

	function toggleAll() {
		if (allSelected) {
			selected.clear();
		} else {
			for (const n of filteredNamespaces) selected.add(n.name);
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
		if (!deleteTarget || !tenant || !nsData) return;
		deleting = true;
		try {
			await delete_namespace({ tenant, name: deleteTarget }).updates(nsData);
			toast.success(`Deleted namespace "${deleteTarget}"`);
		} catch {
			toast.error('Failed to delete namespace');
		} finally {
			deleting = false;
			deleteDialogOpen = false;
			deleteTarget = '';
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
		selected.clear();
		deleting = false;
		bulkDeleteOpen = false;
	}

	let createOpen = $state(false);
	let createError = $state('');
	let creating = $state(false);
	let createTags = $state<string[]>([]);
	let tagInput = $state('');

	function addTag() {
		const t = tagInput.trim();
		if (t && !createTags.includes(t.toLowerCase())) {
			createTags = [...createTags, t.toLowerCase()];
		}
		tagInput = '';
	}

	function removeTag(t: string) {
		createTags = createTags.filter((x) => x !== t);
	}

	function handleTagKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addTag();
		}
	}

	// Tag editing for existing namespaces
	let editingTagsNs = $state('');
	let editTags = $state<string[]>([]);
	let editTagInput = $state('');
	let savingTags = $state(false);

	function startEditTags(ns: Namespace) {
		editingTagsNs = ns.name;
		editTags = [...(ns.tags?.tag ?? [])];
		editTagInput = '';
	}

	function addEditTag() {
		const t = editTagInput.trim();
		if (t && !editTags.includes(t.toLowerCase())) {
			editTags = [...editTags, t.toLowerCase()];
		}
		editTagInput = '';
	}

	function removeEditTag(t: string) {
		editTags = editTags.filter((x) => x !== t);
	}

	function handleEditTagKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addEditTag();
		}
	}

	async function saveTags() {
		if (!tenant || !nsData || !editingTagsNs) return;
		savingTags = true;
		try {
			await update_namespace({
				tenant,
				name: editingTagsNs,
				body: { tags: { tag: editTags } },
			}).updates(nsData);
			toast.success('Tags updated');
			editingTagsNs = '';
		} catch {
			toast.error('Failed to update tags');
		} finally {
			savingTags = false;
		}
	}

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
			const description = (formData.get('description') as string) || undefined;
			const hardQuota = (formData.get('hardQuota') as string) || undefined;
			const softQuotaStr = formData.get('softQuota') as string;
			const softQuota = softQuotaStr ? Number(softQuotaStr) : undefined;
			const hashScheme = (formData.get('hashScheme') as string) || undefined;
			const searchEnabled = formData.has('searchEnabled');
			const versioningEnabled = formData.has('versioningEnabled');
			await create_namespace({
				tenant,
				name,
				description,
				hardQuota,
				softQuota,
				hashScheme,
				searchEnabled,
				versioningEnabled,
				tags: createTags.length > 0 ? createTags : undefined,
			}).updates(nsData);
			toast.success('Namespace created successfully');
			createOpen = false;
			createTags = [];
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
		<Dialog.Content class="sm:max-w-lg">
			<Dialog.Header>
				<Dialog.Title>Create Namespace</Dialog.Title>
				<Dialog.Description>Configure a new namespace for this tenant.</Dialog.Description>
			</Dialog.Header>
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
				<div class="space-y-2">
					<Label for="ns-desc">Description</Label>
					<Input id="ns-desc" name="description" placeholder="Optional description" />
				</div>
				<div class="grid grid-cols-2 gap-4">
					<div class="space-y-2">
						<Label for="ns-hard-quota">Hard Quota</Label>
						<Input id="ns-hard-quota" name="hardQuota" placeholder="e.g. 50 GB" />
					</div>
					<div class="space-y-2">
						<Label for="ns-soft-quota">Soft Quota (%)</Label>
						<Input
							id="ns-soft-quota"
							name="softQuota"
							type="number"
							min="10"
							max="95"
							placeholder="85"
						/>
					</div>
				</div>
				<div class="space-y-2">
					<Label for="ns-hash">Hash Scheme</Label>
					<select
						id="ns-hash"
						name="hashScheme"
						class="flex h-9 w-full rounded-md border border-input bg-transparent px-3 py-1 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
					>
						<option value="SHA-256">SHA-256</option>
						<option value="SHA-512">SHA-512</option>
						<option value="SHA-384">SHA-384</option>
						<option value="SHA-1">SHA-1</option>
						<option value="MD5">MD5</option>
					</select>
				</div>
				<div class="space-y-2">
					<Label for="ns-tags">Tags</Label>
					<div class="flex gap-2">
						<Input
							id="ns-tags"
							placeholder="e.g. lakefs, nfs, s3"
							bind:value={tagInput}
							onkeydown={handleTagKeydown}
						/>
						<Button type="button" variant="secondary" size="sm" onclick={addTag}>Add</Button>
					</div>
					{#if createTags.length > 0}
						<div class="flex flex-wrap gap-1 pt-1">
							{#each createTags as t (t)}
								<ServiceTagBadge tag={t} />
								<button
									type="button"
									class="-ml-1 mr-1 rounded-full p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
									onclick={() => removeTag(t)}
								>
									<X class="h-3 w-3" />
								</button>
							{/each}
						</div>
					{/if}
				</div>
				<div class="flex gap-6">
					<label class="flex items-center gap-2 text-sm">
						<input type="checkbox" name="searchEnabled" class="h-4 w-4 rounded border-input" />
						Enable Search
					</label>
					<label class="flex items-center gap-2 text-sm">
						<input type="checkbox" name="versioningEnabled" class="h-4 w-4 rounded border-input" />
						Enable Versioning
					</label>
				</div>
				<Dialog.Footer>
					<Button variant="ghost" type="button" onclick={() => (createOpen = false)}>Cancel</Button>
					<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
				</Dialog.Footer>
			</form>
		</Dialog.Content>
	</Dialog.Root>

	{#if tenant}
		<!-- Tenant Stats -->
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
			{#await tenantStats}
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
			{:then stats}
				<StatCard label="Objects" value={(stats?.objectCount ?? 0).toLocaleString()} icon={FileBox}>
					<p class="mt-1 text-xs text-muted-foreground">
						{stats?.customMetadataCount ?? 0} with custom metadata
					</p>
				</StatCard>

				<StatCard
					label="Storage Used"
					value={formatBytes(Number(stats?.storageCapacityUsed ?? 0))}
					icon={HardDrive}
					delay="delay-75"
				>
					{#await tenantInfo then info}
						{#if quotaPercent !== null}
							<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
								<div
									class="h-full rounded-full transition-all duration-500 {quotaPercent > 90
										? 'bg-destructive'
										: quotaPercent > 70
											? 'bg-yellow-500'
											: 'bg-primary'}"
									style="width: {quotaPercent}%"
								></div>
							</div>
							<p class="mt-1 text-xs text-muted-foreground">
								{formatBytes(Number(stats?.storageCapacityUsed ?? 0))} / {info?.hardQuota}
							</p>
						{:else}
							<p class="mt-1 text-xs text-muted-foreground">No quota limit</p>
						{/if}
					{/await}
				</StatCard>

				<StatCard
					label="Quota Allocated"
					value={formatBytes(totalAllocatedBytes)}
					icon={PieChart}
					delay="delay-150"
				>
					{#await tenantInfo then info}
						{#if allocatedPercent !== null}
							<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
								<div
									class="h-full rounded-full transition-all duration-500 {allocatedPercent > 90
										? 'bg-destructive'
										: allocatedPercent > 70
											? 'bg-yellow-500'
											: 'bg-blue-500'}"
									style="width: {allocatedPercent}%"
								></div>
							</div>
							<p class="mt-1 text-xs text-muted-foreground">
								{formatBytes(totalAllocatedBytes)} / {info?.hardQuota}
							</p>
						{:else}
							<p class="mt-1 text-xs text-muted-foreground">
								{namespaces.filter((n) => n.hardQuota).length} of {namespaces.length} with quotas
							</p>
						{/if}
					{/await}
				</StatCard>

				{#await nsData}
					<CardSkeleton />
				{:then _}
					<StatCard
						label="Namespaces"
						value={String(namespaces.length)}
						icon={Boxes}
						delay="delay-200"
					/>
				{/await}

				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-300">
					{#await usersData}
						<CardSkeleton />
					{:then _}
						<StatCard label="Users" value={String(users.length)} icon={Users}>
							<p class="mt-1 text-xs">
								<a href="/users" class="text-primary underline-offset-4 hover:underline">
									Manage &rarr;
								</a>
							</p>
						</StatCard>
					{/await}
				</div>
			{/await}
		</div>

		{#await nsData}
			<TableSkeleton rows={5} columns={5} />
		{:then _}
			<SearchToolbar
				bind:search
				placeholder="Search namespaces..."
				selectedCount={selected.size}
				ondeleteselected={() => (bulkDeleteOpen = true)}
				ondeselectall={() => selected.clear()}
			/>

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
							<th class="px-4 py-3 font-medium">Storage Used</th>
							<th class="px-4 py-3 font-medium">Tags</th>
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
								><td colspan="9" class="px-4 py-8 text-center text-muted-foreground"
									>No namespaces found. Create one to get started.</td
								></tr
							>
						{:else if filteredNamespaces.length === 0}
							<tr
								><td colspan="9" class="px-4 py-8 text-center text-muted-foreground"
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
									<td class="px-4 py-3 font-medium">
										<a
											href="/namespaces/{ns.name}"
											class="text-primary underline-offset-4 hover:underline"
											onclick={(e) => e.stopPropagation()}
										>
											{ns.name}
										</a>
									</td>
									<td class="px-4 py-3 text-muted-foreground">
										{#if true}
											{@const used = nsStorageMap.get(ns.name) ?? 0}
											{@const quota = ns.hardQuota ? parseQuotaBytes(ns.hardQuota) : null}
											{#if used > 0 || quota}
												<div class="flex flex-col gap-1">
													<span class="text-sm"
														>{formatBytes(used)}{quota ? ` / ${ns.hardQuota}` : ''}</span
													>
													{#if quota}
														{@const pct = Math.min(100, (used / quota) * 100)}
														<div
															class="h-1.5 w-full max-w-24 overflow-hidden rounded-full bg-muted"
														>
															<div
																class="h-full rounded-full transition-all {pct > 90
																	? 'bg-destructive'
																	: pct > 70
																		? 'bg-yellow-500'
																		: 'bg-primary'}"
																style="width: {pct}%"
															></div>
														</div>
													{/if}
												</div>
											{:else}
												—
											{/if}
										{/if}
									</td>
									<td class="px-4 py-3">
										{#if editingTagsNs === ns.name}
											<div class="flex flex-col gap-1.5">
												<div class="flex gap-1.5">
													<input
														class="h-7 w-28 rounded border border-input bg-transparent px-2 text-xs focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
														placeholder="Add tag..."
														bind:value={editTagInput}
														onkeydown={handleEditTagKeydown}
													/>
													<Button
														variant="ghost"
														size="icon"
														class="h-7 w-7"
														onclick={saveTags}
														disabled={savingTags}
													>
														{#if savingTags}...{:else}Save{/if}
													</Button>
													<Button
														variant="ghost"
														size="icon"
														class="h-7 w-7"
														onclick={() => (editingTagsNs = '')}
													>
														<X class="h-3 w-3" />
													</Button>
												</div>
												{#if editTags.length > 0}
													<div class="flex flex-wrap gap-1">
														{#each editTags as t (t)}
															<span class="inline-flex items-center gap-0.5">
																<ServiceTagBadge tag={t} />
																<button
																	type="button"
																	class="rounded-full p-0.5 text-muted-foreground hover:text-destructive"
																	onclick={() => removeEditTag(t)}
																>
																	<X class="h-2.5 w-2.5" />
																</button>
															</span>
														{/each}
													</div>
												{/if}
											</div>
										{:else}
											<div class="group flex items-center gap-1">
												{#if ns.tags?.tag?.length}
													<div class="flex flex-wrap gap-1">
														{#each ns.tags.tag as t (t)}
															<ServiceTagBadge tag={t} />
														{/each}
													</div>
												{:else}
													<span class="text-muted-foreground">—</span>
												{/if}
												<button
													type="button"
													class="rounded p-0.5 text-muted-foreground opacity-0 transition-opacity hover:text-foreground group-hover:opacity-100"
													onclick={() => startEditTags(ns)}
												>
													<Pencil class="h-3 w-3" />
												</button>
											</div>
										{/if}
									</td>
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
														onclick={() => {
															deleteTarget = ns.name;
															deleteDialogOpen = true;
														}}
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

<DeleteConfirmDialog
	bind:open={deleteDialogOpen}
	name={deleteTarget}
	itemType="namespace"
	loading={deleting}
	onconfirm={confirmDelete}
/>

<BulkDeleteDialog
	bind:open={bulkDeleteOpen}
	count={selected.size}
	itemType="namespace"
	loading={deleting}
	onconfirm={confirmBulkDelete}
/>
