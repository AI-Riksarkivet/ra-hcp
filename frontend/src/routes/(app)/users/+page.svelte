<script lang="ts">
	import { page } from '$app/state';
	import { Plus } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
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
	import { AVAILABLE_ROLES, type User, getUserRoles } from '$lib/constants.js';
	import PageHeader from '$lib/components/ui/page-header.svelte';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import NoTenantPlaceholder from '$lib/components/ui/no-tenant-placeholder.svelte';
	import {
		DataTable,
		createSvelteTable,
		getCoreRowModel,
		renderSnippet,
	} from '$lib/components/ui/data-table/index.js';
	import type { ColumnDef } from '@tanstack/table-core';

	type Group = { groupname?: string; name?: string; description?: string };

	let tenant = $derived(page.data.tenant as string | undefined);
	let usersData = $derived(tenant ? get_users({ tenant }) : undefined);
	let groupsData = $derived(tenant ? get_groups({ tenant }) : undefined);

	let users = $derived((usersData?.current ?? []) as User[]);
	let groups = $derived((groupsData?.current ?? []) as Group[]);

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

	// --- Groups TanStack Table ---
	const groupColumns: ColumnDef<Group>[] = [
		{
			accessorFn: (row) => row.groupname ?? row.name ?? '—',
			header: 'Group Name',
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			accessorFn: (row) => row.description || '—',
			header: 'Description',
			meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
		},
	];

	let groupsTable = $derived(
		createSvelteTable({
			get data() {
				return groups;
			},
			columns: groupColumns,
			getCoreRowModel: getCoreRowModel(),
		})
	);

	// --- Users TanStack Table ---
	let userColumns = $derived.by((): ColumnDef<User>[] => [
		{
			accessorKey: 'username',
			header: 'Username',
			cell: ({ row }) => renderSnippet(usernameCell, row.original),
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			accessorKey: 'fullName',
			header: 'Full Name',
			cell: ({ row }) => (row.original.fullName || '—') as string,
			meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'status',
			header: 'Status',
			cell: ({ row }) => renderSnippet(statusCell, row.original),
		},
		{
			id: 'roles',
			header: 'Roles',
			cell: ({ row }) => renderSnippet(rolesCell, row.original),
		},
		{
			id: 'namespaceAccess',
			header: 'Namespace Access',
			cell: ({ row }) => renderSnippet(nsAccessCell, row.original),
		},
	]);

	let usersTable = $derived(
		createSvelteTable({
			get data() {
				return users;
			},
			get columns() {
				return userColumns;
			},
			getCoreRowModel: getCoreRowModel(),
		})
	);

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

{#snippet usernameCell(user: User)}
	<a href="/users/{user.username}" class="text-primary underline-offset-4 hover:underline">
		{user.username}
	</a>
{/snippet}

{#snippet statusCell(user: User)}
	<Badge variant={user.enabled !== false ? 'default' : 'outline'}>
		{user.enabled !== false ? 'Active' : 'Disabled'}
	</Badge>
{/snippet}

{#snippet rolesCell(user: User)}
	{#each getUserRoles(user) as role (role)}
		<Badge variant="secondary" class="mr-1">{role}</Badge>
	{/each}
	{#if getUserRoles(user).length === 0}
		<span class="text-muted-foreground">—</span>
	{/if}
{/snippet}

{#snippet nsAccessCell(user: User)}
	{#if userNsAccess[user.username] === undefined}
		<div class="h-5 w-20 animate-pulse rounded bg-muted"></div>
	{:else if userNsAccess[user.username].length > 0}
		<div class="flex flex-wrap gap-1">
			{#each userNsAccess[user.username] as ns (ns)}
				<a href="/namespaces/{ns}">
					<Badge variant="outline" class="cursor-pointer hover:bg-accent">{ns}</Badge>
				</a>
			{/each}
		</div>
	{:else}
		<span class="text-muted-foreground">—</span>
	{/if}
{/snippet}

<svelte:head>
	<title>Users - HCP Admin Console</title>
</svelte:head>

<div class="space-y-8">
	<PageHeader title="Users & Groups" description="Manage user accounts and groups" />

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
			{:then}
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
				<DataTable table={usersTable} noResultsMessage="No user accounts found." />
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
			{:then}
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
				<DataTable table={groupsTable} noResultsMessage="No groups found." />
			{/await}
		</div>
	{:else}
		<NoTenantPlaceholder message="Log in with a tenant to manage users and groups." />
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
			<ErrorBanner message={createUserError} />
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
			<ErrorBanner message={createGroupError} />
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
							<Checkbox name="role-{role}" />
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
