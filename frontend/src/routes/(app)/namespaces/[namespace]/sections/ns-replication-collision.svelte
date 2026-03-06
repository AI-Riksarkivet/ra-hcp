<script lang="ts">
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_repl_collision,
		update_repl_collision,
		type ReplicationCollision,
	} from '$lib/namespaces.remote.js';

	let {
		tenant,
		namespaceName,
	}: {
		tenant: string;
		namespaceName: string;
	} = $props();

	let replData = $derived(get_repl_collision({ tenant, name: namespaceName }));
	let repl = $derived((replData?.current ?? {}) as ReplicationCollision);

	let syncVersion = $state(0);
	let localAction = $state('');
	let localDeleteEnabled = $state(false);
	let localDeleteDays = $state('0');

	$effect(() => {
		const r = repl;
		void syncVersion;
		localAction = r.action ?? '';
		localDeleteEnabled = r.deleteEnabled ?? false;
		localDeleteDays = String(r.deleteDays ?? 0);
	});

	let dirty = $derived(
		localAction !== (repl.action ?? '') ||
			localDeleteEnabled !== (repl.deleteEnabled ?? false) ||
			localDeleteDays !== String(repl.deleteDays ?? 0)
	);

	let saving = $state(false);

	async function save() {
		if (!replData) return;
		saving = true;
		try {
			await update_repl_collision({
				tenant,
				name: namespaceName,
				body: {
					action: localAction || undefined,
					deleteEnabled: localDeleteEnabled,
					deleteDays: parseInt(localDeleteDays, 10) || 0,
				},
			}).updates(replData);
			syncVersion++;
			toast.success('Replication collision settings updated');
		} catch {
			toast.error('Failed to update replication collision settings');
		} finally {
			saving = false;
		}
	}
</script>

<Card.Root class="flex h-full flex-col">
	<Card.Header>
		<Card.Title>Replication Collision</Card.Title>
		<Card.Description>
			How the system handles conflicts from simultaneous writes to replicated data.
		</Card.Description>
	</Card.Header>
	{#await replData}
		<Card.Content class="flex-1">
			<div class="flex flex-wrap gap-6">
				{#each Array(3) as _, i (i)}
					<div class="h-5 w-28 animate-pulse rounded bg-muted"></div>
				{/each}
			</div>
		</Card.Content>
	{:then}
		<Card.Content class="flex-1 space-y-4">
			<div class="space-y-1.5">
				<Label>Collision Action</Label>
				<Select.Root type="single" bind:value={localAction}>
					<Select.Trigger class="w-full">
						{localAction || 'Select...'}
					</Select.Trigger>
					<Select.Content>
						<Select.Item value="MOVE">MOVE</Select.Item>
						<Select.Item value="RENAME">RENAME</Select.Item>
					</Select.Content>
				</Select.Root>
				<p class="text-xs text-muted-foreground">
					Move to .lost+found or rename with .collision suffix.
				</p>
			</div>
			<div class="flex items-center gap-2">
				<Switch id="auto-delete-collisions" bind:checked={localDeleteEnabled} />
				<Label for="auto-delete-collisions" class="text-sm">Auto-delete collisions</Label>
			</div>
			{#if localDeleteEnabled}
				<div class="space-y-1.5">
					<Label for="delete-days">Delete After (days)</Label>
					<Input id="delete-days" type="number" min="0" bind:value={localDeleteDays} />
					<p class="text-xs text-muted-foreground">0 = delete immediately, max 36,500.</p>
				</div>
			{/if}
		</Card.Content>
		<Card.Footer>
			<SaveButton {dirty} {saving} onclick={save} />
		</Card.Footer>
	{/await}
</Card.Root>
