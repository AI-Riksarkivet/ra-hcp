<script module>
	import { defineMeta } from '@storybook/addon-svelte-csf';
	import { fn } from 'storybook/test';
	import DeleteConfirmDialog from './delete-confirm-dialog.svelte';

	const { Story } = defineMeta({
		title: 'UI/DeleteConfirmDialog',
		component: DeleteConfirmDialog,
		tags: ['autodocs'],
		args: {
			open: true,
			name: 'production-data',
			itemType: 'namespace',
			loading: false,
			onconfirm: fn(),
		},
	});
</script>

<Story name="Default" />

<Story name="Loading" args={{ loading: true }} />

<Story name="User" args={{ name: 'john.doe', itemType: 'user' }} />

<Story name="Bucket" args={{ name: 'backup-2024', itemType: 'bucket' }} />
