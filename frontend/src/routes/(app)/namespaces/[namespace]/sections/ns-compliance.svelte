<script lang="ts">
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_ns_compliance,
		update_ns_compliance,
		type ComplianceSettings,
	} from '$lib/namespaces.remote.js';

	let {
		tenant,
		namespaceName,
	}: {
		tenant: string;
		namespaceName: string;
	} = $props();

	let complianceData = $derived(get_ns_compliance({ tenant, name: namespaceName }));
	let compliance = $derived((complianceData?.current ?? {}) as ComplianceSettings);

	let syncVersion = $state(0);
	let localRetentionDefault = $state('');
	let localMinRetention = $state('');
	let localShreddingDefault = $state(false);
	let localCustomMetadataChanges = $state('');
	let localDispositionEnabled = $state(false);

	$effect(() => {
		const c = compliance;
		void syncVersion;
		localRetentionDefault = c.retentionDefault ?? '';
		localMinRetention = c.minimumRetentionAfterInitialUnspecified ?? '';
		localShreddingDefault = c.shreddingDefault ?? false;
		localCustomMetadataChanges = c.customMetadataChanges ?? '';
		localDispositionEnabled = c.dispositionEnabled ?? false;
	});

	let dirty = $derived(
		localRetentionDefault !== (compliance.retentionDefault ?? '') ||
			localMinRetention !== (compliance.minimumRetentionAfterInitialUnspecified ?? '') ||
			localShreddingDefault !== (compliance.shreddingDefault ?? false) ||
			localCustomMetadataChanges !== (compliance.customMetadataChanges ?? '') ||
			localDispositionEnabled !== (compliance.dispositionEnabled ?? false)
	);

	let saving = $state(false);

	async function save() {
		if (!complianceData) return;
		saving = true;
		try {
			await update_ns_compliance({
				tenant,
				name: namespaceName,
				body: {
					retentionDefault: localRetentionDefault || undefined,
					minimumRetentionAfterInitialUnspecified: localMinRetention || undefined,
					shreddingDefault: localShreddingDefault,
					customMetadataChanges: localCustomMetadataChanges || undefined,
					dispositionEnabled: localDispositionEnabled,
				},
			}).updates(complianceData);
			syncVersion++;
			toast.success('Compliance settings updated');
		} catch {
			toast.error('Failed to update compliance settings');
		} finally {
			saving = false;
		}
	}
</script>

<Card.Root class="flex h-full flex-col">
	<Card.Header>
		<Card.Title>Compliance</Card.Title>
		<Card.Description>
			Controls how objects are retained and protected from modification or deletion.
		</Card.Description>
	</Card.Header>
	{#await complianceData}
		<Card.Content class="flex-1">
			<div class="flex flex-wrap gap-6">
				{#each Array(5) as _, i (i)}
					<div class="h-5 w-32 animate-pulse rounded bg-muted"></div>
				{/each}
			</div>
		</Card.Content>
	{:then}
		<Card.Content class="flex-1 space-y-4">
			<div class="grid gap-4 sm:grid-cols-2">
				<div class="space-y-1.5">
					<Label for="retention-default">Retention Default</Label>
					<Input
						id="retention-default"
						placeholder="e.g. 0, A+1y, or -1"
						bind:value={localRetentionDefault}
					/>
					<p class="text-xs text-muted-foreground">
						0 = deletion allowed, -1 = indefinite, offsets like A+1y.
					</p>
				</div>
				<div class="space-y-1.5">
					<Label for="min-retention">Min Retention After Initial</Label>
					<Input id="min-retention" placeholder="e.g. 0 or A+90d" bind:value={localMinRetention} />
					<p class="text-xs text-muted-foreground">
						Floor for objects initially stored without retention.
					</p>
				</div>
			</div>
			<div class="space-y-1.5">
				<Label>Custom Metadata Changes</Label>
				<Select.Root type="single" bind:value={localCustomMetadataChanges}>
					<Select.Trigger class="w-full">
						{localCustomMetadataChanges || 'Select...'}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="allowed">allowed</Select.Item>
						<Select.Item value="notAllowed">notAllowed</Select.Item>
						<Select.Item value="creationOnly">creationOnly</Select.Item>
					</Select.Content>
				</Select.Root>
			</div>
			<div class="flex flex-wrap gap-x-6 gap-y-3">
				<div class="flex items-center gap-2">
					<Switch id="shredding-default" bind:checked={localShreddingDefault} />
					<Label for="shredding-default" class="text-sm">Shredding Default</Label>
				</div>
				<div class="flex items-center gap-2">
					<Switch id="disposition-enabled" bind:checked={localDispositionEnabled} />
					<Label for="disposition-enabled" class="text-sm">Disposition</Label>
				</div>
			</div>
		</Card.Content>
		<Card.Footer>
			<SaveButton {dirty} {saving} onclick={save} />
		</Card.Footer>
	{/await}
</Card.Root>
