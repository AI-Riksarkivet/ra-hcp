<script lang="ts">
	import { page } from '$app/state';
	import { Plus } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { toast } from 'svelte-sonner';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import {
		get_users,
		get_groups,
		get_user_permissions,
		create_user,
		create_group,
		type DataAccessPermissions,
	} from '$lib/users.remote.js';

	type User = {
		username: string;
		fullName?: string;
		enabled?: boolean;
		roles?: { role?: string[] } | string[];
	};
	type Group = { groupname?: string; name?: string; description?: string };

	const AVAILABLE_ROLES = ['ADMINISTRATOR', 'SECURITY', 'MONITOR', 'COMPLIANCE'] as const;

	let tenant = $derived(page.data.tenant as string | undefined);
	let usersData = $derived(tenant ? get_users({ tenant }) : undefined);
	let groupsData = $derived(tenant ? get_groups({ tenant }) : undefined);

	let users = $derived((usersData?.current ?? []) as User[]);
	let groups = $derived((groupsData?.current ?? []) as Group[]);

	function getUserRoles(user: User): string[] {
		if (!user.roles) return [];
		if (Array.isArray(user.roles)) return user.roles;
		return user.roles.role ?? [];
	}

	// --- Namespace access per user (async derived — auto-cancels on dependency change) ---
	async function loadUserNsAccess(
		t: string | undefined,
		u: User[]
	): Promise<Record<string, string[]>> {
		if (!t || u.length === 0) return {};
		const results = await Promise.all(
			u.map(async (user) => {
				try {
					const perms = (await get_user_permissions({
						tenant: t,
						username: user.username,
					})) as DataAccessPermissions;
					const namespaces = (perms.namespacePermission ?? [])
						.filter(
							(entry) => entry.permissions?.permission && entry.permissions.permission.length > 0
						)
						.map((entry) => entry.namespaceName);
					return { username: user.username, namespaces };
				} catch {
					return { username: user.username, namespaces: [] as string[] };
				}
			})
		);
		const map: Record<string, string[]> = {};
		for (const r of results) map[r.username] = r.namespaces;
		return map;
	}

	let userNsAccess = $derived(await loadUserNsAccess(tenant, users));

	// --- Create User dialog ---
	let createUserOpen = $state(false);
	let createUserError = $state('');
	let creatingUser = $state(false);

	async function handleCreateUser(e: SubmitEvent) {
		e.preventDefault();
		if (!tenant || !usersData) return;
		const form = e.currentTarget as HTMLFormElement;
		const fd = new FormData(form);
		const username = fd.get('username') as string;
		if (!username) return;
		creatingUser = true;
		createUserError = '';
		try {
			const fullName = (fd.get('fullName') as string) || undefined;
			const description = (fd.get('description') as string) || undefined;
			const enabled = fd.has('enabled');
			const roles = AVAILABLE_ROLES.filter((r) => fd.has(`role-${r}`));
			await create_user({ tenant, username, fullName, description, enabled, roles }).updates(
				usersData
			);
			toast.success(`User "${username}" created`);
			createUserOpen = false;
			form.reset();
		} catch (err) {
			createUserError = err instanceof Error ? err.message : 'Failed to create user';
		} finally {
			creatingUser = false;
		}
	}

	// --- Create Group dialog ---
	let createGroupOpen = $state(false);
	let createGroupError = $state('');
	let creatingGroup = $state(false);

	async function handleCreateGroup(e: SubmitEvent) {
		e.preventDefault();
		if (!tenant || !groupsData) return;
		const form = e.currentTarget as HTMLFormElement;
		const fd = new FormData(form);
		const groupname = fd.get('groupname') as string;
		if (!groupname) return;
		creatingGroup = true;
		createGroupError = '';
		try {
			const description = (fd.get('description') as string) || undefined;
			const roles = AVAILABLE_ROLES.filter((r) => fd.has(`role-${r}`));
			await create_group({ tenant, groupname, description, roles }).updates(groupsData);
			toast.success(`Group "${groupname}" created`);
			createGroupOpen = false;
			form.reset();
		} catch (err) {
			createGroupError = err instanceof Error ? err.message : 'Failed to create group';
		} finally {
			creatingGroup = false;
		}
	}
</script>

<svelte:head>
	<title>Users - HCP Admin Console</title>
</svelte:head>

