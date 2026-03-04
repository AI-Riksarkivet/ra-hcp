<script lang="ts">
	import { page } from '$app/state';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import { get_tenant, get_tenant_settings } from '$lib/tenant-info.remote.js';

	let tenant = $derived(page.data.tenant as string | undefined);

	let settingsQuery = $derived(
		tenant ? Promise.all([get_tenant({ tenant }), get_tenant_settings({ tenant })]) : null
	);

	function entries(obj: Record<string, unknown>): [string, unknown][] {
		return Object.entries(obj).filter(([, v]) => v !== null && v !== undefined);
	}

	function formatKey(key: string): string {
		return key.replace(/([A-Z])/g, ' $1').replace(/^./, (s) => s.toUpperCase());
	}

	function formatValue(value: unknown): string {
		if (typeof value === 'boolean') return value ? 'Yes' : 'No';
		if (typeof value === 'number') return value.toLocaleString();
		if (typeof value === 'string') return value || '—';
		if (Array.isArray(value)) return value.join(', ') || '—';
		if (typeof value === 'object' && value !== null) return JSON.stringify(value);
		return '—';
	}
</script>

<svelte:head>
	<title>Settings - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h2 class="text-2xl font-bold">Tenant Settings</h2>
		<p class="mt-1 text-sm text-muted-foreground">View tenant configuration and permissions</p>
	</div>

	{#if settingsQuery}
		{#await settingsQuery}
			<div class="grid gap-6 lg:grid-cols-2">
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
			</div>
		{:then [info, settings]}
			<div class="grid gap-6 lg:grid-cols-2">
				<Card.Root class="animate-in fade-in slide-in-from-bottom-2 duration-300">
					<Card.Header>
						<Card.Title>General</Card.Title>
						<Card.Description>Core tenant configuration</Card.Description>
					</Card.Header>
					<Card.Content>
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
								<dd class="text-sm font-medium">{info.softQuota ?? '—'}</dd>
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
					</Card.Content>
				</Card.Root>

				<Card.Root class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-75">
					<Card.Header>
						<Card.Title>Namespace Defaults</Card.Title>
						<Card.Description>Default settings for new namespaces</Card.Description>
					</Card.Header>
					<Card.Content>
						<dl class="space-y-3">
							{#each entries(settings.namespaceDefaults) as [key, value] (key)}
								<div class="flex justify-between">
									<dt class="text-sm text-muted-foreground">{formatKey(key)}</dt>
									<dd class="text-sm font-medium">{formatValue(value)}</dd>
								</div>
							{/each}
							{#if entries(settings.namespaceDefaults).length === 0}
								<p class="text-sm text-muted-foreground">No namespace defaults configured</p>
							{/if}
						</dl>
					</Card.Content>
				</Card.Root>

				<Card.Root class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-150">
					<Card.Header>
						<Card.Title>Permissions</Card.Title>
						<Card.Description>Tenant-level permission settings</Card.Description>
					</Card.Header>
					<Card.Content>
						<dl class="space-y-3">
							{#each entries(settings.permissions) as [key, value] (key)}
								<div class="flex justify-between">
									<dt class="text-sm text-muted-foreground">{formatKey(key)}</dt>
									<dd>
										{#if typeof value === 'boolean'}
											<Badge variant={value ? 'success' : 'secondary'}
												>{value ? 'Allowed' : 'Denied'}</Badge
											>
										{:else}
											<span class="text-sm font-medium">{formatValue(value)}</span>
										{/if}
									</dd>
								</div>
							{/each}
							{#if entries(settings.permissions).length === 0}
								<p class="text-sm text-muted-foreground">No permissions configured</p>
							{/if}
						</dl>
					</Card.Content>
				</Card.Root>

				<Card.Root class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-200">
					<Card.Header>
						<Card.Title>Contact Info</Card.Title>
						<Card.Description>Tenant administrator contact details</Card.Description>
					</Card.Header>
					<Card.Content>
						<dl class="space-y-3">
							{#each entries(settings.contactInfo) as [key, value] (key)}
								<div class="flex justify-between">
									<dt class="text-sm text-muted-foreground">{formatKey(key)}</dt>
									<dd class="text-sm font-medium">{formatValue(value)}</dd>
								</div>
							{/each}
							{#if entries(settings.contactInfo).length === 0}
								<p class="text-sm text-muted-foreground">No contact info configured</p>
							{/if}
						</dl>
					</Card.Content>
				</Card.Root>
			</div>
		{/await}
	{:else}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to view settings.</p>
		</div>
	{/if}
</div>
