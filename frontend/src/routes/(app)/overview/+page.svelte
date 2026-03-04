<script lang="ts">
	import { page } from '$app/state';
	import { Boxes, FileBox, HardDrive, Activity, Users, ArrowLeftRight } from 'lucide-svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { formatBytes } from '$lib/utils/format.js';
	import {
		get_tenant,
		get_tenant_statistics,
		get_tenant_chargeback,
		type ChargebackEntry,
	} from '$lib/tenant-info.remote.js';
	import { get_users } from '$lib/users.remote.js';

	let tenant = $derived(page.data.tenant as string | undefined);

	let tenantInfo = $derived(tenant ? get_tenant({ tenant }) : undefined);
	let tenantStats = $derived(tenant ? get_tenant_statistics({ tenant }) : undefined);
	let chargebackData = $derived(tenant ? get_tenant_chargeback({ tenant }) : undefined);
	let usersData = $derived(tenant ? get_users({ tenant }) : undefined);

	let chargeback = $derived((chargebackData?.current?.chargebackData ?? []) as ChargebackEntry[]);
	let users = $derived((usersData?.current ?? []) as { username: string }[]);

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

	let sortedChargeback = $derived.by(() => {
		return [...chargeback].sort((a, b) => {
			const opsA = (a.reads ?? 0) + (a.writes ?? 0) + (a.deletes ?? 0);
			const opsB = (b.reads ?? 0) + (b.writes ?? 0) + (b.deletes ?? 0);
			return opsB - opsA;
		});
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

	const MAX_USERS_SHOWN = 8;
	let displayedUsers = $derived(users.slice(0, MAX_USERS_SHOWN));
	let hasMoreUsers = $derived(users.length > MAX_USERS_SHOWN);
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
		<!-- Row 1: Compact stat strip -->
		<div class="grid gap-4 sm:grid-cols-3">
			{#await tenantStats}
				<CardSkeleton />
				<CardSkeleton />
				<CardSkeleton />
			{:then stats}
				<!-- Objects -->
				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300">
					<Card.Root class="h-full">
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-muted-foreground">Objects</p>
									<p class="mt-1 text-2xl font-bold">
										{(stats?.objectCount ?? 0).toLocaleString()}
									</p>
									<p class="mt-1 text-xs text-muted-foreground">
										{stats?.customMetadataObjectCount ?? 0} with custom metadata
									</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<FileBox class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>

				<!-- Storage -->
				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-75">
					<Card.Root class="h-full">
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div class="min-w-0 flex-1">
									<p class="text-sm font-medium text-muted-foreground">Storage</p>
									<p class="mt-1 text-2xl font-bold">
										{formatBytes(Number(stats?.bytesUsed ?? 0))}
									</p>
									{#await tenantInfo then info}
										{#if quotaPercent !== null}
											<div class="mt-2 h-1.5 w-full overflow-hidden rounded-full bg-muted">
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
											<p class="mt-1 text-xs text-muted-foreground">No quota limit</p>
										{/if}
									{/await}
								</div>
								<div class="ml-4 rounded-lg bg-primary/10 p-3">
									<HardDrive class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>

				<!-- Namespaces -->
				<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 delay-150">
					<Card.Root class="h-full">
						<Card.Content class="pt-6">
							<div class="flex items-center justify-between">
								<div>
									<p class="text-sm font-medium text-muted-foreground">Namespaces</p>
									<p class="mt-1 text-2xl font-bold">
										{stats?.namespacesUsed ?? 0}
									</p>
									<p class="mt-1 text-xs">
										<a href="/namespaces" class="text-primary underline-offset-4 hover:underline">
											View all &rarr;
										</a>
									</p>
								</div>
								<div class="rounded-lg bg-primary/10 p-3">
									<Boxes class="h-6 w-6 text-primary" />
								</div>
							</div>
						</Card.Content>
					</Card.Root>
				</div>
			{/await}
		</div>

		<!-- Row 2: Namespace Activity + Users -->
		<div class="grid gap-6 lg:grid-cols-2">
			<!-- Namespace Activity -->
			<Card.Root>
				<Card.Header>
					<div class="flex items-center gap-2">
						<Activity class="h-5 w-5 text-muted-foreground" />
						<Card.Title>Namespace Activity</Card.Title>
					</div>
					<Card.Description>Ranked by total operations</Card.Description>
				</Card.Header>
				<Card.Content>
					{#await chargebackData}
						<TableSkeleton rows={4} columns={5} />
					{:then _}
						{#if sortedChargeback.length === 0}
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
											<th class="px-4 py-3 text-right font-medium">Storage</th>
											<th class="px-4 py-3 text-right font-medium">Ingress</th>
											<th class="px-4 py-3 text-right font-medium">Egress</th>
											<th class="px-4 py-3 text-right font-medium">Ops</th>
										</tr>
									</thead>
									<tbody class="divide-y">
										{#each sortedChargeback as entry (entry.namespaceName)}
											<tr class="bg-card transition-colors hover:bg-accent/50">
												<td class="px-4 py-3 font-medium">
													<a
														href="/namespaces/{entry.namespaceName}"
														class="text-primary underline-offset-4 hover:underline"
													>
														{entry.namespaceName ?? '—'}
													</a>
												</td>
												<td class="px-4 py-3 text-right text-muted-foreground">
													{formatBytes(entry.storageCapacityUsed ?? 0)}
												</td>
												<td class="px-4 py-3 text-right text-muted-foreground">
													{formatBytes(entry.bytesIn ?? 0)}
												</td>
												<td class="px-4 py-3 text-right text-muted-foreground">
													{formatBytes(entry.bytesOut ?? 0)}
												</td>
												<td class="px-4 py-3 text-right text-muted-foreground">
													{(
														(entry.reads ?? 0) +
														(entry.writes ?? 0) +
														(entry.deletes ?? 0)
													).toLocaleString()}
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

			<!-- Users -->
			<Card.Root>
				<Card.Header>
					<div class="flex items-center gap-2">
						<Users class="h-5 w-5 text-muted-foreground" />
						<Card.Title>Users</Card.Title>
						{#await usersData then _}
							<Badge variant="secondary">{users.length}</Badge>
						{/await}
					</div>
					<Card.Description>Tenant user accounts</Card.Description>
				</Card.Header>
				<Card.Content>
					{#await usersData}
						<div class="space-y-3">
							{#each Array(4) as _, i (i)}
								<div class="h-5 w-32 animate-pulse rounded bg-muted"></div>
							{/each}
						</div>
					{:then _}
						{#if users.length === 0}
							<div class="rounded-lg border border-dashed p-8 text-center">
								<p class="text-muted-foreground">No users found.</p>
							</div>
						{:else}
							<ul class="space-y-2">
								{#each displayedUsers as user (user.username)}
									<li>
										<a href="/users/{user.username}" class="text-sm text-primary hover:underline">
											{user.username}
										</a>
									</li>
								{/each}
							</ul>
							{#if hasMoreUsers}
								<p class="mt-4 text-sm">
									<a href="/users" class="text-primary underline-offset-4 hover:underline">
										View all &rarr;
									</a>
								</p>
							{/if}
						{/if}
					{/await}
				</Card.Content>
			</Card.Root>
		</div>

		<!-- Row 3: I/O Summary -->
		<Card.Root>
			<Card.Header>
				<div class="flex items-center gap-2">
					<ArrowLeftRight class="h-5 w-5 text-muted-foreground" />
					<Card.Title>I/O Summary</Card.Title>
				</div>
				<Card.Description>Aggregate data transfer across all namespaces</Card.Description>
			</Card.Header>
			<Card.Content>
				{#await chargebackData}
					<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
						{#each Array(4) as _, i (i)}
							<div class="h-20 animate-pulse rounded-lg border bg-muted"></div>
						{/each}
					</div>
				{:then _}
					<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
						<div class="rounded-lg border p-4">
							<p class="text-xl font-bold">{formatBytes(chargebackTotals.bytesIn)}</p>
							<p class="text-xs text-muted-foreground">Data received</p>
						</div>
						<div class="rounded-lg border p-4">
							<p class="text-xl font-bold">{formatBytes(chargebackTotals.bytesOut)}</p>
							<p class="text-xs text-muted-foreground">Data sent</p>
						</div>
						<div class="rounded-lg border p-4">
							<p class="text-xl font-bold">{chargebackTotals.reads.toLocaleString()}</p>
							<p class="text-xs text-muted-foreground">Read operations</p>
						</div>
						<div class="rounded-lg border p-4">
							<p class="text-xl font-bold">
								{(chargebackTotals.writes + chargebackTotals.deletes).toLocaleString()}
							</p>
							<p class="text-xs text-muted-foreground">Write & delete ops</p>
						</div>
					</div>
				{/await}
			</Card.Content>
		</Card.Root>
	{:else}
		<div class="rounded-lg border border-dashed p-8 text-center">
			<p class="text-muted-foreground">Log in with a tenant to view overview.</p>
		</div>
	{/if}
</div>
