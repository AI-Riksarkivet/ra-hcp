<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { ArrowLeft, Save, Loader2, Trash2, KeyRound, HelpCircle } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_user,
		update_user,
		delete_user,
		change_password,
		get_user_permissions,
		type DataAccessPermissions,
	} from '$lib/users.remote.js';

	type User = {
		username: string;
		fullName?: string;
		description?: string;
		enabled?: boolean;
		localAuthentication?: boolean;
		roles?: { role?: string[] };
	};

	const AVAILABLE_ROLES = ['ADMINISTRATOR', 'SECURITY', 'MONITOR', 'COMPLIANCE'] as const;

	const ROLE_DESCRIPTIONS: Record<string, string> = {
		ADMINISTRATOR:
			'Full tenant administration — create namespaces, manage users and groups, view statistics',
		SECURITY: 'Manage console security, search security, and authentication settings',
		MONITOR: 'View tenant and namespace statistics and chargeback reports (read-only)',
		COMPLIANCE: 'Manage compliance and retention settings on namespaces',
	};

	const PERMISSION_DESCRIPTIONS: Record<string, string> = {
		BROWSE: 'List objects in the namespace',
		READ: 'Read object data and metadata',
		WRITE: 'Create and modify objects',
		DELETE: 'Delete objects',
		PURGE: 'Permanently remove objects (bypass retention)',
		SEARCH: 'Query objects via HCP metadata search',
		READ_ACL: 'Read object access control lists',
		WRITE_ACL: 'Modify object access control lists',
		CHOWN: 'Change object ownership',
		PRIVILEGED: 'Perform privileged operations like deleting retained objects',
	};

	let tenant = $derived(page.data.tenant as string | undefined);
	let username = $derived(page.params.username ?? '');

	// --- User general info ---
	let userData = $derived(tenant && username ? get_user({ tenant, username }) : undefined);
	let user = $derived((userData?.current ?? null) as User | null);

	// --- Local editable state ---
	let syncVersion = $state(0);
	let localFullName = $state('');
	let localDescription = $state('');
	let localEnabled = $state(true);
	let localRoles = $state<string[]>([]);

	$effect(() => {
		const u = user;
		void syncVersion;
		localFullName = u?.fullName ?? '';
		localDescription = u?.description ?? '';
		localEnabled = u?.enabled ?? true;
		localRoles = u?.roles?.role ? [...u.roles.role] : [];
	});

	let dirty = $derived(
		localFullName !== (user?.fullName ?? '') ||
			localDescription !== (user?.description ?? '') ||
			localEnabled !== (user?.enabled ?? true) ||
			JSON.stringify([...localRoles].sort()) !==
				JSON.stringify([...(user?.roles?.role ?? [])].sort())
	);

	let saving = $state(false);

	async function saveUser() {
		if (!tenant || !userData) return;
		saving = true;
		try {
			const body: Record<string, unknown> = {
				fullName: localFullName,
				description: localDescription,
				enabled: localEnabled,
				roles: { role: localRoles },
			};
			await update_user({ tenant, username, body }).updates(userData);
			syncVersion++;
			toast.success('User updated successfully');
		} catch {
			toast.error('Failed to update user');
		} finally {
			saving = false;
		}
	}

	// --- Roles toggle ---
	function toggleRole(role: string) {
		if (localRoles.includes(role)) {
			localRoles = localRoles.filter((r) => r !== role);
		} else {
			localRoles = [...localRoles, role];
		}
	}

	// --- Change Password ---
	let passwordOpen = $state(false);
	let newPassword = $state('');
	let confirmPassword = $state('');
	let changingPassword = $state(false);

	let passwordValid = $derived(newPassword.length > 0 && newPassword === confirmPassword);

	async function handleChangePassword() {
		if (!tenant || !passwordValid) return;
		changingPassword = true;
		try {
			await change_password({ tenant, username, password: newPassword });
			toast.success('Password changed successfully');
			newPassword = '';
			confirmPassword = '';
			passwordOpen = false;
		} catch {
			toast.error('Failed to change password');
		} finally {
			changingPassword = false;
		}
	}

	// --- Namespace Access ---
	let permsData = $derived(
		tenant && username ? get_user_permissions({ tenant, username }) : undefined
	);
	let nsPermissions = $derived(
		((permsData?.current as DataAccessPermissions)?.namespacePermission ?? []).filter(
			(entry) => entry.permissions?.permission && entry.permissions.permission.length > 0
		)
	);

	// --- Delete User ---
	let deleteOpen = $state(false);
	let deleting = $state(false);

	async function handleDelete() {
		if (!tenant) return;
		deleting = true;
		try {
			await delete_user({ tenant, username });
			toast.success(`User "${username}" deleted`);
			goto('/users');
		} catch {
			toast.error('Failed to delete user');
			deleting = false;
		}
	}
