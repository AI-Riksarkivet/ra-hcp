<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import IpListEditor from './ip-list-editor.svelte';

	const { Story } = defineMeta({
		title: 'UI/IpListEditor',
		component: IpListEditor,
		tags: ['autodocs'],
	});
</script>

<script lang="ts">
	let emptyAddresses = $state<string[]>([]);
	let populatedAddresses = $state(['10.0.0.0/8', '192.168.1.0/24', '172.16.0.0/12']);
	let destructiveAddresses = $state(['10.0.0.1', '192.168.1.100']);
</script>

<Story name="Empty">
	{#snippet template()}
		<IpListEditor bind:addresses={emptyAddresses} label="Allowed IPs" />
	{/snippet}
</Story>

<Story name="With Addresses">
	{#snippet template()}
		<IpListEditor bind:addresses={populatedAddresses} label="Allow List" />
	{/snippet}
</Story>

<Story name="Destructive Variant">
	{#snippet template()}
		<IpListEditor
			bind:addresses={destructiveAddresses}
			label="Deny List"
			variant="destructive"
			placeholder="Block IP address..."
			emptyText="No blocked addresses."
		/>
	{/snippet}
</Story>

<Story name="Disabled">
	{#snippet template()}
		<IpListEditor
			addresses={['10.0.0.0/8', '192.168.1.0/24']}
			label="Read-only IPs"
			disabled={true}
		/>
	{/snippet}
</Story>
