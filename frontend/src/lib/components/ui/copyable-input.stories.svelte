<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import CopyableInput from './copyable-input.svelte';

	const { Story } = defineMeta({
		title: 'UI/CopyableInput',
		component: CopyableInput,
		tags: ['autodocs'],
		argTypes: {
			secret: { control: 'boolean' },
		},
	});
</script>

<Story name="Default" args={{ value: 'urn:hcp:namespace:my-namespace', label: 'Canonical ID' }} />

<Story name="Without Label" args={{ value: 'https://hcp.example.com/rest/namespaces' }} />

<Story
	name="Secret"
	args={{ value: 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY', label: 'Secret Key', secret: true }}
/>

<Story name="S3 Credentials">
	{#snippet template()}
		<div class="space-y-3 max-w-md">
			<CopyableInput value="AKIAIOSFODNN7EXAMPLE" label="Access Key" />
			<CopyableInput value="wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY" label="Secret Key" secret />
			<CopyableInput value="https://s3.example.com" label="Endpoint" />
		</div>
	{/snippet}
</Story>
