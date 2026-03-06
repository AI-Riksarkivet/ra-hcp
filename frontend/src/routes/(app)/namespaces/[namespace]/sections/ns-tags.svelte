<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Pencil, X } from 'lucide-svelte';
	import ServiceTagBadge from '$lib/components/ui/service-tag-badge.svelte';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import { toast } from 'svelte-sonner';
	import { get_namespace, update_namespace, type Namespace } from '$lib/namespaces.remote.js';

	let {
		tenant,
		namespaceName,
	}: {
		tenant: string;
		namespaceName: string;
	} = $props();

	let nsData = $derived(get_namespace({ tenant, name: namespaceName }));
	let ns = $derived((nsData?.current ?? null) as Namespace | null);

	let editingTags = $state(false);
	let editTags = $state<string[]>([]);
	let editTagInput = $state('');
	let savingTags = $state(false);

	function startEditTags() {
		editTags = [...(ns?.tags?.tag ?? [])];
		editTagInput = '';
		editingTags = true;
	}

	function addEditTag() {
		const t = editTagInput.trim().toLowerCase();
		if (t && !editTags.includes(t)) {
			editTags = [...editTags, t];
		}
		editTagInput = '';
	}

	function removeEditTag(t: string) {
		editTags = editTags.filter((x) => x !== t);
	}

	function handleEditTagKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addEditTag();
		}
	}

	async function saveTags() {
		if (!nsData) return;
		savingTags = true;
		try {
			await update_namespace({
				tenant,
				name: namespaceName,
				body: { tags: { tag: editTags } },
			}).updates(nsData);
			toast.success('Tags updated');
			editingTags = false;
		} catch {
			toast.error('Failed to update tags');
		} finally {
			savingTags = false;
		}
	}
</script>

<Card.Root class="flex h-full flex-col">
	<Card.Header class="pb-3">
		<Card.Title class="text-base">Tags</Card.Title>
		<Card.Description>Classify and organize namespaces with custom labels.</Card.Description>
		{#if !editingTags}
			<Card.Action>
				<Button variant="ghost" size="icon" class="h-6 w-6" onclick={startEditTags}>
					<Pencil class="h-3.5 w-3.5" />
				</Button>
			</Card.Action>
		{/if}
	</Card.Header>
	<Card.Content>
		{#if editingTags}
			<div class="space-y-3">
				<div class="flex gap-2">
					<Input
						class="h-8"
						placeholder="Add tag..."
						bind:value={editTagInput}
						onkeydown={handleEditTagKeydown}
					/>
					<Button variant="secondary" size="sm" class="h-8" onclick={addEditTag}>Add</Button>
				</div>
				{#if editTags.length > 0}
					<div class="flex flex-wrap gap-1.5">
						{#each editTags as t (t)}
							<span class="inline-flex items-center gap-0.5">
								<ServiceTagBadge tag={t} />
								<button
									type="button"
									class="rounded-full p-0.5 text-muted-foreground hover:text-destructive"
									onclick={() => removeEditTag(t)}
								>
									<X class="h-2.5 w-2.5" />
								</button>
							</span>
						{/each}
					</div>
				{:else}
					<p class="text-sm text-muted-foreground">No tags yet</p>
				{/if}
			</div>
		{:else if ns?.tags?.tag?.length}
			<div class="flex flex-wrap gap-1.5">
				{#each ns.tags.tag as t (t)}
					<ServiceTagBadge tag={t} />
				{/each}
			</div>
		{:else}
			<p class="text-sm text-muted-foreground">No tags</p>
		{/if}
	</Card.Content>
	{#if editingTags}
		<Card.Footer class="gap-3">
			<SaveButton dirty={true} saving={savingTags} onclick={saveTags} />
			<Button variant="ghost" size="sm" onclick={() => (editingTags = false)}>Cancel</Button>
		</Card.Footer>
	{/if}
</Card.Root>
