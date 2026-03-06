<script lang="ts">
	import { page } from '$app/state';
	import { Plus, Search, Copy, Users, UsersRound } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
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
	import {
		AVAILABLE_ROLES,
		GROUP_ROLES,
		type User,
		type GroupAccount,
		getUserRoles,
		getGroupName,
		getGroupRoles,
	} from '$lib/constants.js';
	import PageHeader from '$lib/components/ui/page-header.svelte';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import NoTenantPlaceholder from '$lib/components/ui/no-tenant-placeholder.svelte';
	import {
		DataTable,
		DataTableHeaderButton,
		createSvelteTable,
		getCoreRowModel,
		getSortedRowModel,
		getPaginationRowModel,
		renderSnippet,
		renderComponent,
	} from '$lib/components/ui/data-table/index.js';
	import type { ColumnDef, SortingState, PaginationState } from '@tanstack/table-core';
	import { SvelteMap } from 'svelte/reactivity';

	let tenant = $derived(page.data.tenant as string | undefined);
	let usersData = $derived(tenant ? get_users({ tenant }) : undefined);
	let groupsData = $derived(tenant ? get_groups({ tenant }) : undefined);

	let users = $derived((usersData?.current ?? []) as User[]);
	let groups = $derived((groupsData?.current ?? []) as GroupAccount[]);

	let activeTab = $state('users');

	// --- Namespace access per user (reactive queries) ---
	let userPermsMap = $derived.by(() => {
		const map = new SvelteMap<string, ReturnType<typeof get_user_permissions>>();
		if (!tenant) return map;
		for (const u of users) {
			map.set(u.username, get_user_permissions({ tenant, username: u.username }));
		}
		return map;
	});

	function getUserNamespaces(username: string): string[] | undefined {
		const query = userPermsMap.get(username);
		if (!query?.current) return undefined;
		const perms = query.current as DataAccessPermissions;
		return (perms.namespacePermission ?? [])
			.filter((entry) => entry.permissions?.permission && entry.permissions.permission.length > 0)
			.map((entry) => entry.namespaceName);
	}

	// --- Search + filtered users ---
	let userSearch = $state('');
	let filteredUsers = $derived(
		users.filter((u) => {
			const q = userSearch.toLowerCase();
			if (!q) return true;
			return u.username.toLowerCase().includes(q) || (u.fullName ?? '').toLowerCase().includes(q);
		})
	);

	// --- TanStack state for users table ---
	let userSorting = $state<SortingState>([]);
	let userPagination = $state<PaginationState>({ pageIndex: 0, pageSize: 25 });

	// --- TanStack state for groups table ---
	let groupSorting = $state<SortingState>([]);
	let groupPagination = $state<PaginationState>({ pageIndex: 0, pageSize: 25 });

	// --- Groups TanStack Table ---
	let groupColumns = $derived.by((): ColumnDef<GroupAccount>[] => [
		{
			id: 'groupName',
			accessorFn: (row) => getGroupName(row),
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Group Name',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => renderSnippet(groupNameCell, row.original),
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			id: 'description',
			accessorFn: (row) => row.description || '—',
			header: 'Description',
			meta: { cellClass: 'px-4 py-3 text-muted-foreground' },
		},
		{
			id: 'roles',
			header: 'Roles',
			cell: ({ row }) => renderSnippet(groupRolesCell, row.original),
			meta: { cellClass: 'px-4 py-3' },
		},
	]);

	let groupsTable = $derived(
		createSvelteTable({
			get data() {
				return groups;
			},
			get columns() {
				return groupColumns;
			},
			state: {
				get sorting() {
					return groupSorting;
				},
				get pagination() {
					return groupPagination;
				},
			},
			onSortingChange: (updater) => {
				groupSorting = typeof updater === 'function' ? updater(groupSorting) : updater;
			},
			onPaginationChange: (updater) => {
				groupPagination = typeof updater === 'function' ? updater(groupPagination) : updater;
			},
			getCoreRowModel: getCoreRowModel(),
			getSortedRowModel: getSortedRowModel(),
			getPaginationRowModel: getPaginationRowModel(),
		})
	);

	// --- Users TanStack Table ---
	let userColumns = $derived.by((): ColumnDef<User>[] => [
		{
			accessorKey: 'username',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Username',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => renderSnippet(usernameCell, row.original),
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			id: 'canonicalId',
			header: 'Canonical ID',
			cell: ({ row }) => renderSnippet(canonicalIdCell, row.original),
			meta: { cellClass: 'px-4 py-3' },
		},
		{
			accessorKey: 'fullName',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Full Name',
					onclick: column.getToggleSortingHandler(),
				}),
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
				return filteredUsers;
			},
			get columns() {
				return userColumns;
			},
			state: {
				get sorting() {
					return userSorting;
				},
				get pagination() {
					return userPagination;
				},
			},
			onSortingChange: (updater) => {
				userSorting = typeof updater === 'function' ? updater(userSorting) : updater;
			},
			onPaginationChange: (updater) => {
				userPagination = typeof updater === 'function' ? updater(userPagination) : updater;
			},
			getCoreRowModel: getCoreRowModel(),
			getSortedRowModel: getSortedRowModel(),
			getPaginationRowModel: getPaginationRowModel(),
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
			const roles = GROUP_ROLES.filter((r) => fd.has(`role-${r}`));
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
	{@const namespaces = getUserNamespaces(user.username)}
	{#if namespaces === undefined}
		<div class="h-5 w-20 animate-pulse rounded bg-muted"></div>
	{:else if namespaces.length > 0}
		<div class="flex flex-wrap gap-1">
			{#each namespaces as ns (ns)}
				<a href="/namespaces/{ns}">
					<Badge variant="outline" class="cursor-pointer hover:bg-accent">{ns}</Badge>
				</a>
			{/each}
		</div>
	{:else}
		<span class="text-muted-foreground">—</span>
	{/if}
{/snippet}

{#snippet canonicalIdCell(user: User)}
	{#if user.userGUID}
		<span class="flex items-center gap-1 font-mono text-xs text-muted-foreground">
			<span class="max-w-[120px] truncate">{user.userGUID}</span>
			<button
				class="shrink-0 rounded p-0.5 hover:bg-muted"
				title="Copy canonical ID"
				onclick={async (e) => {
					e.stopPropagation();
					e.preventDefault();
					try {
						await navigator.clipboard.writeText(user.userGUID!);
						toast.success('Canonical ID copied');
					} catch {
						const ta = document.createElement('textarea');
						ta.value = user.userGUID!;
						ta.style.position = 'fixed';
						ta.style.opacity = '0';
						document.body.appendChild(ta);
						ta.select();
						document.execCommand('copy');
						document.body.removeChild(ta);
						toast.success('Canonical ID copied');
					}
				}}
			>
				<Copy class="h-3 w-3" />
			</button>
		</span>
	{:else}
		<span class="text-muted-foreground">—</span>
	{/if}
{/snippet}

{#snippet groupNameCell(group: GroupAccount)}
	<a
		href="/users/groups/{getGroupName(group)}"
		class="text-primary underline-offset-4 hover:underline"
	>
		{getGroupName(group)}
	</a>
{/snippet}

{#snippet groupRolesCell(group: GroupAccount)}
	{#each getGroupRoles(group) as role (role)}
		<Badge variant="secondary" class="mr-1">{role}</Badge>
	{/each}
	{#if getGroupRoles(group).length === 0}
		<span class="text-muted-foreground">—</span>
	{/if}
{/snippet}

<svelte:head>
	<title>Users & Groups - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<PageHeader title="Users & Groups" description="Manage user accounts and groups" />

	{#if tenant}
		<Tabs.Root bind:value={activeTab}>
			<Tabs.List>
				<Tabs.Trigger value="users">
					<Users class="mr-1.5 h-4 w-4" />
					Users
					{#if users.length > 0}
						<Badge variant="secondary" class="ml-1.5">{users.length}</Badge>
					{/if}
				</Tabs.Trigger>
				<Tabs.Trigger value="groups">
					<UsersRound class="mr-1.5 h-4 w-4" />
					Groups
					{#if groups.length > 0}
						<Badge variant="secondary" class="ml-1.5">{groups.length}</Badge>
					{/if}
				</Tabs.Trigger>
			</Tabs.List>

			<Tabs.Content value="users" class="space-y-4">
				{#await usersData}
					<TableSkeleton rows={5} columns={6} />
				{:then}
					<div class="flex items-center justify-between">
						<div class="relative flex-1">
							<Search
								class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground"
							/>
							<Input bind:value={userSearch} placeholder="Search users..." class="pl-10" />
						</div>
						<Button size="sm" class="ml-4" onclick={() => (createUserOpen = true)}>
							<Plus class="h-4 w-4" />
							Create User
						</Button>
					</div>
					<DataTable table={usersTable} noResultsMessage="No user accounts found." />
				{/await}
			</Tabs.Content>

			<Tabs.Content value="groups" class="space-y-4">
				{#await groupsData}
					<TableSkeleton rows={3} columns={3} />
				{:then}
					<div class="flex items-center justify-end">
						<Button size="sm" onclick={() => (createGroupOpen = true)}>
							<Plus class="h-4 w-4" />
							Create Group
						</Button>
					</div>
					<DataTable table={groupsTable} noResultsMessage="No groups found." />
				{/await}
			</Tabs.Content>
		</Tabs.Root>
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
					{#each GROUP_ROLES as role (role)}
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
