<script lang="ts">
	import { page } from '$app/state';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import { Database, Settings2 } from 'lucide-svelte';
	import BackButton from '$lib/components/custom/back-button/back-button.svelte';
	import NoTenantPlaceholder from '$lib/components/custom/no-tenant-placeholder/no-tenant-placeholder.svelte';
	import NsGeneralInfo from './sections/ns-general-info.svelte';
	import NsProtocols from './sections/ns-protocols.svelte';
	import NsFeatures from './sections/ns-features.svelte';
	import NsTags from './sections/ns-tags.svelte';
	import NsUserAccess from './sections/ns-user-access.svelte';
	import NsChargeback from './sections/ns-chargeback.svelte';
	import NsCompliance from './sections/ns-compliance.svelte';
	import NsVersioning from './sections/ns-versioning.svelte';
	import NsRetentionClasses from './sections/ns-retention-classes.svelte';
	import NsIndexing from './sections/ns-indexing.svelte';
	import NsCors from './sections/ns-cors.svelte';
	import NsReplicationCollision from './sections/ns-replication-collision.svelte';

	let tenant = $derived(page.data.tenant as string | undefined);
	let namespaceName = $derived(page.params.namespace ?? '');

	let activeTab = $state('namespace');
</script>

<svelte:head>
	<title>{namespaceName} - Namespace Settings - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
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
		<Tabs.Root bind:value={activeTab}>
			<Tabs.List>
				<Tabs.Trigger value="namespace">
					<Database class="mr-1.5 h-4 w-4" />
					Namespace
				</Tabs.Trigger>
				<Tabs.Trigger value="settings">
					<Settings2 class="mr-1.5 h-4 w-4" />
					Settings
				</Tabs.Trigger>
			</Tabs.List>

			<Tabs.Content value="namespace" class="space-y-6">
				<NsGeneralInfo {tenant} {namespaceName} />
				<NsChargeback {tenant} {namespaceName} />
				<NsUserAccess {tenant} {namespaceName} />
			</Tabs.Content>

			<Tabs.Content value="settings" class="space-y-6">
				<div class="grid items-stretch gap-6 lg:grid-cols-3">
					<NsProtocols {tenant} {namespaceName} />
					<NsFeatures {tenant} {namespaceName} />
					<NsTags {tenant} {namespaceName} />
				</div>

				<div class="grid items-stretch gap-6 lg:grid-cols-3">
					<NsCompliance {tenant} {namespaceName} />
					<NsVersioning {tenant} {namespaceName} />
					<NsRetentionClasses {tenant} {namespaceName} />
				</div>

				<div class="grid items-stretch gap-6 lg:grid-cols-3">
					<NsIndexing {tenant} {namespaceName} />
					<NsCors {tenant} {namespaceName} />
					<NsReplicationCollision {tenant} {namespaceName} />
				</div>
			</Tabs.Content>
		</Tabs.Root>
	{/if}
</div>
