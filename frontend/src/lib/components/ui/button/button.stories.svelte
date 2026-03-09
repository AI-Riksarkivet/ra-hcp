<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import { fn } from 'storybook/test';
	import Button from './button.svelte';

	const { Story } = defineMeta({
		title: 'UI/Button',
		component: Button,
		render: template,
		args: {
			label: 'Button',
			onclick: fn(),
		},
		argTypes: {
			label: { control: 'text' },
			variant: {
				control: 'select',
				options: ['default', 'destructive', 'outline', 'secondary', 'ghost', 'link'],
			},
			size: {
				control: 'select',
				options: ['default', 'sm', 'lg', 'icon', 'icon-sm', 'icon-lg'],
			},
			disabled: { control: 'boolean' },
		},
	});
</script>

{#snippet template(args)}
	{@const { label, ...buttonProps } = args}
	<Button {...buttonProps}>{label}</Button>
{/snippet}

<Story name="Default" args={{ variant: 'default', label: 'Button' }} />

<Story name="Destructive" args={{ variant: 'destructive', label: 'Delete' }} />

<Story name="Outline" args={{ variant: 'outline', label: 'Outline' }} />

<Story name="Secondary" args={{ variant: 'secondary', label: 'Secondary' }} />

<Story name="Ghost" args={{ variant: 'ghost', label: 'Ghost' }} />

<Story name="Link" args={{ variant: 'link', label: 'Link' }} />

<Story name="Small" args={{ variant: 'default', size: 'sm', label: 'Small' }} />

<Story name="Large" args={{ variant: 'default', size: 'lg', label: 'Large' }} />

<Story name="Disabled" args={{ variant: 'default', disabled: true, label: 'Disabled' }} />

<Story name="As Link" args={{ variant: 'default', href: '#', label: 'Link Button' }} />

<Story name="All Variants">
	{#snippet template()}
		<div class="flex flex-wrap items-center gap-3">
			<Button variant="default">Default</Button>
			<Button variant="destructive">Destructive</Button>
			<Button variant="outline">Outline</Button>
			<Button variant="secondary">Secondary</Button>
			<Button variant="ghost">Ghost</Button>
			<Button variant="link">Link</Button>
		</div>
	{/snippet}
</Story>
