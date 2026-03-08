<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Loader2, Shield, HelpCircle, Info, Trash2, Plus } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import { SvelteMap } from 'svelte/reactivity';
	import {
		get_bucket_acl,
		put_bucket_acl,
		type AclGrant,
		type AclData,
	} from '$lib/buckets.remote.js';
	import { get_users, get_groups } from '$lib/users.remote.js';
	import type { User, GroupAccount } from '$lib/constants.js';

	let {
		bucket,
		tenant,
	}: {
		bucket: string;
		tenant?: string;
	} = $props();

	const PERMISSIONS: { value: string; label: string; description: string }[] = [
		{
			value: 'FULL_CONTROL',
			label: 'Full Control',
			description:
				'Grants READ, WRITE, READ_ACP, and WRITE_ACP — the grantee can read/write objects and manage ACLs.',
		},
		{
			value: 'READ',
			label: 'Read',
			description: 'List objects in the bucket and read their contents.',
		},
		{
			value: 'WRITE',
			label: 'Write',
			description: 'Create, overwrite, and delete objects in the bucket.',
		},
		{
			value: 'READ_ACP',
			label: 'Read ACP',
			description: 'Read the bucket access control policy (ACL).',
		},
		{
			value: 'WRITE_ACP',
			label: 'Write ACP',
			description: 'Modify the bucket access control policy (ACL).',
		},
	];

	const PERMISSION_MAP = new Map(PERMISSIONS.map((p) => [p.value, p]));

	let aclData = $derived(get_bucket_acl({ bucket }));
	let acl = $derived((aclData?.current ?? { owner: null, grants: [] }) as AclData);

	// Fetch users/groups when tenant is available
	let usersData = $derived(tenant ? get_users({ tenant }) : null);
	let groupsData = $derived(tenant ? get_groups({ tenant }) : null);
	let users = $derived((usersData?.current ?? []) as User[]);
	let groups = $derived((groupsData?.current ?? []) as GroupAccount[]);

	// Build a lookup map: userGUID -> username for display
	let userNameMap = $derived.by(() => {
		const map = new SvelteMap<string, string>();
		for (const u of users) {
			if (u.userGUID) map.set(u.userGUID, u.username);
			map.set(u.username, u.username);
		}
		return map;
	});

	// Add grant form state
	let granteeType = $state<'CanonicalUser' | 'Group'>('CanonicalUser');
	let granteeId = $state('');
	let grantPermission = $state('READ');
	let granting = $state(false);
	let revoking = $state('');

	function getGranteeName(grant: AclGrant): string {
		const g = grant.Grantee;
		if (!g) return 'Unknown';
		// Try resolving via user lookup
		if (g.ID) {
			const resolved = userNameMap.get(g.ID as string);
			if (resolved) return resolved;
		}
		if (g.DisplayName) return g.DisplayName as string;
		if (g.ID) return (g.ID as string).slice(0, 16) + '…';
		if (g.URI) return (g.URI as string).split('/').pop() ?? (g.URI as string);
		return 'Unknown';
	}

	function getGranteeId(grant: AclGrant): string {
		const g = grant.Grantee;
		if (!g) return '';
		return (g.ID ?? g.URI ?? '') as string;
	}

	function getGranteeType(grant: AclGrant): string {
		const g = grant.Grantee;
		if (!g) return '';
		if (g.URI) return 'Group';
		return 'User';
	}

	function permissionColor(p: string): 'default' | 'secondary' | 'destructive' | 'outline' {
		if (p === 'FULL_CONTROL') return 'destructive';
		if (p === 'WRITE' || p === 'WRITE_ACP') return 'default';
		return 'secondary';
	}

	function permissionLabel(p: string): string {
		return PERMISSION_MAP.get(p)?.label ?? p;
	}

	async function addGrant() {
		if (!aclData || !granteeId) return;
		granting = true;
		try {
			const newGrant = {
				Grantee: {
					Type: granteeType,
					...(granteeType === 'CanonicalUser' ? { ID: granteeId } : { URI: granteeId }),
				},
				Permission: grantPermission,
			};
			await put_bucket_acl({
				bucket,
				owner: acl.owner ? { ID: acl.owner.ID, DisplayName: acl.owner.DisplayName } : undefined,
				grants: [
					...acl.grants.map((g) => ({ Grantee: g.Grantee, Permission: g.Permission })),
					newGrant,
				],
			}).updates(aclData);
			toast.success(`Granted ${permissionLabel(grantPermission)} access`);
			granteeId = '';
			grantPermission = 'READ';
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to add grant');
		} finally {
			granting = false;
		}
	}

	async function revokeGrant(index: number) {
		if (!aclData) return;
		const grant = acl.grants[index];
		const key = getGranteeId(grant) + grant.Permission;
		revoking = key;
		try {
			const remaining = acl.grants
				.filter((_, i) => i !== index)
				.map((g) => ({ Grantee: g.Grantee, Permission: g.Permission }));
			await put_bucket_acl({
				bucket,
				owner: acl.owner ? { ID: acl.owner.ID, DisplayName: acl.owner.DisplayName } : undefined,
				grants: remaining,
			}).updates(aclData);
			toast.success('Grant revoked');
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to revoke grant');
		} finally {
			revoking = '';
		}
	}
