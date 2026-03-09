<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import PageHeader from './page-header.svelte';

	const { Story } = defineMeta({
		title: 'UI/PageHeader',
		component: PageHeader,
		tags: ['autodocs'],
	});
</script>

<Story name="Default" args={{ title: 'Namespaces', description: 'Manage tenant namespaces' }} />

<Story name="With Actions">
	{#snippet template()}
		<PageHeader title="Namespaces" description="Manage tenant namespaces">
			{#snippet actions()}
				<button
					class="inline-flex items-center rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground shadow-xs hover:bg-primary/90"
				>
					Create Namespace
				</button>
			{/snippet}
		</PageHeader>
	{/snippet}
</Story>

<Story name="Long Description">
	{#snippet template()}
		<PageHeader
			title="Settings"
			description="Configure tenant-wide settings including authentication, storage quotas, and network policies."
		/>
	{/snippet}
</Story>