<div class="space-y-8">
	<div>
		<h2 class="text-2xl font-bold">Users & Groups</h2>
		<p class="mt-1 text-sm text-muted-foreground">Manage user accounts and groups</p>
	</div>

	{#if tenant}
		<!-- User Accounts -->
		<div>
			{#await usersData}
				<div class="mb-4 flex items-center justify-between">
					<div class="flex items-center gap-3">
						<h3 class="text-lg font-semibold">User Accounts</h3>
					</div>
				</div>
				<TableSkeleton rows={5} columns={6} />
			{:then _}
				<div class="mb-4 flex items-center justify-between">
					<div class="flex items-center gap-3">
						<h3 class="text-lg font-semibold">User Accounts</h3>
						<Badge variant="secondary">{users.length}</Badge>
					</div>
					<Button size="sm" onclick={() => (createUserOpen = true)}>
						<Plus class="h-4 w-4" />
						Create User
					</Button>
				</div>
				<div class="overflow-x-auto rounded-lg border">
					<table class="w-full text-left text-sm">
						<thead
							class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground"
						>
							<tr>
								<th class="px-4 py-3 font-medium">Username</th>
								<th class="px-4 py-3 font-medium">Full Name</th>
								<th class="px-4 py-3 font-medium">Status</th>
								<th class="px-4 py-3 font-medium">Roles</th>
								<th class="px-4 py-3 font-medium">Namespace Access</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#if users.length === 0}
								<tr>
									<td colspan="5" class="px-4 py-8 text-center text-muted-foreground"
										>No user accounts found.</td
									>
								</tr>
							{:else}
								{#each users as user (user.username)}
									<tr class="bg-card transition-colors hover:bg-accent/50">
										<td class="px-4 py-3 font-medium">
											<a
												href="/users/{user.username}"
												class="text-primary underline-offset-4 hover:underline"
											>
												{user.username}
											</a>
										</td>
										<td class="px-4 py-3 text-muted-foreground">{user.fullName || '—'}</td>
										<td class="px-4 py-3">
											<Badge variant={user.enabled !== false ? 'default' : 'outline'}>
												{user.enabled !== false ? 'Active' : 'Disabled'}
											</Badge>
										</td>
										<td class="px-4 py-3">
											{#each getUserRoles(user) as role (role)}
												<Badge variant="secondary" class="mr-1">{role}</Badge>
											{/each}
											{#if getUserRoles(user).length === 0}
												<span class="text-muted-foreground">—</span>
											{/if}
										</td>
										<td class="px-4 py-3">
											{#if userNsAccess[user.username] === undefined}
												<div class="h-5 w-20 animate-pulse rounded bg-muted"></div>
											{:else if userNsAccess[user.username].length > 0}
												<div class="flex flex-wrap gap-1">
													{#each userNsAccess[user.username] as ns (ns)}
														<a href="/namespaces/{ns}">
															<Badge variant="outline" class="cursor-pointer hover:bg-accent"
																>{ns}</Badge
															>
														</a>
													{/each}
												</div>
											{:else}
												<span class="text-muted-foreground">—</span>
											{/if}
										</td>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			{/await}
		</div>

		<!-- Groups -->
		<div>
			{#await groupsData}
				<div class="mb-4 flex items-center justify-between">
					<div class="flex items-center gap-3">
						<h3 class="text-lg font-semibold">Groups</h3>
					</div>
				</div>
				<TableSkeleton rows={3} columns={2} />
			{:then _}
				<div class="mb-4 flex items-center justify-between">
					<div class="flex items-center gap-3">
						<h3 class="text-lg font-semibold">Groups</h3>
						<Badge variant="secondary">{groups.length}</Badge>
					</div>
					<Button size="sm" onclick={() => (createGroupOpen = true)}>
						<Plus class="h-4 w-4" />
						Create Group
					</Button>
				</div>
				<div class="overflow-x-auto rounded-lg border">
					<table class="w-full text-left text-sm">
						<thead
							class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground"
						>
							<tr>
								<th class="px-4 py-3 font-medium">Group Name</th>
								<th class="px-4 py-3 font-medium">Description</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#if groups.length === 0}
								<tr>
									<td colspan="2" class="px-4 py-8 text-center text-muted-foreground"
										>No groups found.</td
									>
								</tr>
							{:else}
								{#each groups as group (group.groupname ?? group.name ?? '')}
									<tr class="bg-card transition-colors hover:bg-accent/50">
										<td class="px-4 py-3 font-medium">{group.groupname ?? group.name ?? '—'}</td>
										<td class="px-4 py-3 text-muted-foreground">{group.description || '—'}</td>
									</tr>
								{/each}
							{/if}
						</tbody>
					</table>
				</div>
			{/await}
		</div>
	{:else}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to manage users and groups.</p>
		</div>
	{/if}
</div>

<!-- Create User Dialog -->
<Dialog.Root bind:open={createUserOpen}>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Create User</Dialog.Title>
			<Dialog.Description>Add a new user account to this tenant.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleCreateUser} class="space-y-4">
			{#if createUserError}
				<div
					class="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
				>
					{createUserError}
				</div>
			{/if}
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
							<input type="checkbox" name="role-{role}" class="h-4 w-4 rounded border-input" />
							{role}
						</label>
					{/each}
				</div>
			</div>
			<label class="flex items-center gap-2 text-sm">
				<input type="checkbox" name="enabled" checked class="h-4 w-4 rounded border-input" />
				Enabled
			</label>
			<Dialog.Footer>
				<Button variant="ghost" type="button" onclick={() => (createUserOpen = false)}
					>Cancel</Button
				>
				<Button type="submit" disabled={creatingUser}
					>{creatingUser ? 'Creating...' : 'Create'}</Button
				>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>

<!-- Create Group Dialog -->
<Dialog.Root bind:open={createGroupOpen}>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Create Group</Dialog.Title>
			<Dialog.Description>Add a new group to this tenant.</Dialog.Description>
		</Dialog.Header>
		<form onsubmit={handleCreateGroup} class="space-y-4">
			{#if createGroupError}
				<div
					class="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
				>
					{createGroupError}
				</div>
			{/if}
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
					{#each AVAILABLE_ROLES as role (role)}
						<label class="flex items-center gap-2 text-sm">
							<input type="checkbox" name="role-{role}" class="h-4 w-4 rounded border-input" />
							{role}
						</label>
					{/each}
				</div>
			</div>
			<Dialog.Footer>
				<Button variant="ghost" type="button" onclick={() => (createGroupOpen = false)}
					>Cancel</Button
				>
				<Button type="submit" disabled={creatingGroup}
					>{creatingGroup ? 'Creating...' : 'Create'}</Button
				>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
