<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Textarea } from '$lib/components/ui/textarea/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import { toast } from 'svelte-sonner';
	import type { Snippet } from 'svelte';

	let {
		corsXml,
		loading = false,
		title = 'CORS Configuration',
		description = '',
		onsave,
		ondelete,
		skeleton,
	}: {
		corsXml: string;
		loading?: boolean;
		title?: string;
		description?: string;
		onsave: (xml: string) => Promise<void>;
		ondelete?: () => Promise<void>;
		skeleton?: Snippet;
	} = $props();

	let syncVersion = $state(0);
	let localCorsXml = $state('');

	$effect(() => {
		void corsXml;
		void syncVersion;
		localCorsXml = corsXml ?? '';
	});

	let dirty = $derived(localCorsXml !== (corsXml ?? ''));
	let saving = $state(false);
	let deleteOpen = $state(false);
	let deleting = $state(false);

	async function save() {
		saving = true;
		try {
			await onsave(localCorsXml);
			syncVersion++;
			toast.success('CORS configuration saved');
		} catch {
			toast.error('Failed to save CORS configuration');
		} finally {
			saving = false;
		}
	}

	async function handleDelete() {
		if (!ondelete) return;
		deleting = true;
		try {
			await ondelete();
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
		<Card.Title>{title}</Card.Title>
		{#if description}
			<Card.Description>{description}</Card.Description>
		{/if}
	</Card.Header>
	{#if loading}
		{#if skeleton}
			{@render skeleton()}
		{:else}
			<Card.Content class="flex-1">
				<div class="h-32 animate-pulse rounded bg-muted"></div>
			</Card.Content>
		{/if}
	{:else}
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
			{#if ondelete && corsXml}
				<Button variant="destructive" size="sm" onclick={() => (deleteOpen = true)}>
					Delete CORS
				</Button>
			{/if}
		</Card.Footer>
	{/if}
</Card.Root>

<DeleteConfirmDialog
	bind:open={deleteOpen}
	name="CORS configuration"
	itemType="CORS configuration"
	loading={deleting}
	onconfirm={handleDelete}
/>
