<script lang="ts">
	import { SvelteSet } from 'svelte/reactivity';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Collapsible from '$lib/components/ui/collapsible/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import { toast } from 'svelte-sonner';
	import {
		Download,
		Upload,
		Search,
		FileJson,
		CheckCircle,
		XCircle,
		Loader2,
		ChevronDown,
		ChevronRight,
		Eye,
		AlertTriangle,
		Pencil,
		Code,
	} from 'lucide-svelte';
	import type { RemoteQuery } from '@sveltejs/kit';
	import {
		export_namespace_configs,
		create_namespace,
		update_namespace,
		update_versioning,
		update_ns_compliance,
		update_ns_permissions,
		update_ns_protocol,
		create_retention_class,
		update_ns_indexing,
		set_ns_cors,
		update_repl_collision,
		type Namespace,
	} from '$lib/namespaces.remote.js';

	let {
		tenant,
		nsData,
	}: {
		tenant: string;
		nsData: RemoteQuery<Namespace[]>;
	} = $props();

	// ── Export state ────────────────────────────────────────────────────
	let namespaces = $derived((nsData?.current ?? []) as Namespace[]);
	let searchFilter = $state('');
	let selected = new SvelteSet<string>();
	let exporting = $state(false);

	let filteredNamespaces = $derived(
		namespaces.filter((ns) => ns.name.toLowerCase().includes(searchFilter.toLowerCase()))
	);

	let allFilteredSelected = $derived(
		filteredNamespaces.length > 0 && filteredNamespaces.every((ns) => selected.has(ns.name))
	);

	function toggleAll(checked: boolean) {
		for (const ns of filteredNamespaces) {
			if (checked) selected.add(ns.name);
			else selected.delete(ns.name);
		}
	}

	function toggleNamespace(name: string, checked: boolean) {
		if (checked) selected.add(name);
		else selected.delete(name);
	}

	async function handleExport() {
		if (selected.size === 0) return;
		exporting = true;
		try {
			const result = await export_namespace_configs({ tenant, names: [...selected] });
			const blob = new Blob([JSON.stringify(result, null, 2)], { type: 'application/json' });
			const url = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = url;
			a.download = `namespace-templates-${new Date().toISOString().slice(0, 10)}.json`;
			a.click();
			URL.revokeObjectURL(url);
			toast.success(`Exported ${selected.size} namespace template(s)`);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Export failed');
		} finally {
			exporting = false;
		}
	}

	// ── Export Preview Dialog state ────────────────────────────────────
	let previewOpen = $state(false);
	let previewLoading = $state(false);
	let previewData = $state<Record<string, unknown> | null>(null);
	let previewShowRaw = $state(false);
	let previewExpandedNs = new SvelteSet<string>();

	async function handlePreview() {
		if (selected.size === 0) return;
		previewLoading = true;
		previewData = null;
		previewShowRaw = false;
		previewExpandedNs.clear();
		previewOpen = true;
		try {
			const result = await export_namespace_configs({ tenant, names: [...selected] });
			previewData = result as Record<string, unknown>;
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to load preview');
			previewOpen = false;
		} finally {
			previewLoading = false;
		}
	}

	let previewNamespaces = $derived.by<TemplateNamespace[]>(() => {
		if (!previewData) return [];
		if (previewData.namespaces && Array.isArray(previewData.namespaces)) {
			return previewData.namespaces as TemplateNamespace[];
		}
		if (Array.isArray(previewData)) {
			return previewData as TemplateNamespace[];
		}
		return [previewData as unknown as TemplateNamespace];
	});

	function downloadPreview() {
		if (!previewData) return;
		const blob = new Blob([JSON.stringify(previewData, null, 2)], { type: 'application/json' });
		const url = URL.createObjectURL(blob);
		const a = document.createElement('a');
		a.href = url;
		a.download = `namespace-templates-${new Date().toISOString().slice(0, 10)}.json`;
		a.click();
		URL.revokeObjectURL(url);
		toast.success(`Downloaded ${selected.size} namespace template(s)`);
		previewOpen = false;
	}

	function togglePreviewNs(name: string) {
		if (previewExpandedNs.has(name)) previewExpandedNs.delete(name);
		else previewExpandedNs.add(name);
	}

	// ── Import state ───────────────────────────────────────────────────
	interface TemplateNamespace {
		name: string;
		description?: string;
		hardQuota?: string;
		softQuota?: number;
		hashScheme?: string;
		searchEnabled?: boolean;
		versioningEnabled?: boolean;
		tags?: { tag: string[] } | string[];
		versioning?: { enabled: boolean };
		compliance?: Record<string, unknown>;
		permissions?: Record<string, unknown>;
		protocols?: {
			http?: Record<string, unknown>;
			cifs?: Record<string, unknown>;
			nfs?: Record<string, unknown>;
			smtp?: Record<string, unknown>;
		};
		retentionClasses?: {
			name: string;
			value: string;
			description?: string;
			allowDisposition?: boolean;
		}[];
		indexing?: Record<string, unknown>;
		cors?: Record<string, unknown> | string;
		replicationCollision?: Record<string, unknown>;
	}

	interface ImportStep {
		ns: string;
		step: string;
		status: 'pending' | 'running' | 'done' | 'failed';
		error?: string;
	}

	/** Extract tags as a flat string[] regardless of API format ({tag: string[]} or string[]). */
	function getTags(tags: TemplateNamespace['tags']): string[] {
		if (!tags) return [];
		if (Array.isArray(tags)) return tags;
		if (typeof tags === 'object' && 'tag' in tags && Array.isArray(tags.tag)) return tags.tag;
		return [];
	}

	const PROTOCOLS = ['http', 'cifs', 'nfs', 'smtp'] as const;

	const PERMISSION_KEYS = [
		{ key: 'readAllowed', label: 'Read' },
		{ key: 'writeAllowed', label: 'Write' },
		{ key: 'deleteAllowed', label: 'Delete' },
		{ key: 'purgeAllowed', label: 'Purge' },
		{ key: 'searchAllowed', label: 'Search' },
		{ key: 'readAclAllowed', label: 'Read ACL' },
		{ key: 'writeAclAllowed', label: 'Write ACL' },
	] as const;

	let fileInput: HTMLInputElement | undefined = $state();
	let templateData = $state<TemplateNamespace[]>([]);
	let importNames = $state<string[]>([]);
	let importSteps = $state<ImportStep[]>([]);
	let importing = $state(false);
	let importDone = $state(false);
	let sourceInfo = $state('');

	// ── Import Editor state ────────────────────────────────────────────
	let editorExpandedNs = new SvelteSet<number>();
	let editorRawMode = new SvelteSet<number>();

	// Raw JSON text per namespace for the raw JSON textarea toggle
	let rawJsonTexts = $state<string[]>([]);

	// Track name conflicts: check importNames against existing namespaces
	let existingNames = $derived(new Set(namespaces.map((n) => n.name)));

	let nameConflicts = $derived(
		importNames.map((name, i) => ({ name, index: i })).filter(({ name }) => existingNames.has(name))
	);

	// Build import summary: count steps and sub-resources per namespace
	let importSummary = $derived(
		templateData.map((ns, i) => {
			const name = importNames[i] || ns.name;
			const subResources: string[] = [];
			let stepCount = 1; // Create namespace is always step 1
			if (ns.versioning) {
				subResources.push('versioning');
				stepCount++;
			}
			if (ns.compliance) {
				subResources.push('compliance');
				stepCount++;
			}
			if (ns.permissions) {
				subResources.push('permissions');
				stepCount++;
			}
			for (const proto of PROTOCOLS) {
				if (ns.protocols?.[proto]) {
					subResources.push(`${proto.toUpperCase()} protocol`);
					stepCount++;
				}
			}
			if (ns.retentionClasses?.length) {
				const count = ns.retentionClasses.length;
				subResources.push(`${count} retention class${count !== 1 ? 'es' : ''}`);
				stepCount += count;
			}
			if (ns.indexing) {
				subResources.push('indexing');
				stepCount++;
			}
			if (ns.cors) {
				subResources.push('CORS');
				stepCount++;
			}
			if (ns.replicationCollision) {
				subResources.push('replication collision');
				stepCount++;
			}
			return { name, stepCount, subResources, hasConflict: existingNames.has(name) };
		})
	);

	let totalSteps = $derived(importSummary.reduce((sum, s) => sum + s.stepCount, 0));

	function handleFileSelect(e: Event) {
		const input = e.currentTarget as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		const reader = new FileReader();
		reader.onload = () => {
			try {
				const parsed = JSON.parse(reader.result as string);
				let templates: TemplateNamespace[];
				if (parsed.namespaces && Array.isArray(parsed.namespaces)) {
					templates = parsed.namespaces;
					sourceInfo = parsed.sourceTenant ? `from tenant "${parsed.sourceTenant}"` : '';
				} else if (Array.isArray(parsed)) {
					templates = parsed;
					sourceInfo = '';
				} else {
					templates = [parsed];
					sourceInfo = '';
				}
				templateData = templates;
				importNames = templates.map((t) => t.name);
				importSteps = [];
				importDone = false;
				editorExpandedNs.clear();
				editorRawMode.clear();
				rawJsonTexts = templates.map((t) => JSON.stringify(t, null, 2));
			} catch {
				toast.error('Invalid JSON file');
			}
		};
		reader.readAsText(file);
	}

	function summarizeNamespace(ns: TemplateNamespace): string {
		const parts: string[] = [];
		if (ns.hashScheme) parts.push(ns.hashScheme);
		if (ns.hardQuota) parts.push(`${ns.hardQuota} quota`);
		if (ns.versioningEnabled || ns.versioning?.enabled) parts.push('versioning: on');
		if (ns.searchEnabled) parts.push('search: on');
		const tagList = getTags(ns.tags);
		if (tagList.length) parts.push(`tags: ${tagList.join(', ')}`);
		return parts.join(' | ') || 'default settings';
	}

	// ── Editor helpers ─────────────────────────────────────────────────
	function toggleEditorNs(idx: number) {
		if (editorExpandedNs.has(idx)) editorExpandedNs.delete(idx);
		else editorExpandedNs.add(idx);
	}

	function toggleEditorRaw(idx: number) {
		if (editorRawMode.has(idx)) {
			// Switching from raw to structured: try to parse the raw JSON back
			try {
				const parsed = JSON.parse(rawJsonTexts[idx]);
				templateData[idx] = parsed;
				templateData = [...templateData];
				editorRawMode.delete(idx);
			} catch {
				toast.error('Invalid JSON -- fix errors before switching to structured view');
			}
		} else {
			// Switching from structured to raw: serialize current state
			rawJsonTexts[idx] = JSON.stringify(templateData[idx], null, 2);
			rawJsonTexts = [...rawJsonTexts];
			editorRawMode.add(idx);
		}
	}

	function updateRawJson(idx: number, value: string) {
		rawJsonTexts[idx] = value;
		rawJsonTexts = [...rawJsonTexts];
	}

	function updateNsField(idx: number, field: keyof TemplateNamespace, value: unknown) {
		const ns = { ...templateData[idx] };
		(ns as Record<string, unknown>)[field] = value;
		templateData[idx] = ns;
		templateData = [...templateData];
	}

	function updatePermission(idx: number, key: string, value: boolean) {
		const ns = { ...templateData[idx] };
		ns.permissions = { ...(ns.permissions ?? {}), [key]: value };
		templateData[idx] = ns;
		templateData = [...templateData];
	}

	function updateTags(idx: number, tagsStr: string) {
		const tagArr = tagsStr
			.split(',')
			.map((t) => t.trim())
			.filter(Boolean);
		updateNsField(idx, 'tags', tagArr.length > 0 ? { tag: tagArr } : undefined);
	}

	// ── Import execution ───────────────────────────────────────────────
	async function handleImport() {
		if (templateData.length === 0) return;
		importing = true;
		importDone = false;

		// Build step list
		const steps: ImportStep[] = [];
		for (let i = 0; i < templateData.length; i++) {
			const ns = templateData[i];
			const name = importNames[i] || ns.name;
			steps.push({ ns: name, step: 'Create namespace', status: 'pending' });
			if (ns.versioning) steps.push({ ns: name, step: 'Set versioning', status: 'pending' });
			if (ns.compliance) steps.push({ ns: name, step: 'Set compliance', status: 'pending' });
			if (ns.permissions) steps.push({ ns: name, step: 'Set permissions', status: 'pending' });
			for (const proto of PROTOCOLS) {
				if (ns.protocols?.[proto])
					steps.push({ ns: name, step: `Set ${proto.toUpperCase()} protocol`, status: 'pending' });
			}
			if (ns.retentionClasses?.length) {
				for (const rc of ns.retentionClasses) {
					steps.push({
						ns: name,
						step: `Create retention class "${rc.name}"`,
						status: 'pending',
					});
				}
			}
			if (ns.indexing) steps.push({ ns: name, step: 'Set indexing', status: 'pending' });
			if (ns.cors) steps.push({ ns: name, step: 'Set CORS', status: 'pending' });
			if (ns.replicationCollision)
				steps.push({ ns: name, step: 'Set replication collision', status: 'pending' });
		}
		importSteps = steps;

		let stepIdx = 0;
		async function runStep(fn: () => Promise<void>) {
			importSteps[stepIdx].status = 'running';
			importSteps = [...importSteps];
			try {
				await fn();
				importSteps[stepIdx].status = 'done';
			} catch (err) {
				importSteps[stepIdx].status = 'failed';
				importSteps[stepIdx].error = err instanceof Error ? err.message : 'Unknown error';
			}
			importSteps = [...importSteps];
			stepIdx++;
		}

		// Execute steps
		for (let i = 0; i < templateData.length; i++) {
			const ns = templateData[i];
			const name = importNames[i] || ns.name;

			await runStep(() =>
				create_namespace({
					tenant,
					name,
					description: ns.description,
					hardQuota: ns.hardQuota,
					softQuota: ns.softQuota,
					hashScheme: ns.hashScheme,
					searchEnabled: ns.searchEnabled,
					versioningEnabled: ns.versioningEnabled,
					tags: getTags(ns.tags),
				})
			);

			if (ns.versioning)
				await runStep(() => update_versioning({ tenant, name, enabled: ns.versioning!.enabled }));
			if (ns.compliance)
				await runStep(() => update_ns_compliance({ tenant, name, body: ns.compliance! }));
			if (ns.permissions)
				await runStep(() => update_ns_permissions({ tenant, name, body: ns.permissions! }));
			for (const proto of PROTOCOLS) {
				if (ns.protocols?.[proto]) {
					await runStep(() =>
						update_ns_protocol({
							tenant,
							name,
							protocol: proto,
							body: ns.protocols![proto]!,
						})
					);
				}
			}
			if (ns.retentionClasses?.length) {
				for (const rc of ns.retentionClasses) {
					await runStep(() =>
						create_retention_class({
							tenant,
							namespace: name,
							body: {
								name: rc.name,
								value: rc.value,
								description: rc.description,
								allowDisposition: rc.allowDisposition,
							},
						})
					);
				}
			}
			if (ns.indexing)
				await runStep(() => update_ns_indexing({ tenant, name, body: ns.indexing! }));
			if (ns.cors) {
				const corsStr = typeof ns.cors === 'string' ? ns.cors : JSON.stringify(ns.cors);
				await runStep(() => set_ns_cors({ tenant, name, body: { cors: corsStr } }));
			}
			if (ns.replicationCollision)
				await runStep(() =>
					update_repl_collision({ tenant, name, body: ns.replicationCollision! })
				);
		}

		// Refresh namespace list
		const lastName =
			importNames[importNames.length - 1] || templateData[templateData.length - 1]?.name;
		if (lastName) {
			try {
				await update_namespace({ tenant, name: lastName, body: {} }).updates(nsData);
			} catch {
				// Ignore -- list refreshes on next navigation
			}
		}

		importing = false;
		importDone = true;

		const succeeded = importSteps.filter((s) => s.status === 'done').length;
		const failed = importSteps.filter((s) => s.status === 'failed').length;
		if (failed === 0) toast.success(`Successfully imported ${templateData.length} namespace(s)`);
		else toast.warning(`Import completed: ${succeeded} steps succeeded, ${failed} failed`);
	}

	function clearImport() {
		templateData = [];
		importNames = [];
		importSteps = [];
		importDone = false;
		importing = false;
		editorExpandedNs.clear();
		editorRawMode.clear();
		rawJsonTexts = [];
		if (fileInput) fileInput.value = '';
	}
