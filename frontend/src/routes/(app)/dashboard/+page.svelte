<script lang="ts">
	import { Activity, Database, HardDrive, CheckCircle, XCircle } from 'lucide-svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import { onMount } from 'svelte';
	import { get_health } from '$lib/health.remote.js';
	import { get_buckets } from '$lib/buckets.remote.js';

	let cards: HTMLElement[] = $state([]);

	onMount(async () => {
		const { gsap } = await import('gsap');
		gsap.from(cards.filter(Boolean), {
			y: 20,
			opacity: 0,
			duration: 0.4,
			stagger: 0.1,
			ease: 'power2.out',
		});
	});
</script>

<svelte:head>
	<title>Dashboard - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h2 class="text-2xl font-bold">Dashboard</h2>
		<p class="mt-1 text-sm text-muted-foreground">Overview of your HCP infrastructure</p>
	</div>

	<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
		{#await get_health()}
			<CardSkeleton />
		{:then health}
			<div bind:this={cards[0]}>
				<Card.Root>
					<Card.Content class="pt-6">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-sm font-medium text-muted-foreground">System Status</p>
								<div class="mt-2 flex items-center gap-2">
									{#if health.status === 'ok'}
										<CheckCircle class="h-5 w-5 text-emerald-500" />
										<Badge variant="success">Healthy</Badge>
									{:else}
										<XCircle class="h-5 w-5 text-red-500" />
										<Badge variant="destructive">Unhealthy</Badge>
									{/if}
								</div>
							</div>
							<div class="rounded-lg bg-primary/10 p-3">
								<Activity class="h-6 w-6 text-primary" />
							</div>
						</div>
					</Card.Content>
				</Card.Root>
			</div>
		{/await}

		{#await get_buckets()}
			<CardSkeleton />
			<CardSkeleton />
		{:then buckets}
			<div bind:this={cards[1]}>
				<Card.Root>
					<Card.Content class="pt-6">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-sm font-medium text-muted-foreground">Total Buckets</p>
								<p class="mt-2 text-3xl font-bold">
									{buckets.buckets?.length ?? 0}
								</p>
							</div>
							<div class="rounded-lg bg-primary/10 p-3">
								<Database class="h-6 w-6 text-primary" />
							</div>
						</div>
					</Card.Content>
				</Card.Root>
			</div>

			<div bind:this={cards[2]}>
				<Card.Root>
					<Card.Content class="pt-6">
						<div class="flex items-center justify-between">
							<div>
								<p class="text-sm font-medium text-muted-foreground">Storage Owner</p>
								<p class="mt-2 text-lg font-semibold">
									{buckets.owner || 'N/A'}
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
</div>
