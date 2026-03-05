<script lang="ts">
	import { page } from '$app/state';
	import {
		type ColumnDef,
		type ColumnFiltersState,
		type PaginationState,
		type SortingState,
		type VisibilityState,
		getCoreRowModel,
		getFilteredRowModel,
		getPaginationRowModel,
		getSortedRowModel,
	} from '@tanstack/table-core';
	import { createRawSnippet } from 'svelte';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import { Plus } from 'lucide-svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import {
		FlexRender,
		createSvelteTable,
		renderComponent,
		renderSnippet,
	} from '$lib/components/ui/data-table/index.js';
	import DataTableHeaderButton from '$lib/components/ui/data-table/data-table-header-button.svelte';
	import DataTableActions from './data-table/data-table-actions.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { toast } from 'svelte-sonner';
	import { goto } from '$app/navigation';
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

	// --- Namespace access per user ---
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

	// ── User row type ──────────────────────────────────────────────
	type UserRow = {
		username: string;
		fullName: string;
		enabled: boolean;
		roles: string[];
	};

	let userData = $derived<UserRow[]>(
		users.map((u) => ({
			username: u.username,
			fullName: u.fullName ?? '',
			enabled: u.enabled !== false,
			roles: getUserRoles(u),
		}))
	);

	// ── User column definitions ────────────────────────────────────
	const userColumns: ColumnDef<UserRow>[] = [
		{
			accessorKey: 'username',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Username',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ username: string }]>((getU) => {
					const { username } = getU();
					return {
						render: () =>
							`<a href="/users/${encodeURIComponent(username)}" class="font-medium text-primary underline-offset-4 hover:underline">${username}</a>`,
					};
				});
				return renderSnippet(s, { username: row.original.username });
			},
		},
		{
			accessorKey: 'fullName',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Full Name',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ val: string }]>((getVal) => {
					const { val } = getVal();
					return {
						render: () => `<span class="text-muted-foreground">${val || '—'}</span>`,
					};
				});
				return renderSnippet(s, { val: row.original.fullName });
			},
		},
		{
			accessorKey: 'enabled',
			header: 'Status',
			cell: ({ row }) =>
				renderComponent(Badge, {
					variant: row.original.enabled ? 'default' : 'outline',
					children: createRawSnippet(() => ({
						render: () => (row.original.enabled ? 'Active' : 'Disabled'),
					})),
				}),
			filterFn: (row, _id, filterValue) => {
				if (!filterValue) return true;
				return row.original.enabled === (filterValue === 'active');
			},
		},
		{
			accessorKey: 'roles',
			header: 'Roles',
			cell: ({ row }) => {
				const roles = row.original.roles;
				if (roles.length === 0) {
					const s = createRawSnippet(() => ({
						render: () => `<span class="text-muted-foreground">—</span>`,
					}));
					return renderSnippet(s, undefined);
				}
				const s = createRawSnippet<[{ roles: string[] }]>((getRoles) => {
					const { roles } = getRoles();
					return {
						render: () =>
							roles
								.map(
									(r) =>
										`<span class="inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold bg-secondary text-secondary-foreground mr-1">${r}</span>`
								)
								.join(''),
					};
				});
				return renderSnippet(s, { roles });
			},
			enableSorting: false,
		},
		{
			id: 'namespaceAccess',
			header: 'Namespace Access',
			cell: ({ row }) => {
				const nsList = userNsAccess[row.original.username];
				if (nsList === undefined) {
					const s = createRawSnippet(() => ({
						render: () => `<div class="h-5 w-20 animate-pulse rounded bg-muted"></div>`,
					}));
					return renderSnippet(s, undefined);
				}
				if (nsList.length === 0) {
					const s = createRawSnippet(() => ({
						render: () => `<span class="text-muted-foreground">—</span>`,
					}));
					return renderSnippet(s, undefined);
				}
				const s = createRawSnippet<[{ ns: string[] }]>((getNs) => {
					const { ns } = getNs();
					return {
						render: () =>
							`<div class="flex flex-wrap gap-1">${ns
								.map(
									(n) =>
										`<a href="/namespaces/${encodeURIComponent(n)}"><span class="inline-flex items-center rounded-md border px-2.5 py-0.5 text-xs font-semibold cursor-pointer hover:bg-accent">${n}</span></a>`
								)
								.join('')}</div>`,
					};
				});
				return renderSnippet(s, { ns: nsList });
			},
			enableSorting: false,
		},
		{
			id: 'actions',
			enableHiding: false,
			cell: ({ row }) =>
				renderComponent(DataTableActions, {
					username: row.original.username,
					onnavigate: () => goto(`/users/${encodeURIComponent(row.original.username)}`),
				}),
		},
	];

	// ── User table state ──────────────────────────────────────────
	let userPagination = $state<PaginationState>({ pageIndex: 0, pageSize: 20 });
	let userSorting = $state<SortingState>([]);
	let userColumnFilters = $state<ColumnFiltersState>([]);
	let userColumnVisibility = $state<VisibilityState>({});

	const userTable = createSvelteTable({
		get data() {
			return userData;
		},
		columns: userColumns,
		state: {
			get pagination() {
				return userPagination;
			},
			get sorting() {
				return userSorting;
			},
			get columnFilters() {
				return userColumnFilters;
			},
			get columnVisibility() {
				return userColumnVisibility;
			},
		},
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		onPaginationChange: (updater) => {
			userPagination = typeof updater === 'function' ? updater(userPagination) : updater;
		},
		onSortingChange: (updater) => {
			userSorting = typeof updater === 'function' ? updater(userSorting) : updater;
		},
		onColumnFiltersChange: (updater) => {
			userColumnFilters = typeof updater === 'function' ? updater(userColumnFilters) : updater;
		},
		onColumnVisibilityChange: (updater) => {
			userColumnVisibility =
				typeof updater === 'function' ? updater(userColumnVisibility) : updater;
		},
	});

	// ── Group row type ─────────────────────────────────────────────
	type GroupRow = { name: string; description: string };

	let groupData = $derived<GroupRow[]>(
		groups.map((g) => ({
			name: g.groupname ?? g.name ?? '',
			description: g.description ?? '',
		}))
	);

	// ── Group column definitions ───────────────────────────────────
	const groupColumns: ColumnDef<GroupRow>[] = [
		{
			accessorKey: 'name',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Group Name',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ name: string }]>((getName) => {
					const { name } = getName();
					return {
						render: () => `<span class="font-medium">${name}</span>`,
					};
				});
				return renderSnippet(s, { name: row.original.name });
			},
		},
		{
			accessorKey: 'description',
			header: 'Description',
			cell: ({ row }) => {
				const s = createRawSnippet<[{ desc: string }]>((getDesc) => {
					const { desc } = getDesc();
					return {
						render: () => `<span class="text-muted-foreground">${desc || '—'}</span>`,
					};
				});
				return renderSnippet(s, { desc: row.original.description });
			},
		},
	];

	// ── Group table state ─────────────────────────────────────────
	let groupPagination = $state<PaginationState>({ pageIndex: 0, pageSize: 20 });
	let groupSorting = $state<SortingState>([]);
	let groupColumnFilters = $state<ColumnFiltersState>([]);

	const groupTable = createSvelteTable({
		get data() {
			return groupData;
		},
		columns: groupColumns,
		state: {
			get pagination() {
				return groupPagination;
			},
			get sorting() {
				return groupSorting;
			},
			get columnFilters() {
				return groupColumnFilters;
			},
		},
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		onPaginationChange: (updater) => {
			groupPagination = typeof updater === 'function' ? updater(groupPagination) : updater;
		},
		onSortingChange: (updater) => {
			groupSorting = typeof updater === 'function' ? updater(groupSorting) : updater;
		},
		onColumnFiltersChange: (updater) => {
			groupColumnFilters = typeof updater === 'function' ? updater(groupColumnFilters) : updater;
		},
	});

	// ── Create User dialog ────────────────────────────────────────
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

	// ── Create Group dialog ───────────────────────────────────────
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
		<div class="space-y-4">
			{#await usersData}
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-3">
						<h3 class="text-lg font-semibold">User Accounts</h3>
					</div>
				</div>
				<TableSkeleton rows={5} columns={6} />
			{:then _}
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-3">
						<h3 class="text-lg font-semibold">User Accounts</h3>
						<Badge variant="secondary">{userData.length}</Badge>
					</div>
					<Button size="sm" onclick={() => (createUserOpen = true)}>
						<Plus class="h-4 w-4" />
						Create User
					</Button>
				</div>

				<!-- Toolbar -->
				<div class="flex items-center gap-2">
					<Input
						placeholder="Filter users..."
						value={(userTable.getColumn('username')?.getFilterValue() as string) ?? ''}
						oninput={(e) => userTable.getColumn('username')?.setFilterValue(e.currentTarget.value)}
						class="max-w-sm"
					/>
					<DropdownMenu.Root>
						<DropdownMenu.Trigger>
							{#snippet child({ props })}
								<Button {...props} variant="outline" class="ml-auto">
									Columns <ChevronDown class="ml-2 size-4" />
								</Button>
							{/snippet}
						</DropdownMenu.Trigger>
						<DropdownMenu.Content align="end">
							{#each userTable
								.getAllColumns()
								.filter((col) => col.getCanHide()) as column (column.id)}
								<DropdownMenu.CheckboxItem
									class="capitalize"
									checked={column.getIsVisible()}
									onCheckedChange={(v) => column.toggleVisibility(!!v)}
								>
									{column.id}
								</DropdownMenu.CheckboxItem>
							{/each}
						</DropdownMenu.Content>
					</DropdownMenu.Root>
				</div>

				<!-- Table -->
				<div class="rounded-md border">
					<Table.Root>
						<Table.Header>
							{#each userTable.getHeaderGroups() as headerGroup (headerGroup.id)}
								<Table.Row>
									{#each headerGroup.headers as header (header.id)}
										<Table.Head>
											{#if !header.isPlaceholder}
												<FlexRender
													content={header.column.columnDef.header}
													context={header.getContext()}
												/>
											{/if}
										</Table.Head>
									{/each}
								</Table.Row>
							{/each}
						</Table.Header>
						<Table.Body>
							{#each userTable.getRowModel().rows as row (row.id)}
								<Table.Row
									class="cursor-pointer"
									onclick={() => goto(`/users/${encodeURIComponent(row.original.username)}`)}
								>
									{#each row.getVisibleCells() as cell (cell.id)}
										<Table.Cell
											onclick={(e) => {
												const target = e.target as HTMLElement;
												if (
													target.closest('[role=menuitem]') ||
													target.closest('button') ||
													target.closest('a')
												) {
													e.stopPropagation();
												}
											}}
										>
											<FlexRender
												content={cell.column.columnDef.cell}
												context={cell.getContext()}
											/>
										</Table.Cell>
									{/each}
								</Table.Row>
							{:else}
								<Table.Row>
									<Table.Cell colspan={userColumns.length} class="h-24 text-center">
										No user accounts found.
									</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>

				<!-- Pagination -->
				<div class="flex items-center justify-end space-x-2">
					<div class="flex-1 text-sm text-muted-foreground">
						{userTable.getFilteredRowModel().rows.length} user(s) total.
					</div>
					<div class="space-x-2">
						<Button
							variant="outline"
							size="sm"
							onclick={() => userTable.previousPage()}
							disabled={!userTable.getCanPreviousPage()}
						>
							Previous
						</Button>
						<Button
							variant="outline"
							size="sm"
							onclick={() => userTable.nextPage()}
							disabled={!userTable.getCanNextPage()}
						>
							Next
						</Button>
					</div>
				</div>
			{/await}
		</div>

		<!-- Groups -->
		<div class="space-y-4">
			{#await groupsData}
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-3">
						<h3 class="text-lg font-semibold">Groups</h3>
					</div>
				</div>
				<TableSkeleton rows={3} columns={2} />
			{:then _}
				<div class="flex items-center justify-between">
					<div class="flex items-center gap-3">
						<h3 class="text-lg font-semibold">Groups</h3>
						<Badge variant="secondary">{groupData.length}</Badge>
					</div>
					<Button size="sm" onclick={() => (createGroupOpen = true)}>
						<Plus class="h-4 w-4" />
						Create Group
					</Button>
				</div>

				<!-- Toolbar -->
				<div class="flex items-center gap-2">
					<Input
						placeholder="Filter groups..."
						value={(groupTable.getColumn('name')?.getFilterValue() as string) ?? ''}
						oninput={(e) => groupTable.getColumn('name')?.setFilterValue(e.currentTarget.value)}
						class="max-w-sm"
					/>
				</div>

				<!-- Table -->
				<div class="rounded-md border">
					<Table.Root>
						<Table.Header>
							{#each groupTable.getHeaderGroups() as headerGroup (headerGroup.id)}
								<Table.Row>
									{#each headerGroup.headers as header (header.id)}
										<Table.Head>
											{#if !header.isPlaceholder}
												<FlexRender
													content={header.column.columnDef.header}
													context={header.getContext()}
												/>
											{/if}
										</Table.Head>
									{/each}
								</Table.Row>
							{/each}
						</Table.Header>
						<Table.Body>
							{#each groupTable.getRowModel().rows as row (row.id)}
								<Table.Row>
									{#each row.getVisibleCells() as cell (cell.id)}
										<Table.Cell>
											<FlexRender
												content={cell.column.columnDef.cell}
												context={cell.getContext()}
											/>
										</Table.Cell>
									{/each}
								</Table.Row>
							{:else}
								<Table.Row>
									<Table.Cell colspan={groupColumns.length} class="h-24 text-center">
										No groups found.
									</Table.Cell>
								</Table.Row>
							{/each}
						</Table.Body>
					</Table.Root>
				</div>

				<!-- Pagination -->
				<div class="flex items-center justify-end space-x-2">
					<div class="flex-1 text-sm text-muted-foreground">
						{groupTable.getFilteredRowModel().rows.length} group(s) total.
					</div>
					<div class="space-x-2">
						<Button
							variant="outline"
							size="sm"
							onclick={() => groupTable.previousPage()}
							disabled={!groupTable.getCanPreviousPage()}
						>
							Previous
						</Button>
						<Button
							variant="outline"
							size="sm"
							onclick={() => groupTable.nextPage()}
							disabled={!groupTable.getCanNextPage()}
						>
							Next
						</Button>
					</div>
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
