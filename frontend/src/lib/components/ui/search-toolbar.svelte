<script lang="ts">
	import { Search, Trash2 } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';

	let {
		search = $bindable(''),
		placeholder = 'Search...',
		selectedCount = 0,
		ondeleteselected,
		ondeselectall,
	}: {
		search: string;
		placeholder?: string;
		selectedCount?: number;
		ondeleteselected?: () => void;
		ondeselectall?: () => void;
	} = $props();
</script>

<div class="space-y-4">
	<div class="relative">
		<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
		<Input type="text" bind:value={search} {placeholder} class="pl-10" />
	</div>

	{#if selectedCount > 0}
		<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
			<span class="text-sm font-medium">{selectedCount} selected</span>
			{#if ondeleteselected}
				<Button variant="destructive" size="sm" onclick={ondeleteselected}>
					<Trash2 class="h-3.5 w-3.5" />Delete Selected
				</Button>
			{/if}
			{#if ondeselectall}
				<Button variant="ghost" size="sm" onclick={ondeselectall}>Deselect All</Button>
			{/if}
		</div>
	{/if}
</div>
