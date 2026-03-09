<script lang="ts">
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { toast } from 'svelte-sonner';
	import FormDialog from '$lib/components/ui/form-dialog.svelte';
	import { get_buckets, create_bucket } from '$lib/buckets.remote.js';

	let {
		open = $bindable(false),
	}: {
		open: boolean;
	} = $props();

	let bucketData = get_buckets();
	let createError = $state('');
	let creating = $state(false);

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		const form = e.currentTarget as HTMLFormElement;
		const formData = new FormData(form);
		const name = formData.get('bucket') as string;
		if (!name) return;
		creating = true;
		createError = '';
		try {
			await create_bucket({ bucket: name }).updates(bucketData);
			toast.success('Bucket created successfully');
			open = false;
			form.reset();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create bucket';
		} finally {
			creating = false;
		}
	}
</script>

<FormDialog
	bind:open
	title="Create Bucket"
	loading={creating}
	error={createError}
	onsubmit={handleCreate}
	class="sm:max-w-md"
>
	<div class="space-y-2">
		<Label for="bucket-name">Bucket Name</Label>
		<Input id="bucket-name" name="bucket" placeholder="my-bucket" required />
	</div>
</FormDialog>
