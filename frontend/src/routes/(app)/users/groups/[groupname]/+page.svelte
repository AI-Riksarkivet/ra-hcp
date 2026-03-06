<script lang="ts">
	import { page } from '$app/state';
	import { goto } from '$app/navigation';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Trash2, HelpCircle } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_group,
		update_group,
		delete_group,
		get_group_permissions,
		type DataAccessPermissions,
	} from '$lib/users.remote.js';
	import {
		GROUP_ROLES,
		ROLE_DESCRIPTIONS,
		PERMISSION_DESCRIPTIONS,
		getGroupName,
		getGroupRoles,
	} from '$lib/constants.js';
	import type { GroupAccount } from '$lib/constants.js';
	import BackButton from '$lib/components/ui/back-button.svelte';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import NoTenantPlaceholder from '$lib/components/ui/no-tenant-placeholder.svelte';
	import {
		DataTable,
		createSvelteTable,
		getCoreRowModel,
		renderSnippet,
	} from '$lib/components/ui/data-table/index.js';
	import type { ColumnDef } from '@tanstack/table-core';

	let tenant = $derived(page.data.tenant as string | undefined);
	let groupname = $derived(page.params.groupname ?? '');

	// Group info
	let groupData = $derived(tenant && groupname ? get_group({ tenant, groupname }) : undefined);
	let group = $derived((groupData?.current ?? null) as GroupAccount | null);

	// Local editable state
	let syncVersion = $state(0);
	let localDescription = $state('');
	let localRoles = $state<string[]>([]);

	$effect(() => {
		const g = group;
		void syncVersion;
		localDescription = g?.description ?? '';
		localRoles = g ? getGroupRoles(g) : [];
	});

	let dirty = $derived(
		localDescription !== (group?.description ?? '') ||
			JSON.stringify([...localRoles].sort()) !==
				JSON.stringify([...(group ? getGroupRoles(group) : [])].sort())
	);

	let saving = $state(false);

	async function saveGroup() {
		if (!tenant || !groupData) return;
		saving = true;
		try {
			const body: Record<string, unknown> = {
				description: localDescription,
				roles: { role: localRoles },
			};
			await update_group({ tenant, groupname, body }).updates(groupData);
			syncVersion++;
			toast.success('Group updated successfully');
		} catch {
			toast.error('Failed to update group');
		} finally {
			saving = false;
		}
	}

	// Roles toggle
	function toggleRole(role: string) {
		if (localRoles.includes(role)) {
			localRoles = localRoles.filter((r) => r !== role);
		} else {
			localRoles = [...localRoles, role];
		}
	}

	// Namespace Access
	let permsData = $derived(
		tenant && groupname ? get_group_permissions({ tenant, groupname }) : undefined
	);
	let nsPermissions = $derived(
		((permsData?.current as DataAccessPermissions)?.namespacePermission ?? []).filter(
			(entry) => entry.permissions?.permission && entry.permissions.permission.length > 0
		)
	);

	type NsPermEntry = { namespaceName: string; permissions?: { permission?: string[] } };

	const nsPermColumns: ColumnDef<NsPermEntry>[] = [
		{
			accessorKey: 'namespaceName',
			header: 'Namespace',
			cell: ({ row }) => renderSnippet(nsNameCell, row.original),
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			id: 'permissions',
			header: 'Permissions',
			cell: ({ row }) => renderSnippet(nsPermsCell, row.original),
		},
	];

	let nsPermTable = $derived(
		createSvelteTable({
			get data() {
				return nsPermissions;
			},
			columns: nsPermColumns,
			getCoreRowModel: getCoreRowModel(),
		})
	);

	// Delete
	let deleteOpen = $state(false);
	let deleting = $state(false);

	async function handleDelete() {
		if (!tenant) return;
		deleting = true;
		try {
			await delete_group({ tenant, groupname });
			toast.success(`Group "${groupname}" deleted`);
			goto('/users');
		} catch {
			toast.error('Failed to delete group');
			deleting = false;
		}
	}
</script>