</script>

<Card.Root>
	<Card.Header class="pb-3">
		<div class="flex items-center gap-2">
			<Shield class="h-4 w-4 text-muted-foreground" />
			<Card.Title class="text-base">Bucket ACL</Card.Title>
		</div>
		<Card.Description>
			S3 Access Control List — controls who can access this bucket and what they can do with it.
		</Card.Description>
	</Card.Header>
	{#await aclData}
		<Card.Content>
			<div class="space-y-2">
				{#each Array(2) as _, i (i)}
					<div class="h-5 w-48 animate-pulse rounded bg-muted"></div>
				{/each}
			</div>
		</Card.Content>
	{:then}
		<Card.Content class="space-y-4">
			<details class="text-sm">
				<summary class="cursor-pointer font-medium text-muted-foreground hover:text-foreground">
					<Info class="mr-1 inline h-4 w-4" /> How ACLs work
				</summary>
				<div class="mt-2 space-y-2 rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
					<p>
						An <strong class="text-foreground">Access Control List (ACL)</strong> is a set of grants that
						define who can access this bucket and what operations they can perform. Each bucket has exactly
						one ACL.
					</p>
					<p>
						Each <strong class="text-foreground">grant</strong> pairs a
						<strong class="text-foreground">grantee</strong> (a user or predefined group) with a
						<strong class="text-foreground">permission</strong> (what they can do).
					</p>
					<div class="mt-1 space-y-1">
						<p class="font-medium text-foreground">Permission levels:</p>
						{#each PERMISSIONS as p (p.value)}
							<p><strong class="text-foreground">{p.label}</strong> — {p.description}</p>
						{/each}
					</div>
					<p class="mt-1">
						The <strong class="text-foreground">bucket owner</strong> always retains full control regardless
						of what grants are defined.
					</p>
				</div>
			</details>

			{#if acl.owner}
				<div class="flex items-center gap-1.5 text-sm text-muted-foreground">
					<span>Owner:</span>
					<span class="font-medium text-foreground"
						>{acl.owner.DisplayName || acl.owner.ID || '—'}</span
					>
					<Tooltip.Root>
						<Tooltip.Trigger>
							{#snippet child({ props })}
								<span {...props}>
									<HelpCircle class="h-3 w-3" />
								</span>
							{/snippet}
						</Tooltip.Trigger>
						<Tooltip.Content side="top" class="max-w-xs">
							The bucket owner always has full control regardless of the ACL grants below.
						</Tooltip.Content>
					</Tooltip.Root>
				</div>
			{/if}

			<!-- 2-column layout: grants list + add form -->
			<div class="grid gap-6 lg:grid-cols-[1fr,320px]">
				<!-- Left: Current grants -->
				<div class="space-y-2">
					<h3 class="text-sm font-medium">Current Grants</h3>
					{#if acl.grants.length > 0}
						<div class="space-y-1.5">
							{#each acl.grants as grant, i (getGranteeId(grant) + grant.Permission + i)}
								{@const key = getGranteeId(grant) + grant.Permission}
								<div class="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
									<div class="flex min-w-0 items-center gap-2">
										<div class="min-w-0">
											<span class="font-medium">{getGranteeName(grant)}</span>
											<span class="ml-1 text-xs text-muted-foreground"
												>({getGranteeType(grant)})</span
											>
										</div>
										<Tooltip.Root>
											<Tooltip.Trigger>
												{#snippet child({ props })}
													<span {...props}>
														<Badge variant={permissionColor(grant.Permission ?? '')}>
															{permissionLabel(grant.Permission ?? '')}
														</Badge>
													</span>
												{/snippet}
											</Tooltip.Trigger>
											<Tooltip.Content side="top" class="max-w-xs">
												{PERMISSION_MAP.get(grant.Permission ?? '')?.description ??
													grant.Permission}
											</Tooltip.Content>
										</Tooltip.Root>
									</div>
									<Button
										variant="ghost"
										size="icon"
										class="h-7 w-7 shrink-0 text-muted-foreground hover:text-destructive"
										disabled={revoking === key}
										onclick={() => revokeGrant(i)}
										title="Revoke this grant"
									>
										{#if revoking === key}
											<Loader2 class="h-3.5 w-3.5 animate-spin" />
										{:else}
											<Trash2 class="h-3.5 w-3.5" />
										{/if}
									</Button>
								</div>
							{/each}
						</div>
					{:else}
						<p
							class="rounded-md border border-dashed px-3 py-4 text-center text-sm text-muted-foreground"
						>
							No ACL grants configured. Only the bucket owner has access.
						</p>
					{/if}
				</div>

				<!-- Right: Add grant form -->
				<div class="space-y-3 rounded-lg border bg-muted/30 p-4">
					<h3 class="flex items-center gap-1.5 text-sm font-medium">
						<Plus class="h-3.5 w-3.5" /> Add Grant
					</h3>

					<!-- Grantee Type -->
					<div class="space-y-1">
						<Label class="text-xs">Grantee Type</Label>
						<select
							class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-8 w-full rounded-md border px-2 text-sm shadow-sm focus:outline-none focus:ring-1"
							bind:value={granteeType}
							onchange={() => {
								granteeId = '';
							}}
						>
							<option value="CanonicalUser">User</option>
							<option value="Group">Group</option>
						</select>
					</div>

					<!-- Grantee selector -->
					<div class="space-y-1">
						<Label class="text-xs">
							{granteeType === 'CanonicalUser' ? 'User' : 'Group'}
						</Label>
						{#if tenant && granteeType === 'CanonicalUser' && users.length > 0}
							<select
								class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-8 w-full rounded-md border px-2 text-sm shadow-sm focus:outline-none focus:ring-1"
								bind:value={granteeId}
							>
								<option value="">Select a user…</option>
								{#each users as u (u.username)}
									<option value={u.userGUID ?? u.username}>
										{u.username}{u.fullName ? ` — ${u.fullName}` : ''}
									</option>
								{/each}
							</select>
							{#if granteeId}
								<p class="truncate font-mono text-[11px] text-muted-foreground">
									ID: {granteeId}
								</p>
							{/if}
						{:else if tenant && granteeType === 'Group' && groups.length > 0}
							<select
								class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-8 w-full rounded-md border px-2 text-sm shadow-sm focus:outline-none focus:ring-1"
								bind:value={granteeId}
							>
								<option value="">Select a group…</option>
								{#each groups as g (g.groupname ?? g.name)}
									<option value={g.groupname ?? g.name ?? ''}>
										{g.groupname ?? g.name}{g.description ? ` — ${g.description}` : ''}
									</option>
								{/each}
							</select>
						{:else}
							<input
								class="border-input bg-background text-foreground ring-offset-background placeholder:text-muted-foreground focus:ring-ring flex h-8 w-full rounded-md border px-2 text-sm shadow-sm focus:outline-none focus:ring-1"
								bind:value={granteeId}
								placeholder={granteeType === 'CanonicalUser'
									? 'User canonical ID'
									: 'Group name or URI'}
							/>
						{/if}
					</div>

					<!-- Permission -->
					<div class="space-y-1">
						<div class="flex items-center gap-1">
							<Label class="text-xs">Permission</Label>
							<Tooltip.Root>
								<Tooltip.Trigger>
									{#snippet child({ props })}
										<span {...props}>
											<HelpCircle class="h-3 w-3 text-muted-foreground" />
										</span>
									{/snippet}
								</Tooltip.Trigger>
								<Tooltip.Content side="top" class="max-w-xs">
									<ul class="space-y-1 text-xs">
										{#each PERMISSIONS as p (p.value)}
											<li><strong>{p.label}</strong> — {p.description}</li>
										{/each}
									</ul>
								</Tooltip.Content>
							</Tooltip.Root>
						</div>
						<select
							class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-8 w-full rounded-md border px-2 text-sm shadow-sm focus:outline-none focus:ring-1"
							bind:value={grantPermission}
						>
							{#each PERMISSIONS as p (p.value)}
								<option value={p.value}>{p.label}</option>
							{/each}
						</select>
					</div>

					<Button class="w-full" size="sm" disabled={granting || !granteeId} onclick={addGrant}>
						{#if granting}
							<Loader2 class="h-3.5 w-3.5 animate-spin" />
							Adding…
						{:else}
							<Plus class="h-3.5 w-3.5" /> Add Grant
						{/if}
					</Button>
				</div>
			</div>
		</Card.Content>
	{/await}
</Card.Root>
