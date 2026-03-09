<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import { fn } from 'storybook/test';
	import Button from './button.svelte';

	const { Story } = defineMeta({
		title: 'UI/Button',
		component: Button,
		tags: ['autodocs'],
		args: {
			onclick: fn(),
		},
		argTypes: {
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

<Story name="Default" args={{ variant: 'default' }}>
	{#snippet template(args)}
		<Button {...args}>Button</Button>
	{/snippet}
</Story>

<Story name="Destructive" args={{ variant: 'destructive' }}>
	{#snippet template(args)}
		<Button {...args}>Delete</Button>
	{/snippet}
</Story>

<Story name="Outline" args={{ variant: 'outline' }}>
	{#snippet template(args)}
		<Button {...args}>Outline</Button>
	{/snippet}
</Story>

<Story name="Secondary" args={{ variant: 'secondary' }}>
	{#snippet template(args)}
		<Button {...args}>Secondary</Button>
	{/snippet}
</Story>

<Story name="Ghost" args={{ variant: 'ghost' }}>
	{#snippet template(args)}
		<Button {...args}>Ghost</Button>
	{/snippet}
</Story>

<Story name="Link" args={{ variant: 'link' }}>
	{#snippet template(args)}
		<Button {...args}>Link</Button>
	{/snippet}
</Story>

<Story name="Small" args={{ variant: 'default', size: 'sm' }}>
	{#snippet template(args)}
		<Button {...args}>Small</Button>
	{/snippet}
</Story>

<Story name="Large" args={{ variant: 'default', size: 'lg' }}>
	{#snippet template(args)}
		<Button {...args}>Large</Button>
	{/snippet}
</Story>

<Story name="Disabled" args={{ variant: 'default', disabled: true }}>
	{#snippet template(args)}
		<Button {...args}>Disabled</Button>
	{/snippet}
</Story>

<Story name="As Link" args={{ variant: 'default', href: '#' }}>
	{#snippet template(args)}
		<Button {...args}>Link Button</Button>
	{/snippet}
</Story>

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
