<script lang="ts">
	import { page } from '$app/state';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { HelpCircle } from 'lucide-svelte';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { toast } from 'svelte-sonner';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import PageHeader from '$lib/components/ui/page-header.svelte';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import NoTenantPlaceholder from '$lib/components/ui/no-tenant-placeholder.svelte';
	import {
		get_tenant,
		get_tenant_settings,
		update_contact_info,
		update_namespace_defaults,
		update_permissions,
		type TenantInfo,
		type TenantSettings,
	} from '$lib/tenant-info.remote.js';

	let tenant = $derived(page.data.tenant as string | undefined);

	let tenantData = $derived(tenant ? get_tenant({ tenant }) : undefined);
	let settingsData = $derived(tenant ? get_tenant_settings({ tenant }) : undefined);

	let info = $derived((tenantData?.current ?? null) as TenantInfo | null);
	let settings = $derived((settingsData?.current ?? null) as TenantSettings | null);

	// ---- Contact Info local state ----
	let contactSyncVersion = $state(0);
	let localContactName = $state('');
	let localContactEmail = $state('');
	let localContactPhone = $state('');

	$effect(() => {
		const s = settings;
		void contactSyncVersion;
		localContactName = (s?.contactInfo?.name as string) ?? '';
		localContactEmail = (s?.contactInfo?.email as string) ?? '';
		localContactPhone = (s?.contactInfo?.phone as string) ?? '';
	});

	let contactDirty = $derived(
		localContactName !== ((settings?.contactInfo?.name as string) ?? '') ||
			localContactEmail !== ((settings?.contactInfo?.email as string) ?? '') ||
			localContactPhone !== ((settings?.contactInfo?.phone as string) ?? '')
	);

	let savingContact = $state(false);

	async function saveContactInfo() {
		if (!tenant || !settingsData) return;
		savingContact = true;
		try {
			await update_contact_info({
				tenant,
				body: {
					name: localContactName,
					email: localContactEmail,
					phone: localContactPhone,
				},
			}).updates(settingsData);
			contactSyncVersion++;
			toast.success('Contact info updated successfully');
		} catch {
			toast.error('Failed to update contact info');
		} finally {
			savingContact = false;
		}
	}

	// ---- Namespace Defaults local state ----
	let nsSyncVersion = $state(0);
	let localHardQuota = $state('');
	let localSoftQuota = $state('');
	let localOptimizedFor = $state('');
	let localHashScheme = $state('');
	let localSearchEnabled = $state(false);
	let localVersioningEnabled = $state(false);

	$effect(() => {
		const s = settings;
		void nsSyncVersion;
		localHardQuota = (s?.namespaceDefaults?.hardQuota as string) ?? '';
		localSoftQuota = (s?.namespaceDefaults?.softQuota as string) ?? '';
		localOptimizedFor = (s?.namespaceDefaults?.optimizedFor as string) ?? '';
		localHashScheme = (s?.namespaceDefaults?.hashScheme as string) ?? '';
		localSearchEnabled = (s?.namespaceDefaults?.searchEnabled as boolean) ?? false;
		localVersioningEnabled = (s?.namespaceDefaults?.versioningEnabled as boolean) ?? false;
	});

	let nsDirty = $derived(
		localHardQuota !== ((settings?.namespaceDefaults?.hardQuota as string) ?? '') ||
			localSoftQuota !== ((settings?.namespaceDefaults?.softQuota as string) ?? '') ||
			localOptimizedFor !== ((settings?.namespaceDefaults?.optimizedFor as string) ?? '') ||
			localHashScheme !== ((settings?.namespaceDefaults?.hashScheme as string) ?? '') ||
			localSearchEnabled !== ((settings?.namespaceDefaults?.searchEnabled as boolean) ?? false) ||
			localVersioningEnabled !==
				((settings?.namespaceDefaults?.versioningEnabled as boolean) ?? false)
	);

	let savingNs = $state(false);

	async function saveNamespaceDefaults() {
		if (!tenant || !settingsData) return;
		savingNs = true;
		try {
			await update_namespace_defaults({
				tenant,
				body: {
					hardQuota: localHardQuota,
					softQuota: localSoftQuota,
					optimizedFor: localOptimizedFor,
					hashScheme: localHashScheme,
					searchEnabled: localSearchEnabled,
					versioningEnabled: localVersioningEnabled,
				},
			}).updates(settingsData);
			nsSyncVersion++;
			toast.success('Namespace defaults updated successfully');
		} catch {
			toast.error('Failed to update namespace defaults');
		} finally {
			savingNs = false;
		}
	}

	// ---- Permissions local state ----
	const PERMISSION_KEYS = [
		'namespaceCreateAllowed',
		'namespaceDeleteAllowed',
		'namespaceManageAllowed',
		'namespaceUndeleteAllowed',
		'erasureCodingAllowed',
		'searchAllowed',
		'replicationAllowed',
		'complianceAllowed',
		'taggingAllowed',
	] as const;

	const PERMISSION_DESCRIPTIONS: Record<string, string> = {
		namespaceCreateAllowed: 'Allow tenant users to create new namespaces',
		namespaceDeleteAllowed: 'Allow tenant users to delete namespaces',
		namespaceManageAllowed: 'Allow tenant users to modify namespace settings',
		namespaceUndeleteAllowed: 'Allow recovery of deleted namespaces',
		erasureCodingAllowed: 'Enable erasure coding for storage efficiency',
		searchAllowed: 'Allow use of HCP metadata search engine',
		replicationAllowed: 'Allow namespace data replication',
		complianceAllowed: 'Allow configuration of compliance and retention policies',
		taggingAllowed: 'Allow tagging of namespaces and objects',
	};

	let permSyncVersion = $state(0);
	let localPermissions = $state<Record<string, boolean>>({});

	$effect(() => {
		const s = settings;
		void permSyncVersion;
		const perms: Record<string, boolean> = {};
		for (const key of PERMISSION_KEYS) {
			perms[key] = (s?.permissions?.[key] as boolean) ?? false;
		}
		localPermissions = perms;
	});

	let permDirty = $derived(
		PERMISSION_KEYS.some(
			(key) =>
				(localPermissions[key] ?? false) !== ((settings?.permissions?.[key] as boolean) ?? false)
		)
	);

	let savingPerm = $state(false);

	async function savePermissions() {
		if (!tenant || !settingsData) return;
		savingPerm = true;
		try {
			await update_permissions({
				tenant,
				body: { ...localPermissions },
			}).updates(settingsData);
			permSyncVersion++;
			toast.success('Permissions updated successfully');
		} catch {
			toast.error('Failed to update permissions');
		} finally {
			savingPerm = false;
		}
	}

	function togglePermission(key: string) {
		localPermissions = { ...localPermissions, [key]: !localPermissions[key] };
	}

	function formatKey(key: string): string {
		return key.replace(/([A-Z])/g, ' $1').replace(/^./, (s) => s.toUpperCase());
	}
