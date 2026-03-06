<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import { Plus, Trash2, HelpCircle } from 'lucide-svelte';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { toast } from 'svelte-sonner';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import BackButton from '$lib/components/ui/back-button.svelte';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import NoTenantPlaceholder from '$lib/components/ui/no-tenant-placeholder.svelte';
	import {
		get_content_class,
		update_content_class,
		delete_content_class,
		type ContentClass,
		type ContentProperty,
	} from '$lib/content-classes.remote.js';

	const PROPERTY_TYPES = ['STRING', 'INTEGER', 'DOUBLE', 'BOOLEAN', 'DATETIME'] as const;

	let tenant = $derived(page.data.tenant as string | undefined);
	let className = $derived(page.params.name ?? '');

	let classData = $derived(
		tenant && className ? get_content_class({ tenant, name: className }) : undefined
	);
	let contentClass = $derived((classData?.current ?? null) as ContentClass | null);

	// Local editable state
	let syncVersion = $state(0);
	let localProperties = $state<ContentProperty[]>([]);
	let localNamespaces = $state<string[]>([]);
	let nsInput = $state('');

	$effect(() => {
		const cc = contentClass;
		void syncVersion;
		localProperties = (cc?.contentProperties ?? []).map((p) => ({ ...p }));
		localNamespaces = [...(cc?.namespaces ?? [])];
	});

	function propsEqual(): boolean {
		const remote = contentClass?.contentProperties ?? [];
		if (localProperties.length !== remote.length) return false;
		return localProperties.every(
			(p, i) =>
				p.name === remote[i].name &&
				p.expression === remote[i].expression &&
				p.type === remote[i].type &&
				(p.multivalued ?? false) === (remote[i].multivalued ?? false) &&
				(p.format ?? '') === (remote[i].format ?? '')
		);
	}

	let dirty = $derived(
		!propsEqual() ||
			JSON.stringify([...localNamespaces].sort()) !==
				JSON.stringify([...(contentClass?.namespaces ?? [])].sort())
	);

	let saving = $state(false);

	async function save() {
		if (!tenant || !classData) return;
		saving = true;
		try {
			await update_content_class({
				tenant,
				name: className,
				body: {
					contentProperties: localProperties,
					namespaces: localNamespaces,
				},
			}).updates(classData);
			syncVersion++;
			toast.success('Content class updated');
		} catch {
			toast.error('Failed to update content class');
		} finally {
			saving = false;
		}
	}

	// Property management
	function addProperty() {
		localProperties = [
			...localProperties,
			{ name: '', expression: '', type: 'STRING', multivalued: false },
		];
	}

	function removeProperty(index: number) {
		localProperties = localProperties.filter((_, i) => i !== index);
	}

	// Namespace management
	function addNamespace() {
		const ns = nsInput.trim();
		if (ns && !localNamespaces.includes(ns)) {
			localNamespaces = [...localNamespaces, ns];
		}
		nsInput = '';
	}

	function removeNamespace(ns: string) {
		localNamespaces = localNamespaces.filter((n) => n !== ns);
	}

	function handleNsKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addNamespace();
		}
	}

	// Delete
	let deleteOpen = $state(false);
	let deleting = $state(false);

	async function handleDelete() {
		if (!tenant) return;
		deleting = true;
		try {
			await delete_content_class({ tenant, name: className });
			toast.success(`Content class "${className}" deleted`);
			goto('/content-classes');
		} catch {
			toast.error('Failed to delete content class');
			deleting = false;
		}
	}
</script>

