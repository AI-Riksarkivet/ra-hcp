<script lang="ts">
	import EllipsisIcon from 'lucide-svelte/icons/ellipsis';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';

	let {
		objectKey,
		downloadUrl,
		ondelete,
		onshare,
		onview,
	}: {
		objectKey: string;
		downloadUrl: string;
		ondelete: () => void;
		onshare: () => void;
		onview: () => void;
	} = $props();
</script>

<DropdownMenu.Root>
	<DropdownMenu.Trigger>
		{#snippet child({ props })}
			<Button {...props} variant="ghost" size="icon" class="relative size-8 p-0">
				<span class="sr-only">Open menu</span>
				<EllipsisIcon class="size-4" />
			</Button>
		{/snippet}
	</DropdownMenu.Trigger>
	<DropdownMenu.Content align="end">
		<DropdownMenu.Group>
			<DropdownMenu.Label>Actions</DropdownMenu.Label>
			<DropdownMenu.Item onclick={() => navigator.clipboard.writeText(objectKey)}>
				Copy object key
			</DropdownMenu.Item>
		</DropdownMenu.Group>
		<DropdownMenu.Separator />
		<DropdownMenu.Item onclick={onview}>View details</DropdownMenu.Item>
		<DropdownMenu.Item>
			<a href={downloadUrl} download class="flex w-full">Download</a>
		</DropdownMenu.Item>
		<DropdownMenu.Item onclick={onshare}>Generate share link</DropdownMenu.Item>
		<DropdownMenu.Separator />
		<DropdownMenu.Item class="text-destructive" onclick={ondelete}>Delete object</DropdownMenu.Item>
	</DropdownMenu.Content>
</DropdownMenu.Root>
