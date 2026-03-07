<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { toast } from 'svelte-sonner';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import { get_users, create_user } from '$lib/users.remote.js';
	import { AVAILABLE_ROLES } from '$lib/constants.js';

	let {
		tenant,
		open = $bindable(false),
	}: {
		tenant: string;
		open: boolean;
	} = $props();

	let usersData = $derived(get_users({ tenant }));
	let createError = $state('');
	let creating = $state(false);

	async function handleCreateUser(e: SubmitEvent) {
		e.preventDefault();
		if (!usersData) return;
		const form = e.currentTarget as HTMLFormElement;
		const fd = new FormData(form);
		const username = fd.get('username') as string;
		if (!username) return;
		creating = true;
		createError = '';
		try {
			const fullName = (fd.get('fullName') as string) || undefined;
			const description = (fd.get('description') as string) || undefined;
			const enabled = fd.has('enabled');
			const roles = AVAILABLE_ROLES.filter((r) => fd.has(`role-${r}`));
			await create_user({ tenant, username, fullName, description, enabled, roles }).updates(
				usersData
			);
			toast.success(`User "${username}" created`);
			open = false;
			form.reset();
		} catch (err) {
			createError = err instanceof Error ? err.message : 'Failed to create user';
		} finally {
			creating = false;
		}
	}
</script>

<Dialog.Root bind:open>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Create User</Dialog.Title>
			<Dialog.Description>Add a new user account to this tenant.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleCreateUser} class="space-y-4">
			<ErrorBanner message={createError} />
			<div class="space-y-2">
				<Label for="cu-username">Username</Label>
				<Input id="cu-username" name="username" placeholder="jdoe" required />
			</div>
			<div class="space-y-2">
				<Label for="cu-fullname">Full Name</Label>
				<Input id="cu-fullname" name="fullName" placeholder="Jane Doe" />
			</div>
			<div class="space-y-2">
				<Label for="cu-desc">Description</Label>
				<Input id="cu-desc" name="description" placeholder="Optional description" />
			</div>
			<div class="space-y-2">
				<Label>Roles</Label>
				<div class="flex flex-wrap gap-4">
					{#each AVAILABLE_ROLES as role (role)}
						<label class="flex items-center gap-2 text-sm">
							<Checkbox name="role-{role}" />
							{role}
						</label>
					{/each}
				</div>
			</div>
			<label class="flex items-center gap-2 text-sm">
				<Checkbox name="enabled" checked />
				Enabled
			</label>
			<Dialog.Footer>
				<Button variant="ghost" type="button" onclick={() => (open = false)}>Cancel</Button>
				<Button type="submit" disabled={creating}>{creating ? 'Creating...' : 'Create'}</Button>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
