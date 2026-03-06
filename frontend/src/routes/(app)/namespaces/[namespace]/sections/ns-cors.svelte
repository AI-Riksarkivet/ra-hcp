<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_ns_cors,
		set_ns_cors,
		delete_ns_cors,
		type CorsConfig,
	} from '$lib/namespaces.remote.js';

	let {
		tenant,
		namespaceName,
	}: {
		tenant: string;
		namespaceName: string;
	} = $props();

	let corsData = $derived(get_ns_cors({ tenant, name: namespaceName }));
	let cors = $derived((corsData?.current ?? {}) as CorsConfig);

	let syncVersion = $state(0);
	let localCorsXml = $state('');

	$effect(() => {
		const c = cors;
		void syncVersion;
		localCorsXml = c.cors ?? '';
	});

	let dirty = $derived(localCorsXml !== (cors.cors ?? ''));
	let saving = $state(false);
	let deleteOpen = $state(false);
	let deleting = $state(false);

	async function save() {
		if (!corsData) return;
		saving = true;
		try {
			await set_ns_cors({
				tenant,
				name: namespaceName,
				body: { cors: localCorsXml },
			}).updates(corsData);
			syncVersion++;
			toast.success('CORS configuration saved');
		} catch {
			toast.error('Failed to save CORS configuration');
		} finally {
			saving = false;
		}
	}

	async function handleDelete() {
		if (!corsData) return;
		deleting = true;
		try {
			await delete_ns_cors({ tenant, name: namespaceName }).updates(corsData);
			syncVersion++;
			deleteOpen = false;
			toast.success('CORS configuration deleted');
		} catch {
			toast.error('Failed to delete CORS configuration');
		} finally {
			deleting = false;
		}
	}
</script>

<Card.Root class="flex h-full flex-col">
	<Card.Header>
		<Card.Title>CORS Configuration</Card.Title>
		<Card.Description>
			Cross-Origin Resource Sharing rules controlling which external origins can access this
			namespace. Overrides the tenant-level CORS configuration.
		</Card.Description>
	</Card.Header>
	{#await corsData}
		<Card.Content class="flex-1">
			<div class="h-32 animate-pulse rounded bg-muted"></div>
		</Card.Content>
	{:then}
		<Card.Content class="flex-1 space-y-4">
			<div class="space-y-2">
				<Label for="cors-xml">CORS Rules (XML)</Label>
				<Textarea
					id="cors-xml"
					class="min-h-[120px] font-mono"
					placeholder="<CORSConfiguration>&#10;  <CORSRule>&#10;    <AllowedOrigin>*</AllowedOrigin>&#10;    <AllowedMethod>GET</AllowedMethod>&#10;  </CORSRule>&#10;</CORSConfiguration>"
					bind:value={localCorsXml}
				/>
				<p class="text-xs text-muted-foreground">
					Define allowed origins, methods, and headers using XML CORSRule elements.
				</p>
			</div>
		</Card.Content>
		<Card.Footer class="gap-3">
			<SaveButton {dirty} {saving} onclick={save} />
			{#if cors.cors}
				<Button variant="destructive" size="sm" onclick={() => (deleteOpen = true)}>
					Delete CORS
				</Button>
			{/if}
		</Card.Footer>
	{/await}
</Card.Root>

<DeleteConfirmDialog
	bind:open={deleteOpen}
	name="CORS configuration"
	itemType="CORS configuration"
	loading={deleting}
	onconfirm={handleDelete}
/>
