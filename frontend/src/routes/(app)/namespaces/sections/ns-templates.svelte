<script lang="ts">
	import { SvelteSet } from 'svelte/reactivity';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { toast } from 'svelte-sonner';
	import { Download, Upload, Search, FileJson, CheckCircle, XCircle, Loader2 } from 'lucide-svelte';
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

	// ── Import state ───────────────────────────────────────────────────
	interface TemplateNamespace {
		name: string;
		description?: string;
		hardQuota?: string;
		softQuota?: number;
		hashScheme?: string;
		searchEnabled?: boolean;
		versioningEnabled?: boolean;
		tags?: string[];
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

	const PROTOCOLS = ['http', 'cifs', 'nfs', 'smtp'] as const;

	let fileInput: HTMLInputElement | undefined = $state();
	let templateData = $state<TemplateNamespace[]>([]);
	let importNames = $state<string[]>([]);
	let importSteps = $state<ImportStep[]>([]);
	let importing = $state(false);
	let importDone = $state(false);
	let sourceInfo = $state('');

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
		return parts.join(' | ') || 'default settings';
	}

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
					tags: ns.tags,
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
				// Ignore — list refreshes on next navigation
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
		if (fileInput) fileInput.value = '';
	}
</script>

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

					<div class="max-h-64 space-y-3 overflow-y-auto">
						{#each templateData as ns, i (i)}
							<div class="space-y-1 rounded-md border p-3">
								<Label for="import-name-{i}">Name</Label>
								<Input
									id="import-name-{i}"
									bind:value={importNames[i]}
									placeholder={ns.name}
									disabled={importing || importDone}
								/>
								<p class="text-xs text-muted-foreground">{summarizeNamespace(ns)}</p>
							</div>
						{/each}
					</div>

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
