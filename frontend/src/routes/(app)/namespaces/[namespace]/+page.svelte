<script lang="ts">
	import { page } from '$app/state';
	import { SvelteSet } from 'svelte/reactivity';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Save, Loader2, Plus, HelpCircle, Terminal, Copy, Info, X, Pencil } from 'lucide-svelte';
	import ServiceTagBadge from '$lib/components/ui/service-tag-badge.svelte';
	import { toast } from 'svelte-sonner';
	import { formatDate, formatBytes, parseQuotaBytes, getStorageUsed } from '$lib/utils/format.js';
	import type { ChargebackEntry } from '$lib/utils/format.js';
	import { get_tenant_chargeback } from '$lib/tenant-info.remote.js';
	import { PERMISSION_DESCRIPTIONS } from '$lib/constants.js';
	import BackButton from '$lib/components/ui/back-button.svelte';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import StorageProgressBar from '$lib/components/ui/storage-progress-bar.svelte';
	import NoTenantPlaceholder from '$lib/components/ui/no-tenant-placeholder.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import {
		get_namespace,
		get_ns_protocols,
		update_ns_protocol,
		update_namespace,
		update_versioning,
		type Namespace,
		type NsProtocols,
	} from '$lib/namespaces.remote.js';
	import {
		get_users,
		get_user_permissions,
		set_user_permissions,
		type DataAccessPermissions,
	} from '$lib/users.remote.js';

	const PROTOCOL_DESCRIPTIONS: Record<string, string> = {
		httpEnabled: 'Allow unencrypted HTTP access via REST API',
		httpsEnabled: 'Allow encrypted HTTPS access via REST API',
		cifsEnabled: 'Enable Windows file sharing (SMB/CIFS) access',
		nfsEnabled: 'Enable Unix/Linux NFS mount access',
		smtpEnabled: 'Enable email-based object ingestion',
	};

	let tenant = $derived(page.data.tenant as string | undefined);
	let hcpDomain = $derived((page.data.hcpDomain as string) || '');
	let namespaceName = $derived(page.params.namespace ?? '');

	// --- Storage usage from chargeback ---
	let chargebackData = $derived(tenant ? get_tenant_chargeback({ tenant }) : undefined);
	let nsStorageUsed = $derived(
		getStorageUsed(
			(chargebackData?.current?.chargebackData ?? []) as ChargebackEntry[],
			namespaceName
		)
	);

	// --- NFS connection info ---
	let nfsDomain = $derived(hcpDomain ? `nfs.${hcpDomain}` : 'nfs.<hcp-domain>');
	let nfsMountPath = $derived(`/fs/${tenant ?? '<tenant>'}/${namespaceName || '<namespace>'}/data`);
	let nfsMountCommand = $derived(
		`mount -o tcp,vers=3,timeo=600,hard,intr -t nfs ${nfsDomain}:${nfsMountPath} /mnt/${namespaceName || 'hcp-data'}`
	);

	let nfsCopied = $state(false);
	async function copyNfsCommand() {
		await navigator.clipboard.writeText(nfsMountCommand);
		nfsCopied = true;
		setTimeout(() => (nfsCopied = false), 2000);
	}

	// --- Namespace general info ---
	let nsData = $derived(
		tenant && namespaceName ? get_namespace({ tenant, name: namespaceName }) : undefined
	);
	let ns = $derived((nsData?.current ?? null) as Namespace | null);

	// --- Namespace settings (search & versioning) ---
	let nsSyncVersion = $state(0);
	let localSearchEnabled = $state(false);
	let localVersioningEnabled = $state(false);

	$effect(() => {
		const n = ns;
		void nsSyncVersion;
		localSearchEnabled = n?.searchEnabled ?? false;
		localVersioningEnabled = n?.versioningSettings?.enabled ?? false;
	});

	let nsSettingsDirty = $derived(
		localSearchEnabled !== (ns?.searchEnabled ?? false) ||
			localVersioningEnabled !== (ns?.versioningSettings?.enabled ?? false)
	);

	let savingNsSettings = $state(false);

	// --- Protocols ---
	let protocolsData = $derived(
		tenant && namespaceName ? get_ns_protocols({ tenant, name: namespaceName }) : undefined
	);
	let protocols = $derived((protocolsData?.current ?? {}) as NsProtocols);

	let protocolSyncVersion = $state(0);
	let localHttpEnabled = $state(false);
	let localHttpsEnabled = $state(false);
	let localCifsEnabled = $state(false);
	let localNfsEnabled = $state(false);
	let localSmtpEnabled = $state(false);

	$effect(() => {
		const p = protocols;
		void protocolSyncVersion;
		localHttpEnabled = p.httpEnabled ?? false;
		localHttpsEnabled = p.httpsEnabled ?? false;
		localCifsEnabled = p.cifsEnabled ?? false;
		localNfsEnabled = p.nfsEnabled ?? false;
		localSmtpEnabled = p.smtpEnabled ?? false;
	});

	let protocolsDirty = $derived(
		localHttpEnabled !== (protocols.httpEnabled ?? false) ||
			localHttpsEnabled !== (protocols.httpsEnabled ?? false) ||
			localCifsEnabled !== (protocols.cifsEnabled ?? false) ||
			localNfsEnabled !== (protocols.nfsEnabled ?? false) ||
			localSmtpEnabled !== (protocols.smtpEnabled ?? false)
	);

	let savingProtocols = $state(false);

	async function saveProtocols() {
		if (!tenant || !protocolsData) return;
		savingProtocols = true;
		try {
			const changes: Array<{
				protocol: 'http' | 'cifs' | 'nfs' | 'smtp';
				body: Record<string, unknown>;
			}> = [];
			if (
				localHttpEnabled !== (protocols.httpEnabled ?? false) ||
				localHttpsEnabled !== (protocols.httpsEnabled ?? false)
			) {
				changes.push({
					protocol: 'http',
					body: { httpEnabled: localHttpEnabled, httpsEnabled: localHttpsEnabled },
				});
			}
			if (localCifsEnabled !== (protocols.cifsEnabled ?? false)) {
				changes.push({ protocol: 'cifs', body: { cifsEnabled: localCifsEnabled } });
			}
			if (localNfsEnabled !== (protocols.nfsEnabled ?? false)) {
				changes.push({ protocol: 'nfs', body: { nfsEnabled: localNfsEnabled } });
			}
			if (localSmtpEnabled !== (protocols.smtpEnabled ?? false)) {
				changes.push({ protocol: 'smtp', body: { smtpEnabled: localSmtpEnabled } });
			}
			for (let i = 0; i < changes.length; i++) {
				const call = update_ns_protocol({
					tenant,
					name: namespaceName,
					protocol: changes[i].protocol,
					body: changes[i].body,
				});
				if (i === changes.length - 1) {
					await call.updates(protocolsData);
				} else {
					await call;
				}
			}
			protocolSyncVersion++;
			toast.success('Protocols updated');
		} catch {
			toast.error('Failed to update protocols');
		} finally {
			savingProtocols = false;
		}
	}

	async function saveNsSettings() {
		if (!tenant || !nsData) return;
		savingNsSettings = true;
		try {
			if (localSearchEnabled !== (ns?.searchEnabled ?? false)) {
				await update_namespace({
					tenant,
					name: namespaceName,
					body: { searchEnabled: localSearchEnabled },
				});
			}
			if (localVersioningEnabled !== (ns?.versioningSettings?.enabled ?? false)) {
				await update_versioning({
					tenant,
					name: namespaceName,
					enabled: localVersioningEnabled,
				});
			}
			nsSyncVersion++;
			toast.success('Settings updated');
		} catch {
			toast.error('Failed to update settings');
		} finally {
			savingNsSettings = false;
		}
	}

	// --- Tags ---
	let editingTags = $state(false);
	let editTags = $state<string[]>([]);
	let editTagInput = $state('');
	let savingTags = $state(false);

	function startEditTags() {
		editTags = [...(ns?.tags?.tag ?? [])];
		editTagInput = '';
		editingTags = true;
	}

	function addEditTag() {
		const t = editTagInput.trim().toLowerCase();
		if (t && !editTags.includes(t)) {
			editTags = [...editTags, t];
		}
		editTagInput = '';
	}

	function removeEditTag(t: string) {
		editTags = editTags.filter((x) => x !== t);
	}

	function handleEditTagKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addEditTag();
		}
	}

	async function saveTags() {
		if (!tenant || !nsData) return;
		savingTags = true;
		try {
			await update_namespace({
				tenant,
				name: namespaceName,
				body: { tags: { tag: editTags } },
			}).updates(nsData);
			toast.success('Tags updated');
			editingTags = false;
		} catch {
			toast.error('Failed to update tags');
		} finally {
			savingTags = false;
		}
	}

	// --- User Access ---
	const PERMISSION_KEYS = ['READ', 'WRITE', 'DELETE', 'PURGE', 'SEARCH', 'BROWSE'] as const;

	interface UserPermState {
		fullData: DataAccessPermissions;
		permissions: SvelteSet<string>;
		loading: boolean;
		saving: boolean;
		dirty: boolean;
		originalPermissions: SvelteSet<string>;
	}

	let allUsers = $state.raw<Array<{ username: string }>>([]);
	let userPermMap = $state<Record<string, UserPermState>>({});
	let accessLoading = $state(true);
	let accessVersion = $state(0);

	// Users who have at least one permission OR had permissions originally (unsaved removal)
	let usersWithAccess = $derived(
		Object.entries(userPermMap)
			.filter(
				([, entry]) =>
					!entry.loading && (entry.originalPermissions.size > 0 || entry.permissions.size > 0)
			)
			.map(([username]) => username)
	);

	// Users who don't have access yet (for the Grant Access dropdown)
	let usersWithoutAccess = $derived(
		allUsers.filter(
			(u) =>
				!userPermMap[u.username] ||
				userPermMap[u.username].loading ||
				(userPermMap[u.username].permissions.size === 0 &&
					userPermMap[u.username].originalPermissions.size === 0)
		)
	);

	// Load all users and their permissions, filter to those with access
	$effect(() => {
		const currentTenant = tenant;
		const currentNs = namespaceName;
		void accessVersion;
		if (!currentTenant || !currentNs) {
			accessLoading = false;
			return;
		}

		accessLoading = true;
		let cancelled = false;

		(async () => {
			try {
				const fetchedUsers = (await get_users({ tenant: currentTenant })) as Array<{
					username: string;
				}>;
				if (cancelled) return;
				allUsers = fetchedUsers;

				const permResults = await Promise.all(
					fetchedUsers.map(async (user) => {
						try {
							const data = (await get_user_permissions({
								tenant: currentTenant,
								username: user.username,
							})) as DataAccessPermissions;
							const nsEntry = (data.namespacePermission ?? []).find(
								(entry) => entry.namespaceName === currentNs
							);
							const permList = nsEntry?.permissions?.permission ?? [];
							return { username: user.username, fullData: data, permList };
						} catch {
							return {
								username: user.username,
								fullData: {} as DataAccessPermissions,
								permList: [] as string[],
							};
						}
					})
				);

				if (cancelled) return;
				const map: Record<string, UserPermState> = {};
				for (const r of permResults) {
					map[r.username] = {
						fullData: r.fullData,
						permissions: new SvelteSet(r.permList),
						loading: false,
						saving: false,
						dirty: false,
						originalPermissions: new SvelteSet(r.permList),
					};
				}
				userPermMap = map;
			} catch {
				if (cancelled) return;
				userPermMap = {};
			} finally {
				if (!cancelled) accessLoading = false;
			}
		})();

		return () => {
			cancelled = true;
		};
	});

	function toggleUserPerm(username: string, perm: string) {
		const entry = userPermMap[username];
		if (!entry) return;

		const next = new SvelteSet(entry.permissions);
		if (next.has(perm)) {
			next.delete(perm);
		} else {
			next.add(perm);
		}

		const originalPerms = entry.originalPermissions;
		const isDirty =
			next.size !== originalPerms.size || [...next].some((p) => !originalPerms.has(p));

		userPermMap[username] = {
			...entry,
			permissions: next,
			dirty: isDirty,
		};
	}

	async function saveUserPerms(username: string) {
		const entry = userPermMap[username];
		if (!entry || !tenant) return;

		userPermMap[username] = { ...entry, saving: true };

		try {
			const otherNsPerms = (entry.fullData.namespacePermission ?? []).filter(
				(e) => e.namespaceName !== namespaceName
			);

			const updatedBody: DataAccessPermissions = {
				namespacePermission: [
					...otherNsPerms,
					{
						namespaceName,
						permissions: { permission: [...entry.permissions] },
					},
				],
			};

			await set_user_permissions({
				tenant,
				username,
				body: updatedBody as Record<string, unknown>,
			});

			const perms = new SvelteSet(entry.permissions);
			userPermMap[username] = {
				...entry,
				fullData: updatedBody,
				saving: false,
				dirty: false,
				originalPermissions: perms,
			};

			toast.success(`Permissions updated for ${username}`);
		} catch {
			userPermMap[username] = { ...entry, saving: false };
			toast.error(`Failed to update permissions for ${username}`);
		}
	}

	// --- Grant Access dialog ---
	let grantOpen = $state(false);
	let grantUser = $state('');
	let grantPerms = new SvelteSet<string>();
	let granting = $state(false);
	let grantError = $state('');

	function openGrantDialog() {
		grantUser = '';
		grantPerms.clear();
		grantError = '';
		grantOpen = true;
	}

	async function handleGrant(e: SubmitEvent) {
		e.preventDefault();
		if (!tenant || !grantUser || grantPerms.size === 0) return;
		granting = true;
		grantError = '';

		try {
			const existing = userPermMap[grantUser];
			const otherNsPerms = (existing?.fullData.namespacePermission ?? []).filter(
				(e2) => e2.namespaceName !== namespaceName
			);

			const body: DataAccessPermissions = {
				namespacePermission: [
					...otherNsPerms,
					{
						namespaceName,
						permissions: { permission: [...grantPerms] },
					},
				],
			};

			await set_user_permissions({
				tenant,
				username: grantUser,
				body: body as Record<string, unknown>,
			});

			toast.success(`Access granted to ${grantUser}`);
			grantOpen = false;
			// Reload access data
			accessVersion++;
		} catch (err) {
			grantError = err instanceof Error ? err.message : 'Failed to grant access';
		} finally {
			granting = false;
		}
	}

	function toggleGrantPerm(perm: string) {
		if (grantPerms.has(perm)) {
			grantPerms.delete(perm);
		} else {
			grantPerms.add(perm);
		}
	}