</script>

<svelte:head>
	<title>Settings - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<PageHeader
		title="Tenant Settings"
		description="View and manage tenant configuration and permissions"
	/>

	{#if tenant}
		{#if !tenantData || !settingsData}
			<div class="grid gap-6 lg:grid-cols-2">
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
			</div>
		{:else}
			{#await Promise.all([tenantData, settingsData])}
				<div class="grid gap-6 lg:grid-cols-2">
					<CardSkeleton />
					<CardSkeleton />
					<CardSkeleton />
					<CardSkeleton />
				</div>
			{:then _}
				<div class="grid gap-6 lg:grid-cols-2">
					<!-- General Card (read-only) -->
					<Card.Root class="animate-in fade-in slide-in-from-bottom-2 duration-300">
						<Card.Header>
							<Card.Title>General</Card.Title>
							<Card.Description>Core tenant configuration</Card.Description>
						</Card.Header>
						<Card.Content>
							{#if info}
								<dl class="space-y-3">
									<div class="flex justify-between">
										<dt class="text-sm text-muted-foreground">Tenant Name</dt>
										<dd class="text-sm font-medium">{info.name}</dd>
									</div>
									<div class="flex justify-between">
										<dt class="text-sm text-muted-foreground">Namespace Quota</dt>
										<dd class="text-sm font-medium">{info.namespaceQuota ?? '—'}</dd>
									</div>
									<div class="flex justify-between">
										<dt class="text-sm text-muted-foreground">Hard Quota</dt>
										<dd class="text-sm font-medium">{info.hardQuota ?? '—'}</dd>
									</div>
									<div class="flex justify-between">
										<dt class="text-sm text-muted-foreground">Soft Quota</dt>
										<dd class="text-sm font-medium">
											{info.softQuota != null ? `${info.softQuota}%` : '—'}
										</dd>
									</div>
									<div class="flex justify-between">
										<dt class="text-sm text-muted-foreground">Authentication</dt>
										<dd class="flex gap-1">
											{#each info.authenticationTypes?.authenticationType ?? [] as type (type)}
												<Badge variant="secondary">{type}</Badge>
											{/each}
											{#if !info.authenticationTypes?.authenticationType?.length}
												<span class="text-sm text-muted-foreground">—</span>
											{/if}
										</dd>
									</div>
									<div class="flex justify-between">
										<dt class="text-sm text-muted-foreground">Service Plan</dt>
										<dd class="text-sm font-medium">{info.servicePlan ?? '—'}</dd>
									</div>
								</dl>
							{/if}
						</Card.Content>
					</Card.Root>

					<!-- Contact Info Card (editable) -->
					<Card.Root class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-75">
						<Card.Header>
							<Card.Title>Contact Info</Card.Title>
							<Card.Description>Tenant administrator contact details</Card.Description>
						</Card.Header>
						<Card.Content>
							{#if settings}
								<div class="space-y-4">
									<div class="space-y-2">
										<Label for="contact-name">Name</Label>
										<Input
											id="contact-name"
											bind:value={localContactName}
											placeholder="Contact name"
										/>
									</div>
									<div class="space-y-2">
										<Label for="contact-email">Email</Label>
										<Input
											id="contact-email"
											type="email"
											bind:value={localContactEmail}
											placeholder="admin@example.com"
										/>
									</div>
									<div class="space-y-2">
										<Label for="contact-phone">Phone</Label>
										<Input
											id="contact-phone"
											type="tel"
											bind:value={localContactPhone}
											placeholder="+1 (555) 000-0000"
										/>
									</div>
									<SaveButton
										dirty={contactDirty}
										saving={savingContact}
										onclick={saveContactInfo}
									/>
								</div>
							{/if}
						</Card.Content>
					</Card.Root>

					<!-- Namespace Defaults Card (editable) -->
					<Card.Root class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-150">
						<Card.Header>
							<Card.Title>Namespace Defaults</Card.Title>
							<Card.Description>Default settings for new namespaces</Card.Description>
						</Card.Header>
						<Card.Content>
							{#if settings}
								<div class="space-y-4">
									<div class="grid gap-4 sm:grid-cols-2">
										<div class="space-y-2">
											<Label for="ns-hard-quota">Hard Quota</Label>
											<Input
												id="ns-hard-quota"
												bind:value={localHardQuota}
												placeholder="e.g. 10 GB"
											/>
										</div>
										<div class="space-y-2">
											<Label for="ns-soft-quota">Soft Quota</Label>
											<Input id="ns-soft-quota" bind:value={localSoftQuota} placeholder="e.g. 85" />
										</div>
										<div class="space-y-2">
											<Label>Optimized For</Label>
											<Select.Root type="single" bind:value={localOptimizedFor}>
												<Select.Trigger class="w-full">
													{localOptimizedFor || 'Select...'}
												</Select.Trigger>
												<Select.Content>
													<Select.Item value="CLOUD">CLOUD</Select.Item>
													<Select.Item value="DEFAULT">DEFAULT</Select.Item>
												</Select.Content>
											</Select.Root>
										</div>
										<div class="space-y-2">
											<Label>Hash Scheme</Label>
											<Select.Root type="single" bind:value={localHashScheme}>
												<Select.Trigger class="w-full">
													{localHashScheme || 'Select...'}
												</Select.Trigger>
												<Select.Content>
													<Select.Item value="MD5">MD5</Select.Item>
													<Select.Item value="SHA-256">SHA-256</Select.Item>
													<Select.Item value="SHA-384">SHA-384</Select.Item>
													<Select.Item value="SHA-512">SHA-512</Select.Item>
												</Select.Content>
											</Select.Root>
										</div>
									</div>
									<div class="flex flex-wrap gap-x-8 gap-y-4">
										<div class="flex items-center gap-2">
											<Switch id="ns-search" bind:checked={localSearchEnabled} />
											<Label for="ns-search" class="text-sm">Search Enabled</Label>
										</div>
										<div class="flex items-center gap-2">
											<Switch id="ns-versioning" bind:checked={localVersioningEnabled} />
											<Label for="ns-versioning" class="text-sm">Versioning Enabled</Label>
										</div>
									</div>
									<SaveButton dirty={nsDirty} saving={savingNs} onclick={saveNamespaceDefaults} />
								</div>
							{/if}
						</Card.Content>
					</Card.Root>

					<!-- Permissions Card (editable) -->
					<Card.Root class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-200">
						<Card.Header>
							<Card.Title>Permissions</Card.Title>
							<Card.Description>Tenant-level permission settings</Card.Description>
						</Card.Header>
						<Card.Content>
							{#if settings}
								<div class="space-y-4">
									<div class="space-y-3">
										{#each PERMISSION_KEYS as key (key)}
											<div class="flex items-center justify-between">
												<span class="flex items-center gap-1.5 text-sm text-muted-foreground">
													{formatKey(key)}
													<Tooltip.Root>
														<Tooltip.Trigger>
															{#snippet child({ props })}
																<span {...props} class="inline-flex">
																	<HelpCircle class="h-3.5 w-3.5" />
																</span>
															{/snippet}
														</Tooltip.Trigger>
														<Tooltip.Content side="left"
															>{PERMISSION_DESCRIPTIONS[key]}</Tooltip.Content
														>
													</Tooltip.Root>
												</span>
												<Switch
													checked={localPermissions[key] ?? false}
													onCheckedChange={() => togglePermission(key)}
												/>
											</div>
										{/each}
									</div>
									<SaveButton dirty={permDirty} saving={savingPerm} onclick={savePermissions} />
								</div>
							{/if}
						</Card.Content>
					</Card.Root>
				</div>
			{/await}
		{/if}
	{:else}
		<NoTenantPlaceholder message="Log in with a tenant to view settings." />
	{/if}
</div>