</script>

<svelte:head>
	<title>{username} - User Settings - HCP Admin Console</title>
</svelte:head>

<div class="space-y-8">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-4">
			<Tooltip.Root>
				<Tooltip.Trigger>
					{#snippet child({ props })}
						<a
							href="/users"
							class="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
							{...props}
						>
							<ArrowLeft class="h-5 w-5" />
						</a>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Content>Back to users</Tooltip.Content>
			</Tooltip.Root>
			<div>
				<h2 class="text-2xl font-bold">{username}</h2>
				<p class="mt-1 text-sm text-muted-foreground">
					{user?.fullName || 'User settings and access control'}
				</p>
			</div>
		</div>
		{#if user}
			<div class="flex items-center gap-2">
				<Button variant="outline" size="sm" onclick={() => (passwordOpen = true)}>
					<KeyRound class="h-4 w-4" />
					Change Password
				</Button>
				<Button variant="destructive" size="sm" onclick={() => (deleteOpen = true)}>
					<Trash2 class="h-4 w-4" />
					Delete
				</Button>
			</div>
		{/if}
	</div>

	{#if !tenant}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to view user details.</p>
		</div>
	{:else}
		<!-- Section 1: General Information -->
		<section class="space-y-4">
			<h3 class="text-lg font-semibold">General Information</h3>
			{#await userData}
				<div class="rounded-lg border p-6">
					<div class="grid gap-4 sm:grid-cols-2">
						{#each Array(4) as _, i (i)}
							<div class="space-y-1">
								<div class="h-3 w-20 animate-pulse rounded bg-muted"></div>
								<div class="h-9 w-full animate-pulse rounded bg-muted"></div>
							</div>
						{/each}
					</div>
				</div>
			{:then _}
				<div class="rounded-lg border p-6">
					{#if user}
						<div class="grid gap-4 sm:grid-cols-2">
							<div class="space-y-2">
								<Label>Username</Label>
								<p class="text-sm font-medium">{user.username}</p>
							</div>
							<div class="space-y-2">
								<Label for="user-fullname">Full Name</Label>
								<Input id="user-fullname" bind:value={localFullName} placeholder="Full name" />
							</div>
							<div class="space-y-2">
								<Label for="user-description">Description</Label>
								<Input
									id="user-description"
									bind:value={localDescription}
									placeholder="Optional description"
								/>
							</div>
							<div class="flex items-center gap-2 self-end">
								<label class="flex items-center gap-2 text-sm">
									<input
										type="checkbox"
										bind:checked={localEnabled}
										class="h-4 w-4 rounded border-input"
									/>
									Enabled
								</label>
							</div>
						</div>
					{:else}
						<p class="text-center text-sm text-muted-foreground">
							User not found or could not be loaded.
						</p>
					{/if}
				</div>
			{/await}
		</section>

		<!-- Section 2: Roles -->
		{#if user}
			<section class="space-y-4">
				<h3 class="text-lg font-semibold">Roles</h3>
				<div class="rounded-lg border p-6">
					<div class="flex flex-wrap gap-x-8 gap-y-4">
						{#each AVAILABLE_ROLES as role (role)}
							<label class="flex items-center gap-2 text-sm">
								<input
									type="checkbox"
									checked={localRoles.includes(role)}
									onchange={() => toggleRole(role)}
									class="h-4 w-4 rounded border-input"
								/>
								{role}
								<Tooltip.Root>
									<Tooltip.Trigger>
										{#snippet child({ props })}
											<span {...props} class="inline-flex items-center gap-1">
												<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
											</span>
										{/snippet}
									</Tooltip.Trigger>
									<Tooltip.Content>{ROLE_DESCRIPTIONS[role]}</Tooltip.Content>
								</Tooltip.Root>
							</label>
						{/each}
					</div>
					<div class="mt-4 flex items-center gap-3">
						<Button size="sm" disabled={!dirty || saving} onclick={saveUser}>
							{#if saving}
								<Loader2 class="h-4 w-4 animate-spin" />
								Saving...
							{:else}
								<Save class="h-4 w-4" />
								Save
							{/if}
						</Button>
						{#if dirty}
							<span class="text-xs text-muted-foreground">Unsaved changes</span>
						{/if}
					</div>
				</div>
			</section>

			<!-- Section 3: Namespace Access -->
			<section class="space-y-4">
				<h3 class="text-lg font-semibold">Namespace Access</h3>
				{#await permsData}
					<div class="rounded-lg border p-6">
						<div class="space-y-3">
							{#each Array(3) as _, i (i)}
								<div class="h-5 w-full animate-pulse rounded bg-muted"></div>
							{/each}
						</div>
					</div>
				{:then _}
					{#if nsPermissions.length === 0}
						<div class="rounded-lg border border-dashed p-8 text-center">
							<p class="text-muted-foreground">This user has no namespace access.</p>
						</div>
					{:else}
						<div class="overflow-x-auto rounded-lg border">
							<table class="w-full text-left text-sm">
								<thead
									class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground"
								>
									<tr>
										<th class="px-4 py-3 font-medium">Namespace</th>
										<th class="px-4 py-3 font-medium">Permissions</th>
									</tr>
								</thead>
								<tbody class="divide-y">
									{#each nsPermissions as entry (entry.namespaceName)}
										<tr class="bg-card transition-colors hover:bg-accent/50">
											<td class="px-4 py-3 font-medium">
												<a
													href="/namespaces/{entry.namespaceName}"
													class="text-primary underline-offset-4 hover:underline"
												>
													{entry.namespaceName}
												</a>
											</td>
											<td class="px-4 py-3">
												<div class="flex flex-wrap gap-1">
													{#each entry.permissions?.permission ?? [] as perm (perm)}
														<Tooltip.Root>
															<Tooltip.Trigger>
																{#snippet child({ props })}
																	<span {...props}>
																		<Badge variant="secondary">{perm}</Badge>
																	</span>
																{/snippet}
															</Tooltip.Trigger>
															<Tooltip.Content
																>{PERMISSION_DESCRIPTIONS[perm] ?? perm}</Tooltip.Content
															>
														</Tooltip.Root>
													{/each}
												</div>
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				{/await}
			</section>
		{/if}
	{/if}
</div>

<!-- Change Password Dialog -->
<Dialog.Root bind:open={passwordOpen}>
	<Dialog.Content class="sm:max-w-md">
		<Dialog.Header>
			<Dialog.Title>Change Password</Dialog.Title>
			<Dialog.Description>Set a new password for "{username}".</Dialog.Description>
		</Dialog.Header>
		<div class="space-y-4">
			<div class="space-y-2">
				<Label for="new-password">New Password</Label>
				<Input
					id="new-password"
					type="password"
					bind:value={newPassword}
					placeholder="Enter new password"
				/>
			</div>
			<div class="space-y-2">
				<Label for="confirm-password">Confirm Password</Label>
				<Input
					id="confirm-password"
					type="password"
					bind:value={confirmPassword}
					placeholder="Confirm new password"
				/>
			</div>
			{#if newPassword.length > 0 && confirmPassword.length > 0 && newPassword !== confirmPassword}
				<p class="text-sm text-destructive">Passwords do not match.</p>
			{/if}
			<Dialog.Footer>
				<Button
					variant="ghost"
					type="button"
					onclick={() => {
						passwordOpen = false;
						newPassword = '';
						confirmPassword = '';
					}}>Cancel</Button
				>
				<Button disabled={!passwordValid || changingPassword} onclick={handleChangePassword}>
					{#if changingPassword}
						<Loader2 class="h-4 w-4 animate-spin" />
						Changing...
					{:else}
						Change Password
					{/if}
				</Button>
			</Dialog.Footer>
		</div>
	</Dialog.Content>
</Dialog.Root>

<DeleteConfirmDialog
	bind:open={deleteOpen}
	name={username}
	itemType="user"
	loading={deleting}
	onconfirm={handleDelete}
/>