</script>

<svelte:head>
	<title>{namespaceName} - Namespace Settings - HCP Admin Console</title>
</svelte:head>

<div class="space-y-8">
	<!-- Header -->
	<div class="flex items-center gap-4">
		<BackButton href="/namespaces" label="Back to namespaces" />
		<div>
			<h2 class="text-2xl font-bold">{namespaceName}</h2>
			<p class="mt-1 text-sm text-muted-foreground">Namespace settings and access control</p>
		</div>
	</div>

	{#if !tenant}
		<NoTenantPlaceholder message="Log in with a tenant to view namespace details." />
	{:else}
		<!-- Section 1: General Info -->
		<section class="space-y-4">
			<h3 class="text-lg font-semibold">General Information</h3>
			{#await nsData}
				<div class="rounded-lg border p-6">
					<div class="grid grid-cols-2 gap-4 sm:grid-cols-3">
						{#each Array(7) as _, i (i)}
							<div class="space-y-1">
								<div class="h-3 w-20 animate-pulse rounded bg-muted"></div>
								<div class="h-4 w-28 animate-pulse rounded bg-muted"></div>
							</div>
						{/each}
					</div>
				</div>
			{:then _}
				<div class="rounded-lg border p-6">
					{#if ns}
						<div class="grid grid-cols-2 gap-x-8 gap-y-4 sm:grid-cols-3">
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Name
								</p>
								<p class="mt-1 text-sm font-medium">{ns.name}</p>
							</div>
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Description
								</p>
								<p class="mt-1 text-sm">{ns.description || '—'}</p>
							</div>
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Hard Quota
								</p>
								<p class="mt-1 text-sm">{ns.hardQuota || '—'}</p>
							</div>
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Soft Quota
								</p>
								<p class="mt-1 text-sm">
									{ns.softQuota != null ? `${ns.softQuota}%` : '—'}
								</p>
							</div>
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Hash Scheme
								</p>
								<p class="mt-1 text-sm">
									{#if ns.hashScheme}
										<Badge variant="secondary">{ns.hashScheme}</Badge>
									{:else}
										—
									{/if}
								</p>
							</div>
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Search
								</p>
								<p class="mt-1 text-sm">
									<Badge variant={ns.searchEnabled ? 'default' : 'outline'}>
										{ns.searchEnabled ? 'Enabled' : 'Disabled'}
									</Badge>
								</p>
							</div>
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Versioning
								</p>
								<p class="mt-1 text-sm">
									<Badge variant={ns.versioningSettings?.enabled ? 'default' : 'outline'}>
										{ns.versioningSettings?.enabled ? 'Enabled' : 'Disabled'}
									</Badge>
								</p>
							</div>
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Owner
								</p>
								<p class="mt-1 text-sm">{ns.owner || '—'}</p>
							</div>
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Created
								</p>
								<p class="mt-1 text-sm">{ns.creationTime ? formatDate(ns.creationTime) : '—'}</p>
							</div>
							<div>
								<p class="text-xs font-medium uppercase tracking-wide text-muted-foreground">
									Storage Used
								</p>
								{#if true}
									{@const quota = ns.hardQuota ? parseQuotaBytes(ns.hardQuota) : null}
									<p class="mt-1 text-sm">
										{formatBytes(nsStorageUsed)}{quota ? ` / ${ns.hardQuota}` : ''}
									</p>
									{#if quota}
										{@const pct = Math.min(100, (nsStorageUsed / quota) * 100)}
										<StorageProgressBar percent={pct} class="mt-1 max-w-32" />
									{/if}
								{/if}
							</div>
						</div>
					{:else}
						<p class="text-center text-sm text-muted-foreground">
							Namespace not found or could not be loaded.
						</p>
					{/if}
				</div>
			{/await}
		</section>

		<!-- Section 2: Protocols, Features & Tags -->
		<div class="grid gap-6 lg:grid-cols-3">
			<section class="space-y-4">
				<h3 class="text-lg font-semibold">Protocols</h3>
				{#await protocolsData}
					<div class="rounded-lg border p-6">
						<div class="flex flex-wrap gap-6">
							{#each Array(5) as _, i (i)}
								<div class="h-5 w-28 animate-pulse rounded bg-muted"></div>
							{/each}
						</div>
					</div>
				{:then _}
					<div class="rounded-lg border p-6">
						<div class="flex flex-wrap gap-x-8 gap-y-4">
							<label class="flex items-center gap-2 text-sm">
								<Switch bind:checked={localHttpEnabled} />
								HTTP
								<Tooltip.Root>
									<Tooltip.Trigger>
										{#snippet child({ props })}
											<span {...props}>
												<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
											</span>
										{/snippet}
									</Tooltip.Trigger>
									<Tooltip.Content side="right">{PROTOCOL_DESCRIPTIONS.httpEnabled}</Tooltip.Content
									>
								</Tooltip.Root>
							</label>
							<label class="flex items-center gap-2 text-sm">
								<Switch bind:checked={localHttpsEnabled} />
								HTTPS
								<Tooltip.Root>
									<Tooltip.Trigger>
										{#snippet child({ props })}
											<span {...props}>
												<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
											</span>
										{/snippet}
									</Tooltip.Trigger>
									<Tooltip.Content side="right"
										>{PROTOCOL_DESCRIPTIONS.httpsEnabled}</Tooltip.Content
									>
								</Tooltip.Root>
							</label>
							<label class="flex items-center gap-2 text-sm">
								<Switch bind:checked={localCifsEnabled} />
								CIFS
								<Tooltip.Root>
									<Tooltip.Trigger>
										{#snippet child({ props })}
											<span {...props}>
												<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
											</span>
										{/snippet}
									</Tooltip.Trigger>
									<Tooltip.Content side="right">{PROTOCOL_DESCRIPTIONS.cifsEnabled}</Tooltip.Content
									>
								</Tooltip.Root>
							</label>
							<label class="flex items-center gap-2 text-sm">
								<Switch bind:checked={localNfsEnabled} />
								NFS
								<Tooltip.Root>
									<Tooltip.Trigger>
										{#snippet child({ props })}
											<span {...props}>
												<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
											</span>
										{/snippet}
									</Tooltip.Trigger>
									<Tooltip.Content side="right">{PROTOCOL_DESCRIPTIONS.nfsEnabled}</Tooltip.Content>
								</Tooltip.Root>
							</label>
							<label class="flex items-center gap-2 text-sm">
								<Switch bind:checked={localSmtpEnabled} />
								SMTP
								<Tooltip.Root>
									<Tooltip.Trigger>
										{#snippet child({ props })}
											<span {...props}>
												<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
											</span>
										{/snippet}
									</Tooltip.Trigger>
									<Tooltip.Content side="right">{PROTOCOL_DESCRIPTIONS.smtpEnabled}</Tooltip.Content
									>
								</Tooltip.Root>
							</label>
						</div>
						<div class="mt-4">
							<SaveButton dirty={protocolsDirty} saving={savingProtocols} onclick={saveProtocols} />
						</div>
					</div>
				{/await}
			</section>

			<!-- Section 3: Features -->
			<section class="space-y-4">
				<h3 class="text-lg font-semibold">Features</h3>
				<div class="rounded-lg border p-6">
					<div class="flex flex-wrap gap-x-8 gap-y-4">
						<label class="flex items-center gap-2 text-sm">
							<Switch bind:checked={localSearchEnabled} />
							Search
							<Tooltip.Root>
								<Tooltip.Trigger>
									{#snippet child({ props })}
										<span {...props}>
											<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
										</span>
									{/snippet}
								</Tooltip.Trigger>
								<Tooltip.Content side="right"
									>Enable metadata query engine indexing for this namespace</Tooltip.Content
								>
							</Tooltip.Root>
						</label>
						<label class="flex items-center gap-2 text-sm">
							<Switch bind:checked={localVersioningEnabled} />
							Versioning
							<Tooltip.Root>
								<Tooltip.Trigger>
									{#snippet child({ props })}
										<span {...props}>
											<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
										</span>
									{/snippet}
								</Tooltip.Trigger>
								<Tooltip.Content side="right"
									>Keep previous versions of objects on update or delete</Tooltip.Content
								>
							</Tooltip.Root>
						</label>
					</div>
					<div class="mt-4">
						<SaveButton
							dirty={nsSettingsDirty}
							saving={savingNsSettings}
							onclick={saveNsSettings}
						/>
					</div>
				</div>
			</section>

			<!-- Tags -->
			<section class="space-y-4">
				<div class="flex items-center gap-2">
					<h3 class="text-lg font-semibold">Tags</h3>
					{#if !editingTags}
						<button
							type="button"
							class="rounded p-0.5 text-muted-foreground transition-colors hover:text-foreground"
							onclick={startEditTags}
						>
							<Pencil class="h-3.5 w-3.5" />
						</button>
					{/if}
				</div>
				<div class="rounded-lg border p-6">
					{#if editingTags}
						<div class="space-y-3">
							<div class="flex gap-2">
								<input
									class="h-8 w-full rounded-md border border-input bg-transparent px-2 text-sm focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
									placeholder="Add tag..."
									bind:value={editTagInput}
									onkeydown={handleEditTagKeydown}
								/>
								<Button variant="secondary" size="sm" class="h-8" onclick={addEditTag}>Add</Button>
							</div>
							{#if editTags.length > 0}
								<div class="flex flex-wrap gap-1.5">
									{#each editTags as t (t)}
										<span class="inline-flex items-center gap-0.5">
											<ServiceTagBadge tag={t} />
											<button
												type="button"
												class="rounded-full p-0.5 text-muted-foreground hover:text-destructive"
												onclick={() => removeEditTag(t)}
											>
												<X class="h-2.5 w-2.5" />
											</button>
										</span>
									{/each}
								</div>
							{:else}
								<p class="text-sm text-muted-foreground">No tags yet</p>
							{/if}
							<div class="flex items-center gap-3">
								<SaveButton dirty={true} saving={savingTags} onclick={saveTags} />
								<Button variant="ghost" size="sm" onclick={() => (editingTags = false)}>
									Cancel
								</Button>
							</div>
						</div>
					{:else if ns?.tags?.tag?.length}
						<div class="flex flex-wrap gap-1.5">
							{#each ns.tags.tag as t (t)}
								<ServiceTagBadge tag={t} />
							{/each}
						</div>
					{:else}
						<p class="text-sm text-muted-foreground">No tags</p>
					{/if}
				</div>
			</section>
		</div>

		<!-- NFS Connection Instructions (shown when NFS is enabled) -->
		{#if localNfsEnabled}
			<section class="space-y-4">
				<h3 class="text-lg font-semibold">NFS Connection</h3>
				<div class="rounded-lg border p-6 space-y-4">
					<div
						class="flex items-start gap-3 rounded-md bg-blue-500/10 p-3 text-sm text-blue-700 dark:text-blue-300"
					>
						<Info class="mt-0.5 h-4 w-4 shrink-0" />
						<p>
							NFS uses <strong>IP-based access control</strong> — no username or password is needed to
							mount. Access is restricted by the IP settings configured in the NFS protocol section. Make
							sure your client's IP is allowed before attempting to mount.
						</p>
					</div>

					<div>
						<p class="mb-2 text-sm font-medium">Mount command</p>
						<div class="group relative">
							<pre class="overflow-x-auto rounded-md bg-muted p-3 text-sm"><code
									>{nfsMountCommand}</code
								></pre>
							<button
								type="button"
								onclick={copyNfsCommand}
								class="absolute right-2 top-2 rounded-md p-1.5 text-muted-foreground opacity-0 transition-opacity hover:bg-accent group-hover:opacity-100"
								title="Copy to clipboard"
							>
								{#if nfsCopied}
									<span class="text-xs text-green-600">Copied!</span>
								{:else}
									<Copy class="h-4 w-4" />
								{/if}
							</button>
						</div>
					</div>

					<div class="grid gap-4 sm:grid-cols-2">
						<div>
							<p class="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
								Mount data directory
							</p>
							<code class="text-sm">{nfsDomain}:{nfsMountPath}</code>
						</div>
						<div>
							<p class="mb-1 text-xs font-medium uppercase tracking-wide text-muted-foreground">
								Mount metadata directory
							</p>
							<code class="text-sm">{nfsDomain}:/fs/{tenant}/{namespaceName}/metadata</code>
						</div>
					</div>

					<details class="text-sm">
						<summary class="cursor-pointer font-medium text-muted-foreground hover:text-foreground">
							<Terminal class="mr-1 inline h-4 w-4" /> Usage examples & tips
						</summary>
						<div class="mt-3 space-y-3 pl-1">
							<div>
								<p class="font-medium">Store an object</p>
								<pre class="mt-1 overflow-x-auto rounded-md bg-muted p-2"><code
										>cp myfile.txt /mnt/{namespaceName}/myfile.txt</code
									></pre>
							</div>
							<div>
								<p class="font-medium">Retrieve an object</p>
								<pre class="mt-1 overflow-x-auto rounded-md bg-muted p-2"><code
										>cp /mnt/{namespaceName}/myfile.txt ./local-copy.txt</code
									></pre>
							</div>
							<div>
								<p class="font-medium">Tips</p>
								<ul class="ml-4 mt-1 list-disc space-y-1 text-muted-foreground">
									<li>
										Do not specify <code>rsize</code> or <code>wsize</code> — HCP uses optimal values
										automatically
									</li>
									<li>Use <code>lookupcache=none</code> if you see stale file handle errors</li>
									<li>NFS uses lazy close — files are finalized after a short idle period</li>
									<li>Objects are immutable once closed (WORM) — you cannot overwrite or rename</li>
									<li>Multiple threads can read the same object on the same or different nodes</li>
								</ul>
							</div>
						</div>
					</details>
				</div>
			</section>
		{/if}

		<!-- Section 3: User Access -->
		<section class="space-y-4">
			<div class="flex items-center justify-between">
				<h3 class="text-lg font-semibold">User Access</h3>
				<div class="flex items-center gap-3">
					<a href="/users" class="text-sm text-primary underline-offset-4 hover:underline">
						Manage users
					</a>
					<Button size="sm" onclick={openGrantDialog} disabled={accessLoading}>
						<Plus class="h-4 w-4" />
						Grant Access
					</Button>
				</div>
			</div>
			{#if accessLoading}
				<TableSkeleton rows={4} columns={8} />
			{:else if usersWithAccess.length === 0}
				<div class="rounded-lg border border-dashed p-8 text-center">
					<p class="text-muted-foreground">
						No users have access to this namespace. Click "Grant Access" to add users.
					</p>
				</div>
			{:else}
				<div class="overflow-x-auto rounded-lg border">
					<table class="w-full text-left text-sm">
						<thead
							class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground"
						>
							<tr>
								<th class="px-4 py-3 font-medium">Username</th>
								{#each PERMISSION_KEYS as perm (perm)}
									<th class="px-3 py-3 text-center font-medium">
										<div class="flex items-center justify-center gap-1">
											{perm}
											{#if PERMISSION_DESCRIPTIONS[perm]}
												<Tooltip.Root>
													<Tooltip.Trigger>
														{#snippet child({ props })}
															<span {...props}>
																<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
															</span>
														{/snippet}
													</Tooltip.Trigger>
													<Tooltip.Content side="bottom"
														>{PERMISSION_DESCRIPTIONS[perm]}</Tooltip.Content
													>
												</Tooltip.Root>
											{/if}
										</div>
									</th>
								{/each}
								<th class="w-24 px-3 py-3 text-center font-medium">Actions</th>
							</tr>
						</thead>
						<tbody class="divide-y">
							{#each usersWithAccess as username (username)}
								{@const entry = userPermMap[username]}
								<tr class="bg-card transition-colors hover:bg-accent/50">
									<td class="px-4 py-3 font-medium">
										<a
											href="/users/{username}"
											class="text-primary underline-offset-4 hover:underline"
										>
											{username}
										</a>
									</td>
									{#each PERMISSION_KEYS as perm (perm)}
										<td class="px-3 py-3 text-center">
											<Checkbox
												checked={entry?.permissions.has(perm) ?? false}
												onCheckedChange={() => toggleUserPerm(username, perm)}
												disabled={entry?.saving ?? false}
											/>
										</td>
									{/each}
									<td class="px-3 py-3 text-center">
										<Button
											variant="ghost"
											size="sm"
											disabled={!entry?.dirty || entry?.saving}
											onclick={() => saveUserPerms(username)}
										>
											{#if entry?.saving}
												<Loader2 class="h-3.5 w-3.5 animate-spin" />
											{:else}
												<Save class="h-3.5 w-3.5" />
											{/if}
										</Button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</section>
	{/if}
</div>

<!-- Grant Access Dialog -->
<Dialog.Root bind:open={grantOpen}>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Grant Access</Dialog.Title>
			<Dialog.Description
				>Grant a user access to the "{namespaceName}" namespace.</Dialog.Description
			>
		</Dialog.Header>
		<form onsubmit={handleGrant} class="space-y-4">
			{#if grantError}
				<div
					class="rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
				>
					{grantError}
				</div>
			{/if}
			<div class="space-y-2">
				<Label>User</Label>
				<Select.Root type="single" bind:value={grantUser}>
					<Select.Trigger>
						{grantUser || 'Select a user...'}
					</Select.Trigger>
					<Select.Content>
						{#each usersWithoutAccess as user (user.username)}
							<Select.Item value={user.username}>{user.username}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
			</div>
			<div class="space-y-2">
				<Label>Permissions</Label>
				<div class="flex flex-wrap gap-4">
					{#each PERMISSION_KEYS as perm (perm)}
						<label class="flex items-center gap-2 text-sm">
							<Checkbox
								checked={grantPerms.has(perm)}
								onCheckedChange={() => toggleGrantPerm(perm)}
							/>
							{perm}
							{#if PERMISSION_DESCRIPTIONS[perm]}
								<Tooltip.Root>
									<Tooltip.Trigger>
										{#snippet child({ props })}
											<span {...props}>
												<HelpCircle class="h-3.5 w-3.5 text-muted-foreground" />
											</span>
										{/snippet}
									</Tooltip.Trigger>
									<Tooltip.Content side="right">{PERMISSION_DESCRIPTIONS[perm]}</Tooltip.Content>
								</Tooltip.Root>
							{/if}
						</label>
					{/each}
				</div>
			</div>
			<Dialog.Footer>
				<Button variant="ghost" type="button" onclick={() => (grantOpen = false)}>Cancel</Button>
				<Button type="submit" disabled={granting || !grantUser || grantPerms.size === 0}
					>{granting ? 'Granting...' : 'Grant Access'}</Button
				>
			</Dialog.Footer>
		</form>
	</Dialog.Content>
</Dialog.Root>
