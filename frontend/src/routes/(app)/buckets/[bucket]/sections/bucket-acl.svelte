<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Plus, Trash2, Loader2, Shield, HelpCircle, Info } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_bucket_acl,
		put_bucket_acl,
		type AclGrant,
		type AclData,
	} from '$lib/buckets.remote.js';

	let {
		bucket,
	}: {
		bucket: string;
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

	let editOpen = $state(false);
	let editGrants = $state<{ id: string; type: string; permission: string }[]>([]);
	let saving = $state(false);

	function getGranteeName(grant: AclGrant): string {
		const g = grant.Grantee;
		if (!g) return 'Unknown';
		if (g.DisplayName) return g.DisplayName as string;
		if (g.ID) return (g.ID as string).slice(0, 16) + '...';
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

	function startEdit() {
		editGrants = acl.grants.map((g) => ({
			id: getGranteeId(g),
			type: (g.Grantee?.Type as string) ?? 'CanonicalUser',
			permission: g.Permission ?? 'READ',
		}));
		editOpen = true;
	}

	function addGrant() {
		editGrants = [...editGrants, { id: '', type: 'CanonicalUser', permission: 'READ' }];
	}

	function removeGrant(index: number) {
		editGrants = editGrants.filter((_, i) => i !== index);
	}

	async function saveAcl() {
		if (!aclData) return;
		saving = true;
		try {
			const grants = editGrants.map((g) => ({
				Grantee: {
					Type: g.type,
					...(g.type === 'CanonicalUser' ? { ID: g.id } : { URI: g.id }),
				},
				Permission: g.permission,
			}));
			await put_bucket_acl({
				bucket,
				owner: acl.owner ? { ID: acl.owner.ID, DisplayName: acl.owner.DisplayName } : undefined,
				grants,
			}).updates(aclData);
			toast.success('Bucket ACL updated');
			editOpen = false;
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to update ACL');
		} finally {
			saving = false;
		}
	}

	function permissionColor(p: string): 'default' | 'secondary' | 'destructive' | 'outline' {
		if (p === 'FULL_CONTROL') return 'destructive';
		if (p === 'WRITE' || p === 'WRITE_ACP') return 'default';
		return 'secondary';
	}

	function permissionLabel(p: string): string {
		return PERMISSION_MAP.get(p)?.label ?? p;
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
		<Card.Action>
			<Button variant="ghost" size="sm" class="h-7" onclick={startEdit}>Edit</Button>
		</Card.Action>
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
						of what grants are defined. Individual objects can also have their own ACLs that override
						the bucket-level settings.
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
			{#if acl.grants.length > 0}
				<div class="space-y-2">
					{#each acl.grants as grant (getGranteeId(grant) + grant.Permission)}
						<div class="flex items-center justify-between rounded-md border px-3 py-2 text-sm">
							<div class="min-w-0">
								<span class="font-medium">{getGranteeName(grant)}</span>
								<span class="ml-1.5 text-xs text-muted-foreground">({getGranteeType(grant)})</span>
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
								<Tooltip.Content side="left" class="max-w-xs">
									{PERMISSION_MAP.get(grant.Permission ?? '')?.description ?? grant.Permission}
								</Tooltip.Content>
							</Tooltip.Root>
						</div>
					{/each}
				</div>
			{:else}
				<p class="text-sm text-muted-foreground">
					No ACL grants configured. Only the bucket owner has access.
				</p>
			{/if}
		</Card.Content>
	{/await}
</Card.Root>

<Dialog.Root bind:open={editOpen}>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Edit Bucket ACL</Dialog.Title>
			<Dialog.Description>
				Each grant gives a specific user or group a permission on this bucket.
			</Dialog.Description>
		</Dialog.Header>

		<div
			class="flex items-start gap-3 rounded-md bg-blue-500/10 p-3 text-sm text-blue-700 dark:text-blue-300"
		>
			<Info class="mt-0.5 h-4 w-4 shrink-0" />
			<div class="space-y-1">
				<p>
					<strong>User (Canonical ID)</strong> — the unique identifier for an HCP user account. Find
					it in the user's profile or via
					<code class="rounded bg-muted px-1 text-xs">GET /userAccounts</code>.
				</p>
				<p>
					<strong>Group (URI)</strong> — a predefined group such as
					<code class="rounded bg-muted px-1 text-xs">AllUsers</code> or
					<code class="rounded bg-muted px-1 text-xs">AuthenticatedUsers</code>.
				</p>
			</div>
		</div>

		<div class="max-h-80 space-y-3 overflow-y-auto">
			{#each editGrants as grant, i (i)}
				<div class="flex items-end gap-2 rounded-md border p-3">
					<div class="min-w-0 flex-1 space-y-2">
						<div class="grid gap-2 sm:grid-cols-2">
							<div class="space-y-1">
								<Label class="text-xs">Grantee Type</Label>
								<select
									class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-8 w-full rounded-md border px-2 text-xs shadow-sm focus:outline-none focus:ring-1"
									bind:value={editGrants[i].type}
								>
									<option value="CanonicalUser">User (Canonical ID)</option>
									<option value="Group">Group (URI)</option>
								</select>
							</div>
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
									class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-8 w-full rounded-md border px-2 text-xs shadow-sm focus:outline-none focus:ring-1"
									bind:value={editGrants[i].permission}
								>
									{#each PERMISSIONS as p (p.value)}
										<option value={p.value}>{p.label}</option>
									{/each}
								</select>
							</div>
						</div>
						<div class="space-y-1">
							<Label class="text-xs">
								{#if grant.type === 'CanonicalUser'}
									User Canonical ID
								{:else}
									Group URI
								{/if}
							</Label>
							<Input
								class="h-8 font-mono text-xs"
								bind:value={editGrants[i].id}
								placeholder={grant.type === 'CanonicalUser'
									? 'HCP user canonical ID (from user profile)'
									: 'e.g. http://acs.amazonaws.com/groups/global/AllUsers'}
							/>
							{#if grant.type === 'CanonicalUser'}
								<p class="text-xs text-muted-foreground">
									The unique ID assigned to each HCP user account.
								</p>
							{:else}
								<p class="text-xs text-muted-foreground">
									Common groups: <code class="rounded bg-muted px-1">AllUsers</code> (public),
									<code class="rounded bg-muted px-1">AuthenticatedUsers</code> (any logged-in user).
								</p>
							{/if}
						</div>
					</div>
					<Button
						variant="ghost"
						size="icon"
						class="h-8 w-8 shrink-0 text-muted-foreground hover:text-destructive"
						onclick={() => removeGrant(i)}
						title="Remove this grant"
					>
						<Trash2 class="h-3.5 w-3.5" />
					</Button>
				</div>
			{/each}
		</div>
		<Button variant="outline" size="sm" onclick={addGrant}>
			<Plus class="h-3.5 w-3.5" />Add Grant
		</Button>
		<Dialog.Footer>
			<Button variant="ghost" onclick={() => (editOpen = false)} disabled={saving}>Cancel</Button>
			<Button onclick={saveAcl} disabled={saving}>
				{#if saving}
					<Loader2 class="h-4 w-4 animate-spin" />
					Saving...
				{:else}
					Save ACL
				{/if}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
