<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import SaveButton from '$lib/components/custom/save-button/save-button.svelte';
	import IpListEditor from '$lib/components/custom/ip-list-editor/ip-list-editor.svelte';
	import { useSave } from '$lib/utils/use-save.svelte.js';
	import {
		get_ns_protocol_detail,
		update_ns_protocol,
		type IpSettings,
	} from '$lib/remote/namespaces.remote.js';

	let {
		tenant,
		namespaceName,
	}: {
		tenant: string;
		namespaceName: string;
	} = $props();

	let httpData = $derived(
		get_ns_protocol_detail({ tenant, name: namespaceName, protocol: 'http' })
	);
	let ipSettings = $derived((httpData?.current?.ipSettings ?? {}) as IpSettings);

	const saver = useSave({
		successMsg: 'Network restrictions updated',
		errorMsg: 'Failed to update network restrictions',
	});

	let localAllowAddresses = $state<string[]>([]);
	let localDenyAddresses = $state<string[]>([]);
	let localAllowIfInBoth = $state(false);

	$effect(() => {
		const s = ipSettings;
		void saver.syncVersion;
		localAllowAddresses = [...(s.allowAddresses ?? [])];
		localDenyAddresses = [...(s.denyAddresses ?? [])];
		localAllowIfInBoth = s.allowIfInBothLists ?? false;
	});

	function arraysEqual(a: string[], b: string[]): boolean {
		if (a.length !== b.length) return false;
		return a.every((v, i) => v === b[i]);
	}

	let dirty = $derived(
		!arraysEqual(localAllowAddresses, ipSettings.allowAddresses ?? []) ||
			!arraysEqual(localDenyAddresses, ipSettings.denyAddresses ?? []) ||
			localAllowIfInBoth !== (ipSettings.allowIfInBothLists ?? false)
	);
</script>

{#await httpData}
	<CardSkeleton />
{:then}
	<Card.Root>
		<Card.Header>
			<Card.Title>Network Restrictions</Card.Title>
			<Card.Description>
				IP address allow and deny lists for HTTP/S3 protocol access to this namespace.
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-6">
			<IpListEditor
				bind:addresses={localAllowAddresses}
				label="Allow List"
				emptyText="No allow list configured. All addresses are allowed by default."
			/>
			<IpListEditor
				bind:addresses={localDenyAddresses}
				label="Deny List"
				placeholder="IP address or CIDR (e.g. 192.168.1.0/24)"
				variant="destructive"
				emptyText="No deny list configured."
			/>
			<div class="flex items-center gap-2">
				<Switch id="ns-allow-if-both" bind:checked={localAllowIfInBoth} />
				<Label for="ns-allow-if-both" class="text-sm">Allow if in both lists</Label>
			</div>
			<p class="text-xs text-muted-foreground">
				When enabled, addresses that appear in both allow and deny lists will be allowed.
			</p>
		</Card.Content>
		<Card.Footer>
			<SaveButton
				{dirty}
				saving={saver.saving}
				onclick={() =>
					saver.run(async () => {
						if (!httpData) return;
						await update_ns_protocol({
							tenant,
							name: namespaceName,
							protocol: 'http',
							body: {
								ipSettings: {
									allowAddresses: localAllowAddresses.filter(Boolean),
									denyAddresses: localDenyAddresses.filter(Boolean),
									allowIfInBothLists: localAllowIfInBoth,
								},
							},
						}).updates(httpData);
					})}
			/>
		</Card.Footer>
	</Card.Root>
{/await}
