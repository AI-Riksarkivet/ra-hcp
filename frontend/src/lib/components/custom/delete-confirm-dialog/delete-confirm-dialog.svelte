<script lang="ts">
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import { Button } from '$lib/components/ui/button/index.js';

	let {
		open = $bindable(false),
		name,
		itemType,
		description,
		loading = false,
		onconfirm,
	}: {
		open: boolean;
		name: string;
		itemType: string;
		description?: string;
		loading?: boolean;
		onconfirm: () => void;
	} = $props();
</script>

<AlertDialog.Root bind:open>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete {itemType}</AlertDialog.Title>
			<AlertDialog.Description>
				{#if description}
					{description}
				{:else}
					Are you sure you want to delete {itemType} "<strong>{name}</strong>"? This action cannot
					be undone.
				{/if}
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel disabled={loading}>Cancel</AlertDialog.Cancel>
			<Button variant="destructive" onclick={onconfirm} disabled={loading}>
				{loading ? 'Deleting...' : 'Delete'}
			</Button>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
