<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_tenant_cors,
		set_tenant_cors,
		delete_tenant_cors,
		type TenantCors,
	} from '$lib/tenant-info.remote.js';

	let {
		tenant,
	}: {
		tenant: string;
	} = $props();

	let corsData = $derived(get_tenant_cors({ tenant }));
	let cors = $derived((corsData?.current ?? {}) as TenantCors);

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
			await set_tenant_cors({
				tenant,
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
			await delete_tenant_cors({ tenant }).updates(corsData);
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

{#await corsData}
	<CardSkeleton />
{:then}
	<Card.Root>
		<Card.Header>
			<Card.Title>CORS Configuration</Card.Title>
			<Card.Description>
				Tenant-wide Cross-Origin Resource Sharing rules for browser-based S3 access. Namespace-level
				CORS overrides these defaults.
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-4">
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
	</Card.Root>
{/await}

<DeleteConfirmDialog
	bind:open={deleteOpen}
	name="CORS configuration"
	itemType="CORS configuration"
	loading={deleting}
	onconfirm={handleDelete}
/>
