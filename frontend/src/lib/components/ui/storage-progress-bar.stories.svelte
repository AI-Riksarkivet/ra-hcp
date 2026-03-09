<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import StorageProgressBar from './storage-progress-bar.svelte';

	const { Story } = defineMeta({
		title: 'UI/StorageProgressBar',
		component: StorageProgressBar,
		tags: ['autodocs'],
		argTypes: {
			percent: { control: { type: 'range', min: 0, max: 100, step: 1 } },
		},
	});
</script>

<Story name="Low Usage" args={{ percent: 30 }}>
	{#snippet template(args)}
		<div class="w-64">
			<StorageProgressBar {...args} />
			<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
		</div>
	{/snippet}
</Story>

<Story name="Medium Usage" args={{ percent: 65 }}>
	{#snippet template(args)}
		<div class="w-64">
			<StorageProgressBar {...args} />
			<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used</p>
		</div>
	{/snippet}
</Story>

<Story name="Warning" args={{ percent: 80 }}>
	{#snippet template(args)}
		<div class="w-64">
			<StorageProgressBar {...args} />
			<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used — approaching limit</p>
		</div>
	{/snippet}
</Story>

<Story name="Critical" args={{ percent: 95 }}>
	{#snippet template(args)}
		<div class="w-64">
			<StorageProgressBar {...args} />
			<p class="mt-1 text-xs text-muted-foreground">{args.percent}% used — over quota!</p>
		</div>
	{/snippet}
</Story>

<Story name="All Levels">
	{#snippet template()}
		<div class="space-y-4 w-64">
			{#each [10, 30, 50, 70, 80, 90, 95, 100] as pct}
				<div>
					<div class="flex justify-between text-xs text-muted-foreground mb-1">
						<span>{pct}%</span>
						<span>{pct > 90 ? 'Critical' : pct > 70 ? 'Warning' : 'OK'}</span>
					</div>
					<StorageProgressBar percent={pct} />
				</div>
			{/each}
		</div>
	{/snippet}
</Story>
