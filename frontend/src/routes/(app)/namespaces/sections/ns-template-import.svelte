<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import { toast } from 'svelte-sonner';
	import { Upload, FileJson, Loader2, AlertTriangle } from 'lucide-svelte';
	import type { RemoteQuery } from '@sveltejs/kit';
	import {
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
	import {
		type TemplateNamespace,
		type ImportStep,
		PROTOCOLS,
		getTags,
	} from '$lib/types/ns-templates.js';
	import NsImportEditor from './ns-import-editor.svelte';
	import StepProgress from '$lib/components/ui/step-progress.svelte';

	let {
		tenant,
		namespaces,
		nsData,
	}: {
		tenant: string;
		namespaces: Namespace[];
		nsData: RemoteQuery<Namespace[]>;
	} = $props();

	let fileInput: HTMLInputElement | undefined = $state();
	let templateData = $state<TemplateNamespace[]>([]);
	let importNames = $state<string[]>([]);
	let importSteps = $state<ImportStep[]>([]);
	let importing = $state(false);
	let importDone = $state(false);
	let sourceInfo = $state('');

	let existingNames = $derived(new Set(namespaces.map((n) => n.name)));

	let nameConflicts = $derived(
		importNames.map((name, i) => ({ name, index: i })).filter(({ name }) => existingNames.has(name))
	);

	let importSummary = $derived(
		templateData.map((ns, i) => {
			const name = importNames[i] || ns.name;
			const subResources: string[] = [];
			let stepCount = 1;
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

	// Map ImportStep[] to StepProgress format
	let progressSteps = $derived(
		importSteps.map((s) => ({ group: s.ns, label: s.step, status: s.status, error: s.error }))
	);

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

	function handleNameChange(index: number, newName: string) {
		importNames[index] = newName;
		importNames = [...importNames];
	}

	function handleNsUpdate(index: number, updated: TemplateNamespace) {
		templateData[index] = updated;
		templateData = [...templateData];
	}

	async function handleImport() {
		if (templateData.length === 0) return;
		importing = true;
		importDone = false;

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
					steps.push({ ns: name, step: `Create retention class "${rc.name}"`, status: 'pending' });
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
			if (ns.replicationCollision) {
				const replBody = { ...ns.replicationCollision };
				if (!replBody.deleteEnabled) {
					delete replBody.deleteDays;
				}
				await runStep(() => update_repl_collision({ tenant, name, body: replBody }));
			}
		}

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
		if (fileInput) fileInput.value = '';
	}
</script>

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

				<div class="max-h-[32rem] space-y-3 overflow-y-auto">
					{#each templateData as ns, i (i)}
						<NsImportEditor
							{ns}
							index={i}
							name={importNames[i]}
							hasConflict={existingNames.has(importNames[i])}
							disabled={importing || importDone}
							onnamechange={handleNameChange}
							onnsupdate={handleNsUpdate}
						/>
					{/each}
				</div>

				{#if templateData.length > 0 && !importDone && importSteps.length === 0}
					<Separator />
					<div class="space-y-2 rounded-md border bg-muted/30 p-3">
						<h4 class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
							Import Summary
						</h4>
						<div class="text-sm">
							<span class="font-medium">{totalSteps}</span> total step{totalSteps !== 1 ? 's' : ''} across
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
								<AlertTriangle class="mt-0.5 h-4 w-4 shrink-0 text-amber-600 dark:text-amber-400" />
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
					<StepProgress steps={progressSteps} />
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
