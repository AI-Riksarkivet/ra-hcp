<script lang="ts">
	import { page } from '$app/state';
	import * as Collapsible from '$lib/components/ui/collapsible/index.js';
	import { buttonVariants } from '$lib/components/ui/button/index.js';
	import { ChevronsUpDown, Settings2 } from 'lucide-svelte';
	import BackButton from '$lib/components/ui/back-button.svelte';
	import NoTenantPlaceholder from '$lib/components/ui/no-tenant-placeholder.svelte';
	import NsGeneralInfo from './sections/ns-general-info.svelte';
	import NsProtocols from './sections/ns-protocols.svelte';
	import NsFeatures from './sections/ns-features.svelte';
	import NsTags from './sections/ns-tags.svelte';
	import NsUserAccess from './sections/ns-user-access.svelte';
	import NsCompliance from './sections/ns-compliance.svelte';
	import NsRetentionClasses from './sections/ns-retention-classes.svelte';
	import NsIndexing from './sections/ns-indexing.svelte';
	import NsCors from './sections/ns-cors.svelte';
	import NsReplicationCollision from './sections/ns-replication-collision.svelte';

	let tenant = $derived(page.data.tenant as string | undefined);
	let namespaceName = $derived(page.params.namespace ?? '');

	let advancedOpen = $state(false);
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
		<NsGeneralInfo {tenant} {namespaceName} />

		<div class="grid gap-6 lg:grid-cols-3">
			<NsProtocols {tenant} {namespaceName} />
			<NsFeatures {tenant} {namespaceName} />
			<NsTags {tenant} {namespaceName} />
		</div>

		<NsUserAccess {tenant} {namespaceName} />

		<Collapsible.Root bind:open={advancedOpen} class="space-y-4">
			<div class="flex items-center gap-3">
				<Settings2 class="h-5 w-5 text-muted-foreground" />
				<h3 class="text-lg font-semibold">Advanced Settings</h3>
				<Collapsible.Trigger
					class={buttonVariants({ variant: 'ghost', size: 'sm', class: 'h-7 w-7 p-0' })}
				>
					<ChevronsUpDown class="h-4 w-4" />
					<span class="sr-only">Toggle advanced settings</span>
				</Collapsible.Trigger>
			</div>

			<Collapsible.Content class="space-y-6">
				<div class="grid gap-6 lg:grid-cols-3">
					<NsCompliance {tenant} {namespaceName} />
					<NsReplicationCollision {tenant} {namespaceName} />
					<NsRetentionClasses {tenant} {namespaceName} />
				</div>

				<div class="grid gap-6 lg:grid-cols-2">
					<NsIndexing {tenant} {namespaceName} />
					<NsCors {tenant} {namespaceName} />
				</div>
			</Collapsible.Content>
		</Collapsible.Root>
	{/if}
</div>