{#snippet nsNameCell(entry: NsPermEntry)}
	<a
		href="/namespaces/{entry.namespaceName}"
		class="text-primary underline-offset-4 hover:underline"
	>
		{entry.namespaceName}
	</a>
{/snippet}

{#snippet nsPermsCell(entry: NsPermEntry)}
	<div class="flex flex-wrap gap-1">
		{#each entry.permissions?.permission ?? [] as perm (perm)}
			<Tooltip.Root>
				<Tooltip.Trigger>
					{#snippet child({ props })}
						<span {...props}><Badge variant="secondary">{perm}</Badge></span>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Content>{PERMISSION_DESCRIPTIONS[perm] ?? perm}</Tooltip.Content>
			</Tooltip.Root>
		{/each}
	</div>
{/snippet}

<svelte:head>
	<title>{groupname} - Group Settings - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-4">
			<BackButton href="/users" label="Back to users & groups" />
			<div>
				<h2 class="text-2xl font-bold">{groupname}</h2>
				<p class="mt-1 text-sm text-muted-foreground">
					{group?.description || 'Group settings and access control'}
				</p>
			</div>
		</div>
		{#if group}
			<Button variant="destructive" size="sm" onclick={() => (deleteOpen = true)}>
				<Trash2 class="h-4 w-4" />
				Delete
			</Button>
		{/if}
	</div>

	{#if !tenant}
		<NoTenantPlaceholder message="Log in with a tenant to view group details." />
	{:else}
		{#await groupData}
			<div class="rounded-lg border p-5">
				<div class="grid gap-3 sm:grid-cols-2">
					{#each Array(3) as _, i (i)}
						<div class="space-y-1">
							<div class="h-3 w-20 animate-pulse rounded bg-muted"></div>
							<div class="h-8 w-full animate-pulse rounded bg-muted"></div>
						</div>
					{/each}
				</div>
			</div>
		{:then}
			{#if !group}
				<div class="rounded-lg border border-dashed p-8 text-center">
					<p class="text-muted-foreground">Group not found or could not be loaded.</p>
				</div>
			{:else}
				<!-- General Info + Roles -->
				<div class="rounded-lg border p-5">
					<h3 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
						General
					</h3>
					<div class="mt-3 grid gap-x-4 gap-y-2 sm:grid-cols-2">
						<div class="space-y-1">
							<Label class="text-xs">Group Name</Label>
							<p class="text-sm font-medium">{getGroupName(group)}</p>
						</div>
						<div class="space-y-1">
							<Label for="group-description" class="text-xs">Description</Label>
							<Input
								id="group-description"
								bind:value={localDescription}
								placeholder="Optional description"
								class="h-8 text-sm"
							/>
						</div>
					</div>

					<div class="mt-4 border-t pt-3">
						<h3 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
							Roles
						</h3>
						<div class="mt-2 flex flex-wrap gap-x-6 gap-y-2">
							{#each GROUP_ROLES as role (role)}
								<label class="flex items-center gap-1.5 text-sm">
									<Checkbox
										checked={localRoles.includes(role)}
										onCheckedChange={() => toggleRole(role)}
									/>
									{role}
									{#if ROLE_DESCRIPTIONS[role]}
										<Tooltip.Root>
											<Tooltip.Trigger>
												{#snippet child({ props })}
													<span {...props}
														><HelpCircle class="h-3 w-3 text-muted-foreground" /></span
													>
												{/snippet}
											</Tooltip.Trigger>
											<Tooltip.Content>{ROLE_DESCRIPTIONS[role]}</Tooltip.Content>
										</Tooltip.Root>
									{/if}
								</label>
							{/each}
						</div>
						<div class="pt-4">
							<SaveButton {dirty} {saving} onclick={saveGroup} />
						</div>
					</div>
				</div>

				<!-- Namespace Access -->
				<section class="space-y-3">
					<h3 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
						Namespace Access
					</h3>
					{#await permsData}
						<div class="rounded-lg border p-5">
							<div class="space-y-2">
								{#each Array(3) as _, i (i)}
									<div class="h-5 w-full animate-pulse rounded bg-muted"></div>
								{/each}
							</div>
						</div>
					{:then}
						<DataTable table={nsPermTable} noResultsMessage="This group has no namespace access." />
					{/await}
				</section>
			{/if}
		{/await}
	{/if}
</div>

<DeleteConfirmDialog
	bind:open={deleteOpen}
	name={groupname}
	itemType="group"
	loading={deleting}
	onconfirm={handleDelete}
/>