<svelte:head>
	<title>{className} - Content Class - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-4">
			<BackButton href="/content-classes" label="Back to content classes" />
			<div>
				<h2 class="text-2xl font-bold">{className}</h2>
				<p class="mt-1 text-sm text-muted-foreground">Metadata schema for object indexing</p>
			</div>
		</div>
		{#if contentClass}
			<Button variant="destructive" size="sm" onclick={() => (deleteOpen = true)}>
				<Trash2 class="h-4 w-4" />
				Delete
			</Button>
		{/if}
	</div>

	{#if !tenant}
		<NoTenantPlaceholder message="Log in with a tenant to view content class details." />
	{:else}
		{#await classData}
			<div class="rounded-lg border p-5">
				<div class="space-y-3">
					{#each Array(3) as _, i (i)}
						<div class="h-8 w-full animate-pulse rounded bg-muted"></div>
					{/each}
				</div>
			</div>
		{:then}
			{#if !contentClass}
				<div class="rounded-lg border border-dashed p-8 text-center">
					<p class="text-muted-foreground">Content class not found or could not be loaded.</p>
				</div>
			{:else}
				<!-- Content Properties -->
				<div class="rounded-lg border p-5">
					<div class="flex items-center justify-between">
						<h3 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
							Content Properties
						</h3>
						<Button variant="outline" size="sm" onclick={addProperty}>
							<Plus class="h-3.5 w-3.5" /> Add Property
						</Button>
					</div>

					{#if localProperties.length > 0}
						<div class="mt-3 space-y-2">
							{#each localProperties as prop, i (i)}
								<div class="flex items-end gap-2 rounded-md border p-3">
									<div class="min-w-0 flex-1">
										<div class="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">
											<div class="space-y-1">
												<Label class="text-xs">Name</Label>
												<Input
													class="h-8 text-sm"
													placeholder="field_name"
													bind:value={localProperties[i].name}
												/>
											</div>
											<div class="space-y-1">
												<Label class="text-xs">Expression</Label>
												<Input
													class="h-8 text-sm"
													placeholder="//xpath or $.jsonpath"
													bind:value={localProperties[i].expression}
												/>
											</div>
											<div class="space-y-1">
												<Label class="text-xs">Type</Label>
												<select
													class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-8 w-full items-center rounded-md border px-3 py-1 text-sm shadow-sm focus:outline-none focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
													bind:value={localProperties[i].type}
												>
													{#each PROPERTY_TYPES as t (t)}
														<option value={t}>{t}</option>
													{/each}
												</select>
											</div>
											<div class="flex items-end gap-4 pb-1">
												<label class="flex items-center gap-1.5 text-sm">
													<Checkbox
														checked={localProperties[i].multivalued ?? false}
														onCheckedChange={(v) => {
															localProperties[i].multivalued = !!v;
															localProperties = localProperties;
														}}
													/>
													Multi
													<Tooltip.Root>
														<Tooltip.Trigger>
															{#snippet child({ props })}
																<span {...props}
																	><HelpCircle class="h-3 w-3 text-muted-foreground" /></span
																>
															{/snippet}
														</Tooltip.Trigger>
														<Tooltip.Content>Field can contain multiple values</Tooltip.Content>
													</Tooltip.Root>
												</label>
											</div>
										</div>
										{#if localProperties[i].type === 'DATETIME'}
											<div class="mt-2 max-w-xs space-y-1">
												<Label class="text-xs">Format</Label>
												<Input
													class="h-8 text-sm"
													placeholder="yyyy-MM-dd"
													bind:value={localProperties[i].format}
												/>
											</div>
										{/if}
									</div>
									<Button
										variant="ghost"
										size="icon"
										class="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
										onclick={() => removeProperty(i)}
									>
										<Trash2 class="h-3.5 w-3.5" />
									</Button>
								</div>
							{/each}
						</div>
					{:else}
						<p class="mt-3 text-sm text-muted-foreground">
							No properties defined. Add properties to define which metadata fields to index.
						</p>
					{/if}
				</div>

				<!-- Assigned Namespaces -->
				<div class="rounded-lg border p-5">
					<h3 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
						Assigned Namespaces
					</h3>
					<p class="mt-1 text-xs text-muted-foreground">
						Namespaces where this content class is active for metadata indexing.
					</p>
					<div class="mt-3">
						{#if localNamespaces.length > 0}
							<div class="mb-3 flex flex-wrap gap-1.5">
								{#each localNamespaces as ns (ns)}
									<Badge variant="secondary" class="gap-1">
										{ns}
										<button
											class="ml-0.5 rounded-full p-0.5 hover:bg-muted"
											onclick={() => removeNamespace(ns)}
										>
											<span class="sr-only">Remove {ns}</span>
											&times;
										</button>
									</Badge>
								{/each}
							</div>
						{/if}
						<div class="flex gap-2">
							<Input
								class="h-8 max-w-xs text-sm"
								placeholder="Namespace name"
								bind:value={nsInput}
								onkeydown={handleNsKeydown}
							/>
							<Button variant="outline" size="sm" onclick={addNamespace}>Add</Button>
						</div>
					</div>
				</div>

				<SaveButton {dirty} {saving} onclick={save} />
			{/if}
		{/await}
	{/if}
</div>

<DeleteConfirmDialog
	bind:open={deleteOpen}
	name={className}
	itemType="content class"
	loading={deleting}
	onconfirm={handleDelete}
/>
