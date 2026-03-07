<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { toast } from 'svelte-sonner';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
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

<Dialog.Root bind:open>
	<Dialog.Content class="sm:max-w-md">
		<Dialog.Header><Dialog.Title>Create Bucket</Dialog.Title></Dialog.Header>
		<form onsubmit={handleCreate} class="space-y-4">
			<ErrorBanner message={createError} />
			<div class="space-y-2">
				<Label for="bucket-name">Bucket Name</Label>
				<Input id="bucket-name" name="bucket" placeholder="my-bucket" required />
			</div>
			<Dialog.Footer>
				<Button variant="ghost" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
