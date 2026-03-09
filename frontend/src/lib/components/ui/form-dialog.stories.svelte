<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import FormDialog from './form-dialog.svelte';

	const { Story } = defineMeta({
		title: 'UI/FormDialog',
		component: FormDialog,
		tags: ['autodocs'],
	});
</script>

<script>
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Button } from '$lib/components/ui/button/index.js';

	let defaultOpen = $state(false);
	let errorOpen = $state(false);
	let loadingOpen = $state(false);
</script>

<Story name="Default">
	{#snippet template()}
		<Button onclick={() => (defaultOpen = true)}>Open Dialog</Button>
		<FormDialog
			bind:open={defaultOpen}
			title="Create Namespace"
			description="Create a new namespace in the tenant."
			onsubmit={(e) => {
				e.preventDefault();
				defaultOpen = false;
			}}
		>
			<div class="space-y-3">
				<div>
					<Label>Name</Label>
					<Input placeholder="my-namespace" />
				</div>
				<div>
					<Label>Description</Label>
					<Input placeholder="Optional description..." />
				</div>
			</div>
		</FormDialog>
	{/snippet}
</Story>

<Story name="With Error">
	{#snippet template()}
		<Button onclick={() => (errorOpen = true)}>Open With Error</Button>
		<FormDialog
			bind:open={errorOpen}
			title="Create Namespace"
			error="Namespace 'my-namespace' already exists."
			onsubmit={(e) => e.preventDefault()}
		>
			<div>
				<Label>Name</Label>
				<Input value="my-namespace" />
			</div>
		</FormDialog>
	{/snippet}
</Story>

<Story name="Loading">
	{#snippet template()}
		<Button onclick={() => (loadingOpen = true)}>Open Loading</Button>
		<FormDialog
			bind:open={loadingOpen}
			title="Create Namespace"
			loading={true}
			onsubmit={(e) => e.preventDefault()}
		>
			<div>
				<Label>Name</Label>
				<Input value="my-namespace" />
			</div>
		</FormDialog>
	{/snippet}
</Story>
