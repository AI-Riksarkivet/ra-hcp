<script lang="ts">
	import { Loader2, Search } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { toast } from 'svelte-sonner';
	import {
		get_buckets,
		get_bucket_acl,
		put_bucket_acl,
		type AclData,
	} from '$lib/buckets.remote.js';
	import { SvelteMap } from 'svelte/reactivity';

	const PERMISSIONS: { value: string; label: string }[] = [
		{ value: 'FULL_CONTROL', label: 'Full Control' },
		{ value: 'READ', label: 'Read' },
		{ value: 'WRITE', label: 'Write' },
		{ value: 'READ_ACP', label: 'Read ACP' },
		{ value: 'WRITE_ACP', label: 'Write ACP' },
	];

	let {
		open = $bindable(false),
	}: {
		open: boolean;
	} = $props();

	let bucketData = get_buckets();
	let buckets = $derived(
		(bucketData.current?.buckets ?? []) as { name: string; creation_date: string }[]
	);

	// Fetch ACL for each bucket
	let bucketAcls = $derived.by(() => {
		const map = new SvelteMap<string, ReturnType<typeof get_bucket_acl>>();
		for (const b of buckets) {
			map.set(b.name, get_bucket_acl({ bucket: b.name }));
		}
		return map;
	});

	let granteeType = $state('CanonicalUser');
	let granteeId = $state('');
	let grantPermission = $state('READ');
	let granting = $state(false);
	let grantBucketSelection = $state<Record<string, boolean>>({});
	let bucketSearch = $state('');

	// Reset state when dialog opens
	$effect(() => {
		if (open) {
			grantBucketSelection = {};
			granteeType = 'CanonicalUser';
			granteeId = '';
			grantPermission = 'READ';
			bucketSearch = '';
		}
	});

	let filteredBuckets = $derived(
		buckets.filter((b) => b.name.toLowerCase().includes(bucketSearch.toLowerCase()))
	);

	let grantBuckets = $derived(
		Object.entries(grantBucketSelection)
			.filter(([, v]) => v)
			.map(([name]) => name)
	);

	let allFilteredSelected = $derived(
		filteredBuckets.length > 0 && filteredBuckets.every((b) => grantBucketSelection[b.name])
	);

	function toggleAllFiltered(checked: boolean) {
		const next = { ...grantBucketSelection };
		for (const b of filteredBuckets) {
			if (checked) {
				next[b.name] = true;
			} else {
				delete next[b.name];
			}
		}
		grantBucketSelection = next;
	}

	function permissionLabel(p: string): string {
		return PERMISSIONS.find((x) => x.value === p)?.label ?? p;
	}

	async function handleGrant() {
		if (grantBuckets.length === 0 || !granteeId) return;
		granting = true;
		try {
			for (const bucketName of grantBuckets) {
				const aclQuery = bucketAcls.get(bucketName);
				const currentAcl = (aclQuery?.current ?? { owner: null, grants: [] }) as AclData;
				const newGrant = {
					Grantee: {
						Type: granteeType,
						...(granteeType === 'CanonicalUser' ? { ID: granteeId } : { URI: granteeId }),
					},
					Permission: grantPermission,
				};
				await put_bucket_acl({
					bucket: bucketName,
					owner: currentAcl.owner
						? { ID: currentAcl.owner.ID, DisplayName: currentAcl.owner.DisplayName }
						: undefined,
					grants: [
						...currentAcl.grants.map((g) => ({
							Grantee: g.Grantee,
							Permission: g.Permission,
						})),
						newGrant,
					],
				});
			}
			toast.success(
				`Granted ${permissionLabel(grantPermission)} to ${grantBuckets.length} bucket(s)`
			);
			open = false;
			granteeId = '';
			grantBucketSelection = {};
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to grant access');
		} finally {
			granting = false;
		}
	}
</script>

<Dialog.Root bind:open>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Grant Access</Dialog.Title>
			<Dialog.Description>
				Add an ACL grant to one or more buckets. The new grant will be appended to each bucket's
				existing ACL.
			</Dialog.Description>
		</Dialog.Header>

		<div class="space-y-4">
			<!-- Bucket selection with search -->
			<div class="space-y-2">
				<Label>Buckets</Label>
				<div class="relative">
					<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
					<Input bind:value={bucketSearch} placeholder="Search buckets..." class="pl-10" />
				</div>
				<div class="max-h-60 space-y-1 overflow-y-auto rounded-md border p-3">
					<div class="mb-1 flex items-center gap-2 border-b pb-2">
						<Checkbox
							checked={allFilteredSelected}
							onCheckedChange={(val) => toggleAllFiltered(!!val)}
						/>
						<span class="text-sm font-medium">
							Select all{bucketSearch
								? ` matching (${filteredBuckets.length})`
								: ` (${buckets.length})`}
						</span>
					</div>
					{#each filteredBuckets as b (b.name)}
						<div class="flex items-center gap-2">
							<Checkbox
								checked={grantBucketSelection[b.name] ?? false}
								onCheckedChange={(val) => {
									grantBucketSelection = { ...grantBucketSelection, [b.name]: !!val };
								}}
							/>
							<span class="text-sm">{b.name}</span>
						</div>
					{/each}
					{#if filteredBuckets.length === 0}
						<p class="py-2 text-center text-sm text-muted-foreground">No buckets match</p>
					{/if}
				</div>
				{#if grantBuckets.length > 0}
					<p class="text-xs text-muted-foreground">
						{grantBuckets.length} bucket(s) selected
					</p>
				{/if}
			</div>

			<!-- Grantee Type -->
			<div class="space-y-2">
				<Label for="grantee-type">Grantee Type</Label>
				<select
					id="grantee-type"
					class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-9 w-full items-center rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
					bind:value={granteeType}
				>
					<option value="CanonicalUser">User (Canonical ID)</option>
					<option value="Group">Group (URI)</option>
				</select>
			</div>

			<!-- Grantee ID -->
			<div class="space-y-2">
				<Label>
					{#if granteeType === 'CanonicalUser'}
						Canonical User ID
					{:else}
						Group URI
					{/if}
				</Label>
				<Input
					bind:value={granteeId}
					placeholder={granteeType === 'CanonicalUser'
						? 'HCP user canonical ID'
						: 'e.g. http://acs.amazonaws.com/groups/global/AllUsers'}
				/>
				{#if granteeType === 'Group'}
					<p class="text-xs text-muted-foreground">
						Common groups: <code class="rounded bg-muted px-1">AllUsers</code> (public),
						<code class="rounded bg-muted px-1">AuthenticatedUsers</code> (any logged-in user).
					</p>
				{/if}
			</div>

			<!-- Permission -->
			<div class="space-y-2">
				<Label for="grant-permission">Permission</Label>
				<select
					id="grant-permission"
					class="border-input bg-background text-foreground ring-offset-background focus:ring-ring flex h-9 w-full items-center rounded-md border px-3 py-2 text-sm shadow-sm focus:outline-none focus:ring-1 disabled:cursor-not-allowed disabled:opacity-50"
					bind:value={grantPermission}
				>
					{#each PERMISSIONS as p (p.value)}
						<option value={p.value}>{p.label}</option>
					{/each}
				</select>
			</div>
		</div>

		<Dialog.Footer>
			<Button variant="ghost" onclick={() => (open = false)} disabled={granting}>Cancel</Button>
			<Button onclick={handleGrant} disabled={granting || grantBuckets.length === 0 || !granteeId}>
				{#if granting}
					<Loader2 class="h-4 w-4 animate-spin" />
					Granting...
				{:else}
					Grant Access
				{/if}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
