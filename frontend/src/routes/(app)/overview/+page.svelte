<script lang="ts">
	import { page } from '$app/state';
	import {
		Boxes,
		FileBox,
		HardDrive,
		Database,
		CheckCircle2,
		XCircle,
		Activity,
		FolderOpen,
	} from 'lucide-svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { formatBytes } from '$lib/utils/format.js';
	import {
		get_tenant,
		get_tenant_statistics,
		get_tenant_chargeback,
	} from '$lib/tenant-info.remote.js';
	import { get_namespaces, type Namespace } from '$lib/namespaces.remote.js';
	import type { ChargebackEntry } from '$lib/tenant-info.remote.js';

	let tenant = $derived(page.data.tenant as string | undefined);

	let tenantInfo = $derived(tenant ? get_tenant({ tenant }) : undefined);
	let tenantStats = $derived(tenant ? get_tenant_statistics({ tenant }) : undefined);
	let namespaceData = $derived(tenant ? get_namespaces({ tenant }) : undefined);
	let chargebackData = $derived(tenant ? get_tenant_chargeback({ tenant }) : undefined);

	let namespaces = $derived((namespaceData?.current ?? []) as Namespace[]);
	let chargeback = $derived((chargebackData?.current?.chargebackData ?? []) as ChargebackEntry[]);

	let quotaPercent = $derived.by(() => {
		const info = tenantInfo?.current;
		const stats = tenantStats?.current;
		if (!info?.hardQuota || !stats?.bytesUsed) return null;
		const quotaMatch = info.hardQuota.match(/([\d.]+)\s*(B|KB|MB|GB|TB|PB)/i);
		if (!quotaMatch) return null;
		const units: Record<string, number> = {
			B: 1,
			KB: 1024,
			MB: 1024 ** 2,
			GB: 1024 ** 3,
			TB: 1024 ** 4,
			PB: 1024 ** 5,
		};
		const quotaBytes = parseFloat(quotaMatch[1]) * (units[quotaMatch[2].toUpperCase()] ?? 1);
		if (quotaBytes <= 0) return null;
		return Math.min(100, (Number(stats.bytesUsed) / quotaBytes) * 100);
	});

	let chargebackTotals = $derived.by(() => {
		let bytesIn = 0;
		let bytesOut = 0;
		let reads = 0;
		let writes = 0;
		let deletes = 0;
		for (const entry of chargeback) {
			bytesIn += entry.bytesIn ?? 0;
			bytesOut += entry.bytesOut ?? 0;
			reads += entry.reads ?? 0;
			writes += entry.writes ?? 0;
			deletes += entry.deletes ?? 0;
		}
		return { bytesIn, bytesOut, reads, writes, deletes };
	});
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
		<!-- Row 1: Summary stat cards -->
		<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
			{#await tenantStats}
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
			{:then stats}
				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300">
					<Card.Root>
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-muted-foreground">Objects</p>
									<p class="mt-2 text-3xl font-bold">
										{(stats?.objectCount ?? 0).toLocaleString()}
									</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<FileBox class="h-6 w-6 text-primary" />
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
									<p class="text-sm font-medium text-muted-foreground">Storage Used</p>
									<p class="mt-2 text-3xl font-bold">
										{formatBytes(Number(stats?.bytesUsed ?? 0))}
									</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<HardDrive class="h-6 w-6 text-primary" />
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
									<p class="text-sm font-medium text-muted-foreground">Namespaces</p>
									<p class="mt-2 text-3xl font-bold">{stats?.namespacesUsed ?? 0}</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<Boxes class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>

				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-200">
					{#await tenantInfo}
						<CardSkeleton />
					{:then info}
						<Card.Root>
							<Card.Content class="pt-6">
								<div class="flex items-center justify-between">
									<div class="min-w-0 flex-1">
										<p class="text-sm font-medium text-muted-foreground">Quota Usage</p>
										{#if quotaPercent !== null}
											<p class="mt-2 text-3xl font-bold">{quotaPercent.toFixed(1)}%</p>
											<div class="mt-2 h-2 w-full overflow-hidden rounded-full bg-muted">
												<div
													class="h-full rounded-full transition-all duration-500 {quotaPercent > 90
														? 'bg-destructive'
														: quotaPercent > 70
															? 'bg-yellow-500'
															: 'bg-primary'}"
													style="width: {quotaPercent}%"
												></div>
											</div>
											<p class="mt-1 text-xs text-muted-foreground">
												{formatBytes(Number(stats?.bytesUsed ?? 0))} / {info?.hardQuota}
											</p>
										{:else}
											<p class="mt-2 text-2xl font-bold">No limit</p>
											<p class="mt-1 text-xs text-muted-foreground">No hard quota set</p>
										{/if}
									</div>
									<div class="ml-4 rounded-lg bg-primary/10 p-3">
										<Database class="h-6 w-6 text-primary" />
									</div>
								</div>
							</Card.Content>
						</Card.Root>
					{/await}
				</div>
			{/await}
		</div>

		<!-- Row 2: Namespace Breakdown -->
		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<FolderOpen class="h-5 w-5 text-muted-foreground" />
					<Card.Title>Namespace Breakdown</Card.Title>
				</div>
				<Card.Description>All namespaces in this tenant</Card.Description>
			</Card.Header>
			<Card.Content>
				{#await namespaceData}
					<TableSkeleton rows={4} columns={4} />
				{:then _}
					{#if namespaces.length === 0}
						<div class="rounded-lg border border-dashed p-8 text-center">
							<p class="text-muted-foreground">No namespaces found.</p>
						</div>
					{:else}
						<div class="overflow-x-auto rounded-lg border">
							<table class="w-full text-left text-sm">
								<thead
									class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground"
								>
									<tr>
										<th class="px-4 py-3 font-medium">Name</th>
										<th class="px-4 py-3 font-medium">Hard Quota</th>
										<th class="px-4 py-3 font-medium">Search</th>
										<th class="px-4 py-3 font-medium">Versioning</th>
									</tr>
								</thead>
								<tbody class="divide-y">
									{#each namespaces as ns (ns.name)}
										<tr class="bg-card transition-colors hover:bg-accent/50">
											<td class="px-4 py-3 font-medium">
												<a
													href="/namespaces/{ns.name}"
													class="text-primary underline-offset-4 hover:underline"
												>
													{ns.name}
												</a>
											</td>
											<td class="px-4 py-3 text-muted-foreground">
												{ns.hardQuota ?? '—'}
											</td>
											<td class="px-4 py-3">
												{#if ns.searchEnabled}
													<CheckCircle2 class="h-4 w-4 text-green-500" />
												{:else}
													<XCircle class="h-4 w-4 text-muted-foreground" />
												{/if}
											</td>
											<td class="px-4 py-3">
												{#if ns.versioningSettings?.enabled}
													<CheckCircle2 class="h-4 w-4 text-green-500" />
												{:else}
													<XCircle class="h-4 w-4 text-muted-foreground" />
												{/if}
											</td>
										</tr>
									{/each}
								</tbody>
							</table>
						</div>
					{/if}
				{/await}
			</Card.Content>
		</Card.Root>

		<!-- Row 3: Activity Summary (Chargeback) -->
		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<Activity class="h-5 w-5 text-muted-foreground" />
					<Card.Title>Activity Summary</Card.Title>
				</div>
				<Card.Description>Per-namespace I/O and operation activity</Card.Description>
			</Card.Header>
			<Card.Content>
				{#await chargebackData}
					<TableSkeleton rows={4} columns={6} />
				{:then _}
					{#if chargeback.length === 0}
						<div class="rounded-lg border border-dashed p-8 text-center">
							<p class="text-muted-foreground">No activity data available.</p>
						</div>
					{:else}
						<div class="overflow-x-auto rounded-lg border">
							<table class="w-full text-left text-sm">
								<thead
									class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground"
								>
									<tr>
										<th class="px-4 py-3 font-medium">Namespace</th>
										<th class="px-4 py-3 text-right font-medium">Bytes In</th>
										<th class="px-4 py-3 text-right font-medium">Bytes Out</th>
										<th class="px-4 py-3 text-right font-medium">Reads</th>
										<th class="px-4 py-3 text-right font-medium">Writes</th>
										<th class="px-4 py-3 text-right font-medium">Deletes</th>
									</tr>
								</thead>
								<tbody class="divide-y">
									{#each chargeback as entry (entry.namespaceName)}
										<tr class="bg-card transition-colors hover:bg-accent/50">
											<td class="px-4 py-3 font-medium">
												{entry.namespaceName ?? '—'}
											</td>
											<td class="px-4 py-3 text-right text-muted-foreground">
												{formatBytes(entry.bytesIn ?? 0)}
											</td>
											<td class="px-4 py-3 text-right text-muted-foreground">
												{formatBytes(entry.bytesOut ?? 0)}
											</td>
											<td class="px-4 py-3 text-right text-muted-foreground">
												{(entry.reads ?? 0).toLocaleString()}
											</td>
											<td class="px-4 py-3 text-right text-muted-foreground">
												{(entry.writes ?? 0).toLocaleString()}
											</td>
											<td class="px-4 py-3 text-right text-muted-foreground">
												{(entry.deletes ?? 0).toLocaleString()}
											</td>
										</tr>
									{/each}
									<tr class="border-t-2 bg-muted/30 font-semibold">
										<td class="px-4 py-3">Total</td>
										<td class="px-4 py-3 text-right">
											{formatBytes(chargebackTotals.bytesIn)}
										</td>
										<td class="px-4 py-3 text-right">
											{formatBytes(chargebackTotals.bytesOut)}
										</td>
										<td class="px-4 py-3 text-right">
											{chargebackTotals.reads.toLocaleString()}
										</td>
										<td class="px-4 py-3 text-right">
											{chargebackTotals.writes.toLocaleString()}
										</td>
										<td class="px-4 py-3 text-right">
											{chargebackTotals.deletes.toLocaleString()}
										</td>
									</tr>
								</tbody>
							</table>
						</div>
					{/if}
				{/await}
			</Card.Content>
		</Card.Root>
	{:else}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to view overview.</p>
		</div>
	{/if}
</div>