</script>

<!-- ── Export Preview Dialog ───────────────────────────────────────── -->
<Dialog.Root open={previewOpen} onOpenChange={(v) => (previewOpen = v)}>
	<Dialog.Content class="sm:max-w-2xl">
		<Dialog.Header>
			<Dialog.Title>Export Preview</Dialog.Title>
			<Dialog.Description>Review the exported configuration before downloading.</Dialog.Description>
		</Dialog.Header>

		{#if previewLoading}
			<div class="flex items-center justify-center py-12">
				<Loader2 class="h-6 w-6 animate-spin text-muted-foreground" />
				<span class="ml-2 text-sm text-muted-foreground">Loading export data...</span>
			</div>
		{:else if previewData}
			<div class="space-y-3">
				<!-- Toggle raw JSON -->
				<div class="flex items-center justify-end gap-2">
					<Label for="preview-raw-toggle" class="text-xs text-muted-foreground">Raw JSON</Label>
					<Switch
						id="preview-raw-toggle"
						checked={previewShowRaw}
						onCheckedChange={(v) => (previewShowRaw = v)}
					/>
				</div>

				{#if previewShowRaw}
					<div class="max-h-96 overflow-auto rounded-md border bg-muted/50 p-3">
						<pre class="whitespace-pre-wrap text-xs">{JSON.stringify(previewData, null, 2)}</pre>
					</div>
				{:else}
					<div class="max-h-96 space-y-2 overflow-y-auto">
						{#each previewNamespaces as ns (ns.name)}
							{@const expanded = previewExpandedNs.has(ns.name)}
							<div class="rounded-md border">
								<button
									type="button"
									class="flex w-full items-center gap-2 p-3 text-left hover:bg-muted/50"
									onclick={() => togglePreviewNs(ns.name)}
								>
									{#if expanded}
										<ChevronDown class="h-4 w-4 shrink-0 text-muted-foreground" />
									{:else}
										<ChevronRight class="h-4 w-4 shrink-0 text-muted-foreground" />
									{/if}
									<span class="text-sm font-medium">{ns.name}</span>
									{#if ns.hashScheme}
										<Badge variant="secondary" class="text-xs">{ns.hashScheme}</Badge>
									{/if}
									{#if ns.hardQuota}
										<Badge variant="outline" class="text-xs">{ns.hardQuota}</Badge>
									{/if}
								</button>

								{#if expanded}
									<div class="space-y-2 border-t px-3 pb-3 pt-2">
										{#if ns.description}
											<div class="text-xs">
												<span class="font-medium text-muted-foreground">Description:</span>
												{ns.description}
											</div>
										{/if}

										<div class="flex flex-wrap gap-1.5">
											{#if ns.searchEnabled}
												<Badge variant="secondary" class="text-xs">Search: on</Badge>
											{/if}
											{#if ns.versioningEnabled || ns.versioning?.enabled}
												<Badge variant="secondary" class="text-xs">Versioning: on</Badge>
											{/if}
											{#if ns.softQuota != null}
												<Badge variant="outline" class="text-xs">
													Soft quota: {ns.softQuota}%
												</Badge>
											{/if}
										</div>

										{#if getTags(ns.tags).length}
											<div class="flex flex-wrap gap-1">
												<span class="text-xs font-medium text-muted-foreground">Tags:</span>
												{#each getTags(ns.tags) as tag (tag)}
													<Badge variant="outline" class="text-xs">{tag}</Badge>
												{/each}
											</div>
										{/if}

										{#if ns.permissions}
											<div>
												<span class="text-xs font-medium text-muted-foreground">
													Permissions:
												</span>
												<div class="mt-1 flex flex-wrap gap-1">
													{#each Object.entries(ns.permissions) as [key, val] (key)}
														<Badge variant={val ? 'secondary' : 'outline'} class="text-xs">
															{key.replace('Allowed', '')}: {val ? 'yes' : 'no'}
														</Badge>
													{/each}
												</div>
											</div>
										{/if}

										{#if ns.compliance}
											<div>
												<span class="text-xs font-medium text-muted-foreground"> Compliance: </span>
												<div class="mt-1 flex flex-wrap gap-1">
													{#each Object.entries(ns.compliance) as [key, val] (key)}
														<Badge variant="outline" class="text-xs">
															{key}: {val}
														</Badge>
													{/each}
												</div>
											</div>
										{/if}

										{#if ns.retentionClasses?.length}
											<div>
												<span class="text-xs font-medium text-muted-foreground">
													Retention Classes ({ns.retentionClasses.length}):
												</span>
												<div class="mt-1 flex flex-wrap gap-1">
													{#each ns.retentionClasses as rc (rc.name)}
														<Badge variant="outline" class="text-xs">
															{rc.name} = {rc.value}
														</Badge>
													{/each}
												</div>
											</div>
										{/if}

										{#if ns.protocols}
											<div>
												<span class="text-xs font-medium text-muted-foreground"> Protocols: </span>
												<div class="mt-1 flex flex-wrap gap-1">
													{#each Object.keys(ns.protocols) as proto (proto)}
														<Badge variant="secondary" class="text-xs">
															{proto.toUpperCase()}
														</Badge>
													{/each}
												</div>
											</div>
										{/if}
									</div>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<Dialog.Footer>
				<Button variant="ghost" onclick={() => (previewOpen = false)}>Close</Button>
				<Button onclick={downloadPreview}>
					<Download class="h-4 w-4" />
					Download
				</Button>
			</Dialog.Footer>
		{/if}
	</Dialog.Content>
</Dialog.Root>

<div class="grid gap-6 lg:grid-cols-2">
	<!-- Export Card -->
	<Card.Root>
		<Card.Header>
			<div class="flex items-center gap-2">
				<Download class="h-5 w-5 text-muted-foreground" />
				<div>
					<Card.Title>Export Templates</Card.Title>
					<Card.Description>Export namespace configurations as JSON templates</Card.Description>
				</div>
			</div>
		</Card.Header>
		<Card.Content class="space-y-4">
			<div class="relative">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<Input bind:value={searchFilter} placeholder="Filter namespaces..." class="pl-10" />
			</div>

			<div class="max-h-72 space-y-1 overflow-y-auto rounded-md border p-3">
				<div class="mb-1 flex items-center gap-2 border-b pb-2">
					<Checkbox checked={allFilteredSelected} onCheckedChange={(val) => toggleAll(!!val)} />
					<span class="text-sm font-medium">
						{allFilteredSelected ? 'Deselect all' : 'Select all'}
						{searchFilter ? ` matching (${filteredNamespaces.length})` : ` (${namespaces.length})`}
					</span>
				</div>
				{#each filteredNamespaces as ns (ns.name)}
					<div class="flex items-center gap-2">
						<Checkbox
							checked={selected.has(ns.name)}
							onCheckedChange={(val) => toggleNamespace(ns.name, !!val)}
						/>
						<span class="text-sm">{ns.name}</span>
					</div>
				{/each}
				{#if filteredNamespaces.length === 0}
					<p class="py-2 text-center text-sm text-muted-foreground">No namespaces found</p>
				{/if}
			</div>

			<div class="flex items-center justify-between">
				<p class="text-sm text-muted-foreground">{selected.size} selected</p>
				<div class="flex gap-2">
					<Button
						variant="outline"
						onclick={handlePreview}
						disabled={selected.size === 0 || previewLoading}
					>
						{#if previewLoading}
							<Loader2 class="h-4 w-4 animate-spin" />
							Loading...
						{:else}
							<Eye class="h-4 w-4" />
							Preview
						{/if}
					</Button>
					<Button onclick={handleExport} disabled={selected.size === 0 || exporting}>
						{#if exporting}
							<Loader2 class="h-4 w-4 animate-spin" />
							Exporting...
						{:else}
							<Download class="h-4 w-4" />
							Export Selected
						{/if}
					</Button>
				</div>
			</div>
		</Card.Content>
	</Card.Root>

	<!-- Import Card -->
	<Card.Root>
		<Card.Header>
			<div class="flex items-center gap-2">
				<Upload class="h-5 w-5 text-muted-foreground" />
				<div>
					<Card.Title>Import Template</Card.Title>
					<Card.Description>Create namespaces from a JSON template file</Card.Description>
				</div>
			</div>
		</Card.Header>
		<Card.Content class="space-y-4">
			<input
				bind:this={fileInput}
				type="file"
				accept=".json"
				class="hidden"
				onchange={handleFileSelect}
			/>

			{#if templateData.length === 0}
				<button
					type="button"
					class="flex w-full cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed p-8 text-muted-foreground transition-colors hover:border-primary hover:text-primary"
					onclick={() => fileInput?.click()}
				>
					<FileJson class="h-10 w-10" />
					<p class="text-sm font-medium">Click to browse for a template file</p>
					<p class="text-xs">Accepts .json files exported from this tool</p>
				</button>
			{:else}
				<div class="space-y-3">
					<div class="flex items-center justify-between">
						<div>
							<h4 class="text-sm font-medium">
								{templateData.length} namespace{templateData.length !== 1 ? 's' : ''} in template
							</h4>
							{#if sourceInfo}
								<p class="text-xs text-muted-foreground">{sourceInfo}</p>
							{/if}
						</div>
						<Button variant="ghost" size="sm" onclick={clearImport}>Clear</Button>
					</div>

					<Separator />

					<!-- Namespace list with inline editors -->
					<div class="max-h-[32rem] space-y-3 overflow-y-auto">
						{#each templateData as ns, i (i)}
							{@const hasConflict = existingNames.has(importNames[i])}
							<div class="space-y-1 rounded-md border p-3" class:border-amber-500={hasConflict}>
								<div class="flex items-center gap-2">
									<div class="flex-1 space-y-1">
										<Label for="import-name-{i}">Name</Label>
										<Input
											id="import-name-{i}"
											bind:value={importNames[i]}
											placeholder={ns.name}
											disabled={importing || importDone}
										/>
									</div>
								</div>

								{#if hasConflict}
									<div class="flex items-center gap-1.5 pt-1 text-xs text-amber-600">
										<AlertTriangle class="h-3.5 w-3.5 shrink-0" />
										<span>
											A namespace named "{importNames[i]}" already exists. Import will fail unless
											you change this name.
										</span>
									</div>
								{/if}

								<p class="text-xs text-muted-foreground">{summarizeNamespace(ns)}</p>

								<!-- Edit Settings collapsible section -->
								{#if !importing && !importDone}
									<Collapsible.Root
										open={editorExpandedNs.has(i)}
										onOpenChange={() => toggleEditorNs(i)}
									>
										<Collapsible.Trigger
											class="mt-1 flex items-center gap-1 text-xs font-medium text-primary hover:underline"
										>
											{#if editorExpandedNs.has(i)}
												<ChevronDown class="h-3.5 w-3.5" />
											{:else}
												<ChevronRight class="h-3.5 w-3.5" />
											{/if}
											<Pencil class="h-3 w-3" />
											Edit Settings
										</Collapsible.Trigger>
										<Collapsible.Content>
											<div class="mt-2 space-y-3 rounded-md border bg-muted/30 p-3">
												<!-- Toggle between structured and raw -->
												<div class="flex items-center justify-end gap-2">
													<button
														type="button"
														class="flex items-center gap-1 text-xs text-muted-foreground hover:text-foreground"
														onclick={() => toggleEditorRaw(i)}
													>
														{#if editorRawMode.has(i)}
															<Pencil class="h-3 w-3" />
															Structured view
														{:else}
															<Code class="h-3 w-3" />
															Raw JSON
														{/if}
													</button>
												</div>

												{#if editorRawMode.has(i)}
													<!-- Raw JSON editor -->
													<Textarea
														value={rawJsonTexts[i]}
														oninput={(e) =>
															updateRawJson(i, (e.currentTarget as HTMLTextAreaElement).value)}
														class="min-h-48 font-mono text-xs"
														placeholder="Edit raw JSON..."
													/>
													<p class="text-xs text-muted-foreground">
														Switch back to structured view to apply changes.
													</p>
												{:else}
													<!-- Structured editor -->
													<div class="space-y-3">
														<!-- Description -->
														<div class="space-y-1">
															<Label for="edit-desc-{i}" class="text-xs">Description</Label>
															<Input
																id="edit-desc-{i}"
																value={ns.description ?? ''}
																oninput={(e) =>
																	updateNsField(
																		i,
																		'description',
																		(e.currentTarget as HTMLInputElement).value || undefined
																	)}
																placeholder="Optional description"
															/>
														</div>

														<!-- Quotas -->
														<div class="grid grid-cols-2 gap-3">
															<div class="space-y-1">
																<Label for="edit-hard-{i}" class="text-xs">Hard Quota</Label>
																<Input
																	id="edit-hard-{i}"
																	value={ns.hardQuota ?? ''}
																	oninput={(e) =>
																		updateNsField(
																			i,
																			'hardQuota',
																			(e.currentTarget as HTMLInputElement).value || undefined
																		)}
																	placeholder="e.g. 50 GB"
																/>
															</div>
															<div class="space-y-1">
																<Label for="edit-soft-{i}" class="text-xs">Soft Quota (%)</Label>
																<Input
																	id="edit-soft-{i}"
																	type="number"
																	min="10"
																	max="95"
																	value={ns.softQuota != null ? String(ns.softQuota) : ''}
																	oninput={(e) => {
																		const val = (e.currentTarget as HTMLInputElement).value;
																		updateNsField(i, 'softQuota', val ? Number(val) : undefined);
																	}}
																	placeholder="85"
																/>
															</div>
														</div>

														<!-- Feature toggles -->
														<div class="flex flex-wrap gap-x-5 gap-y-2">
															<div class="flex items-center gap-2">
																<Switch
																	id="edit-search-{i}"
																	checked={ns.searchEnabled ?? false}
																	onCheckedChange={(v) => updateNsField(i, 'searchEnabled', v)}
																/>
																<Label for="edit-search-{i}" class="text-xs">Search</Label>
															</div>
															<div class="flex items-center gap-2">
																<Switch
																	id="edit-versioning-{i}"
																	checked={ns.versioningEnabled ?? ns.versioning?.enabled ?? false}
																	onCheckedChange={(v) => {
																		updateNsField(i, 'versioningEnabled', v);
																		if (ns.versioning) {
																			const updated = { ...ns };
																			updated.versioning = {
																				...updated.versioning!,
																				enabled: v,
																			};
																			templateData[i] = updated;
																			templateData = [...templateData];
																		}
																	}}
																/>
																<Label for="edit-versioning-{i}" class="text-xs">Versioning</Label>
															</div>
														</div>

														<!-- Hash scheme (read-only) -->
														{#if ns.hashScheme}
															<div class="flex items-center gap-2">
																<span class="text-xs text-muted-foreground"> Hash Scheme: </span>
																<Badge variant="secondary" class="text-xs">
																	{ns.hashScheme}
																</Badge>
																<span class="text-xs text-muted-foreground">
																	(read-only, set at creation)
																</span>
															</div>
														{/if}

														<!-- Tags -->
														<div class="space-y-1">
															<Label for="edit-tags-{i}" class="text-xs">
																Tags (comma-separated)
															</Label>
															<Input
																id="edit-tags-{i}"
																value={getTags(ns.tags).join(', ')}
																oninput={(e) =>
																	updateTags(i, (e.currentTarget as HTMLInputElement).value)}
																placeholder="e.g. lakefs, nfs, s3"
															/>
														</div>

														<!-- Permissions -->
														{#if ns.permissions || true}
															<div class="space-y-1.5">
																<span class="text-xs font-medium">Permissions</span>
																<div class="grid grid-cols-2 gap-x-4 gap-y-1.5">
																	{#each PERMISSION_KEYS as perm (perm.key)}
																		{@const checked =
																			(ns.permissions as Record<string, boolean>)?.[perm.key] ??
																			false}
																		<div class="flex items-center gap-2">
																			<Switch
																				id="edit-perm-{i}-{perm.key}"
																				{checked}
																				onCheckedChange={(v) => updatePermission(i, perm.key, v)}
																			/>
																			<Label for="edit-perm-{i}-{perm.key}" class="text-xs">
																				{perm.label}
																			</Label>
																		</div>
																	{/each}
																</div>
															</div>
														{/if}
													</div>
												{/if}
											</div>
										</Collapsible.Content>
									</Collapsible.Root>
								{/if}
							</div>
						{/each}
					</div>

					<!-- Import Preview Summary -->
					{#if templateData.length > 0 && !importDone && importSteps.length === 0}
						<Separator />
						<div class="space-y-2 rounded-md border bg-muted/30 p-3">
							<h4 class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
								Import Summary
							</h4>
							<div class="text-sm">
								<span class="font-medium">{totalSteps}</span> total step{totalSteps !== 1
									? 's'
									: ''} across
								<span class="font-medium">{templateData.length}</span>
								namespace{templateData.length !== 1 ? 's' : ''}
							</div>
							<div class="space-y-1">
								{#each importSummary as summary (summary.name)}
									<div class="text-xs">
										<span class="font-medium">{summary.name}</span>:
										{summary.stepCount} step{summary.stepCount !== 1 ? 's' : ''}
										{#if summary.subResources.length > 0}
											<span class="text-muted-foreground">
												({summary.subResources.join(', ')})
											</span>
										{/if}
									</div>
								{/each}
							</div>

							{#if nameConflicts.length > 0}
								<div
									class="mt-2 flex items-start gap-2 rounded-md border border-amber-400 bg-amber-50 p-2 dark:bg-amber-950/30"
								>
									<AlertTriangle
										class="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400"
									/>
									<div class="text-xs text-amber-800 dark:text-amber-200">
										<span class="font-medium">Name conflicts detected:</span>
										{nameConflicts.map((c) => `"${c.name}"`).join(', ')}
										{nameConflicts.length === 1 ? ' already exists' : ' already exist'}
										in this tenant. Rename {nameConflicts.length === 1 ? 'it' : 'them'} above or the import
										will fail.
									</div>
								</div>
							{/if}
						</div>
					{/if}

					{#if importSteps.length > 0}
						<Separator />
						<div class="max-h-48 space-y-1 overflow-y-auto rounded-md border p-3">
							{#each importSteps as step (step.ns + step.step)}
								<div class="flex items-center gap-2 text-sm">
									{#if step.status === 'pending'}
										<div class="h-4 w-4 rounded-full border border-muted-foreground"></div>
									{:else if step.status === 'running'}
										<Loader2 class="h-4 w-4 animate-spin text-primary" />
									{:else if step.status === 'done'}
										<CheckCircle class="h-4 w-4 text-green-600" />
									{:else}
										<XCircle class="h-4 w-4 text-destructive" />
									{/if}
									<span class="truncate">
										<span class="font-medium">{step.ns}</span>: {step.step}
									</span>
									{#if step.error}
										<Badge variant="destructive" class="ml-auto shrink-0 text-xs">
											{step.error}
										</Badge>
									{/if}
								</div>
							{/each}
						</div>
					{/if}

					{#if !importDone}
						<Button
							class="w-full"
							onclick={handleImport}
							disabled={importing || templateData.length === 0}
						>
							{#if importing}
								<Loader2 class="h-4 w-4 animate-spin" />
								Importing...
							{:else}
								<Upload class="h-4 w-4" />
								Create from Template
							{/if}
						</Button>
					{:else}
						<Button variant="outline" class="w-full" onclick={clearImport}>Import Another</Button>
					{/if}
				</div>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
