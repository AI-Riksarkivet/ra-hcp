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
		oncopy,
	}: {
		objectKey: string;
		downloadUrl: string;
		ondelete: () => void;
		onshare: () => void;
		onview: () => void;
		oncopy: () => void;
	} = $props();

	function handleDownload(e: MouseEvent) {
		e.preventDefault();
		const a = document.createElement('a');
		a.href = downloadUrl;
		a.download = objectKey.split('/').pop() ?? objectKey;
		a.style.display = 'none';
		document.body.appendChild(a);
		a.click();
		document.body.removeChild(a);
	}
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
		<DropdownMenu.Item onclick={handleDownload}>Download</DropdownMenu.Item>
		<DropdownMenu.Item onclick={onshare}>Generate share link</DropdownMenu.Item>
		<DropdownMenu.Item onclick={oncopy}>Copy to...</DropdownMenu.Item>
		<DropdownMenu.Separator />
		<DropdownMenu.Item class="text-destructive" onclick={ondelete}>Delete object</DropdownMenu.Item>
	</DropdownMenu.Content>
</DropdownMenu.Root>
