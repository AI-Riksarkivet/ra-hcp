<script lang="ts">
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import { Button } from '$lib/components/ui/button/index.js';

	let {
		open = $bindable(false),
		count,
		itemType,
		loading = false,
		onconfirm,
	}: {
		open: boolean;
		count: number;
		itemType: string;
		loading?: boolean;
		onconfirm: () => void;
	} = $props();

	let plural = $derived(count !== 1 ? 's' : '');
</script>

<AlertDialog.Root bind:open>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete {count} {itemType}{plural}</AlertDialog.Title>
			<AlertDialog.Description>
				Are you sure you want to delete {count}
				{itemType}{plural}? This action cannot be undone.
			</AlertDialog.Description>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel disabled={loading}>Cancel</AlertDialog.Cancel>
			<Button variant="destructive" onclick={onconfirm} disabled={loading}>
				{loading ? 'Deleting...' : `Delete ${count} ${itemType}${plural}`}
			</Button>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
