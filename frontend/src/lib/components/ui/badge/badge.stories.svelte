<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import Badge from './badge.svelte';

	const { Story } = defineMeta({
		title: 'UI/Badge',
		component: Badge,
		render: template,
		args: {
			label: 'Badge',
			variant: 'default',
		},
		argTypes: {
			label: { control: 'text' },
			variant: {
				control: 'select',
				options: ['default', 'secondary', 'destructive', 'outline', 'success', 'warning'],
			},
		},
	});
</script>

{#snippet template(args)}
	{@const { label, ...badgeProps } = args}
	<Badge {...badgeProps}>{label}</Badge>
{/snippet}

<Story name="Default" args={{ variant: 'default', label: 'Default' }} />

<Story name="Secondary" args={{ variant: 'secondary', label: 'Secondary' }} />

<Story name="Destructive" args={{ variant: 'destructive', label: 'Destructive' }} />

<Story name="Outline" args={{ variant: 'outline', label: 'Outline' }} />

<Story name="Success" args={{ variant: 'success', label: 'Success' }} />

<Story name="Warning" args={{ variant: 'warning', label: 'Warning' }} />

<Story name="As Link" args={{ variant: 'default', href: '#', label: 'Clickable' }} />

<Story name="All Variants">
	{#snippet template()}
		<div class="flex flex-wrap items-center gap-2">
			<Badge variant="default">Default</Badge>
			<Badge variant="secondary">Secondary</Badge>
			<Badge variant="destructive">Destructive</Badge>
			<Badge variant="outline">Outline</Badge>
			<Badge variant="success">Success</Badge>
			<Badge variant="warning">Warning</Badge>
		</div>
	{/snippet}
</Story>
