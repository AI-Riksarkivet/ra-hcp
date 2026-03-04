<script lang="ts">
	import { page } from '$app/state';
	import {
		Building2,
		Boxes,
		FileBox,
		HardDrive,
		ArrowUpRight,
		ArrowDownRight,
	} from 'lucide-svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import { formatBytes } from '$lib/utils/format.js';
	import { get_tenant, get_tenant_statistics } from '$lib/tenant-info.remote.js';

	let tenant = $derived(page.data.tenant as string | undefined);

	let tenantInfo = $derived(tenant ? get_tenant({ tenant }) : undefined);
	let tenantStats = $derived(tenant ? get_tenant_statistics({ tenant }) : undefined);
</script>

<svelte:head>
	<title>Tenant Overview - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h2 class="text-2xl font-bold">Tenant Overview</h2>
		<p class="mt-1 text-sm text-muted-foreground">Overview of your tenant</p>
	</div>

	{#if tenant}
		<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
			{#await tenantInfo}
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
			{:then info}
				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300">
					<Card.Root>
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-muted-foreground">Tenant Name</p>
									<p class="mt-2 text-2xl font-bold">{info.name}</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<Building2 class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>

				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-75">
					<Card.Root>
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-muted-foreground">Hard Quota</p>
									<p class="mt-2 text-2xl font-bold">{info.hardQuota ?? 'N/A'}</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<ArrowUpRight class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>

				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-150">
					<Card.Root>
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-muted-foreground">Soft Quota</p>
									<p class="mt-2 text-2xl font-bold">{info.softQuota ?? 'N/A'}</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<ArrowDownRight class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>
			{/await}

			{#await tenantStats}
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
			{:then stats}
				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300">
					<Card.Root>
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-muted-foreground">Namespaces</p>
									<p class="mt-2 text-3xl font-bold">{stats.namespacesUsed ?? 0}</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<Boxes class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>

				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-75">
					<Card.Root>
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-muted-foreground">Objects</p>
									<p class="mt-2 text-3xl font-bold">
										{stats.objectCount.toLocaleString()}
									</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<FileBox class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>

				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-150">
					<Card.Root>
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-muted-foreground">Storage Used</p>
									<p class="mt-2 text-3xl font-bold">
										{formatBytes(Number(stats.bytesUsed))}
									</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<HardDrive class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>
			{/await}
		</div>
	{:else}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to view overview.</p>
		</div>
	{/if}
</div>
