<script lang="ts">
	import { X } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { toast } from 'svelte-sonner';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import ServiceTagBadge from '$lib/components/ui/service-tag-badge.svelte';
	import { get_namespaces, create_namespace } from '$lib/namespaces.remote.js';

	let {
		tenant,
		open = $bindable(false),
	}: {
		tenant: string;
		open: boolean;
	} = $props();

	let nsData = $derived(get_namespaces({ tenant }));

	let createError = $state('');
	let creating = $state(false);
	let createHashScheme = $state('SHA-256');
	let createTags = $state<string[]>([]);
	let tagInput = $state('');

	function addTag() {
		const t = tagInput.trim();
		if (t && !createTags.includes(t.toLowerCase())) {
			createTags = [...createTags, t.toLowerCase()];
		}
		tagInput = '';
	}

	function removeTag(t: string) {
		createTags = createTags.filter((x) => x !== t);
	}

	function handleTagKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addTag();
		}
	}

	async function handleCreate(e: SubmitEvent) {
		e.preventDefault();
		if (!nsData) return;
		const form = e.currentTarget as HTMLFormElement;
		const formData = new FormData(form);
		const name = formData.get('namespace') as string;
		if (!name) return;
		creating = true;
		createError = '';
		try {
			const description = (formData.get('description') as string) || undefined;
			const hardQuota = (formData.get('hardQuota') as string) || undefined;
			const softQuotaStr = formData.get('softQuota') as string;
			const softQuota = softQuotaStr ? Number(softQuotaStr) : undefined;
			const hashScheme = (formData.get('hashScheme') as string) || undefined;
			const searchEnabled = formData.has('searchEnabled');
			const versioningEnabled = formData.has('versioningEnabled');
			await create_namespace({
				tenant,
				name,
				description,
				hardQuota,
				softQuota,
				hashScheme,
				searchEnabled,
				versioningEnabled,
				tags: createTags.length > 0 ? createTags : undefined,
			}).updates(nsData);
			toast.success('Namespace created successfully');
			open = false;
			createTags = [];
			form.reset();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create namespace';
		} finally {
			creating = false;
		}
	}
</script>

<Dialog.Root bind:open>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Create Namespace</Dialog.Title>
			<Dialog.Description>Configure a new namespace for this tenant.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleCreate} class="space-y-4">
			<ErrorBanner message={createError} />
			<div class="space-y-2">
				<Label for="ns-name">Namespace Name</Label>
				<Input id="ns-name" name="namespace" placeholder="my-namespace" required />
			</div>
			<div class="space-y-2">
				<Label for="ns-desc">Description</Label>
				<Input id="ns-desc" name="description" placeholder="Optional description" />
			</div>
			<div class="grid grid-cols-2 gap-4">
				<div class="space-y-2">
					<Label for="ns-hard-quota">Hard Quota</Label>
					<Input id="ns-hard-quota" name="hardQuota" placeholder="e.g. 50 GB" />
				</div>
				<div class="space-y-2">
					<Label for="ns-soft-quota">Soft Quota (%)</Label>
					<Input
						id="ns-soft-quota"
						name="softQuota"
						type="number"
						min="10"
						max="95"
						placeholder="85"
					/>
				</div>
			</div>
			<div class="space-y-2">
				<Label for="ns-hash">Hash Scheme</Label>
				<select
					id="ns-hash"
					class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-9 w-full items-center rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
					bind:value={createHashScheme}
				>
					<option value="SHA-256">SHA-256</option>
					<option value="SHA-512">SHA-512</option>
					<option value="SHA-384">SHA-384</option>
					<option value="SHA-1">SHA-1</option>
					<option value="MD5">MD5</option>
				</select>
				<input type="hidden" name="hashScheme" value={createHashScheme} />
			</div>
			<div class="space-y-2">
				<Label for="ns-tags">Tags</Label>
				<div class="flex gap-2">
					<Input
						id="ns-tags"
						placeholder="e.g. lakefs, nfs, s3"
						bind:value={tagInput}
						onkeydown={handleTagKeydown}
					/>
					<Button type="button" variant="secondary" size="sm" onclick={addTag}>Add</Button>
				</div>
				{#if createTags.length > 0}
					<div class="flex flex-wrap gap-1 pt-1">
						{#each createTags as t (t)}
							<ServiceTagBadge tag={t} />
							<button
								type="button"
								class="-ml-1 mr-1 rounded-full p-0.5 text-muted-foreground hover:bg-destructive/10 hover:text-destructive"
								onclick={() => removeTag(t)}
							>
								<X class="h-3 w-3" />
							</button>
						{/each}
					</div>
				{/if}
			</div>
			<div class="flex gap-6">
				<div class="flex items-center gap-2">
					<Checkbox id="ns-search" name="searchEnabled" />
					<Label for="ns-search">Enable Search</Label>
				</div>
				<div class="flex items-center gap-2">
					<Checkbox id="ns-versioning" name="versioningEnabled" />
					<Label for="ns-versioning">Enable Versioning</Label>
				</div>
			</div>
			<Dialog.Footer>
				<Button variant="ghost" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
