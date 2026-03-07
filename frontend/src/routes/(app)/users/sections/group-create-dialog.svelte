<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { toast } from 'svelte-sonner';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import { get_groups, create_group } from '$lib/users.remote.js';
	import { GROUP_ROLES } from '$lib/constants.js';

	let {
		tenant,
		open = $bindable(false),
	}: {
		tenant: string;
		open: boolean;
	} = $props();

	let groupsData = $derived(get_groups({ tenant }));
	let createError = $state('');
	let creating = $state(false);

	async function handleCreateGroup(e: SubmitEvent) {
		e.preventDefault();
		if (!groupsData) return;
		const form = e.currentTarget as HTMLFormElement;
		const fd = new FormData(form);
		const groupname = fd.get('groupname') as string;
		if (!groupname) return;
		creating = true;
		createError = '';
		try {
			const description = (fd.get('description') as string) || undefined;
			const roles = GROUP_ROLES.filter((r) => fd.has(`role-${r}`));
			await create_group({ tenant, groupname, description, roles }).updates(groupsData);
			toast.success(`Group "${groupname}" created`);
			open = false;
			form.reset();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create group';
		} finally {
			creating = false;
		}
	}
</script>

<Dialog.Root bind:open>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Create Group</Dialog.Title>
			<Dialog.Description>Add a new group to this tenant.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleCreateGroup} class="space-y-4">
			<ErrorBanner message={createError} />
			<div class="space-y-2">
				<Label for="cg-name">Group Name</Label>
				<Input id="cg-name" name="groupname" placeholder="my-group" required />
			</div>
			<div class="space-y-2">
				<Label for="cg-desc">Description</Label>
				<Input id="cg-desc" name="description" placeholder="Optional description" />
			</div>
			<div class="space-y-2">
				<Label>Roles</Label>
				<div class="flex flex-wrap gap-4">
					{#each GROUP_ROLES as role (role)}
						<label class="flex items-center gap-2 text-sm">
							<Checkbox name="role-{role}" />
							{role}
						</label>
					{/each}
				</div>
			</div>
			<Dialog.Footer>
				<Button variant="ghost" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
