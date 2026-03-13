<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import SaveButton from '$lib/components/custom/save-button/save-button.svelte';
	import PageHeader from '$lib/components/custom/page-header/page-header.svelte';
	import { useSave } from '$lib/utils/use-save.svelte.js';
	import {
		get_network_settings,
		update_network_settings,
		type NetworkSettings,
	} from '$lib/remote/system.remote.js';

	let networkData = $derived(get_network_settings({}));
	let network = $derived((networkData?.current ?? {}) as NetworkSettings);

	const saver = useSave({
		successMsg: 'Network settings updated',
		errorMsg: 'Failed to update network settings',
	});

	let localDnsMode = $state('ADVANCED');

	$effect(() => {
		const n = network;
		void saver.syncVersion;
		localDnsMode = n.downstreamDNSMode ?? 'ADVANCED';
	});

	let dirty = $derived(localDnsMode !== (network.downstreamDNSMode ?? 'ADVANCED'));
</script>

<svelte:head>
	<title>Network - System - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<PageHeader title="Network Settings" description="Manage system-level network configuration" />

	{#await networkData}
		<CardSkeleton />
	{:then}
		<Card.Root class="max-w-2xl">
			<Card.Header>
				<Card.Title>DNS Configuration</Card.Title>
				<Card.Description>
					Controls how the HCP system resolves downstream DNS queries.
				</Card.Description>
			</Card.Header>
			<Card.Content class="space-y-4">
				<div class="space-y-1.5">
					<Label for="dns-mode">Downstream DNS Mode</Label>
					<Select.Root type="single" bind:value={localDnsMode}>
						<Select.Trigger id="dns-mode" class="w-48">
							{localDnsMode}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="ADVANCED">ADVANCED</Select.Item>
							<Select.Item value="BASIC">BASIC</Select.Item>
						</Select.Content>
					</Select.Root>
					<p class="text-xs text-muted-foreground">
						ADVANCED mode allows full DNS configuration. BASIC mode uses simplified settings.
					</p>
				</div>
			</Card.Content>
			<Card.Footer>
				<SaveButton
					{dirty}
					saving={saver.saving}
					onclick={() =>
						saver.run(async () => {
							if (!networkData) return;
							await update_network_settings({
								body: { downstreamDNSMode: localDnsMode },
							}).updates(networkData);
						})}
				/>
			</Card.Footer>
		</Card.Root>
	{/await}
</div>
