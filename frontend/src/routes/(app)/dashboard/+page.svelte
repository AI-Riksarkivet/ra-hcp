<script lang="ts">
	import { Activity, Database, HardDrive, CheckCircle, XCircle } from 'lucide-svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import { onMount } from 'svelte';

	let { data } = $props();

	let cards: HTMLElement[] = $state([]);

	onMount(async () => {
		const { gsap } = await import('gsap');
		gsap.from(cards.filter(Boolean), {
			y: 20,
			opacity: 0,
			duration: 0.4,
			stagger: 0.1,
			ease: 'power2.out'
		});
	});
</script>

<svelte:head>
	<title>Dashboard - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div>
		<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-100">Dashboard</h2>
		<p class="mt-1 text-sm text-surface-500 dark:text-surface-400">
			Overview of your HCP infrastructure
		</p>
	</div>

	<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
		<div bind:this={cards[0]}>
			<Card>
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-surface-500 dark:text-surface-400">System Status</p>
						<div class="mt-2 flex items-center gap-2">
							{#if data.health.status === 'ok'}
								<CheckCircle class="h-5 w-5 text-emerald-500" />
								<Badge variant="success">Healthy</Badge>
							{:else}
								<XCircle class="h-5 w-5 text-red-500" />
								<Badge variant="danger">Unhealthy</Badge>
							{/if}
						</div>
					</div>
					<div class="rounded-lg bg-primary-50 p-3 dark:bg-primary-900/20">
						<Activity class="h-6 w-6 text-primary-600 dark:text-primary-400" />
					</div>
				</div>
			</Card>
		</div>

		<div bind:this={cards[1]}>
			<Card>
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-surface-500 dark:text-surface-400">Total Buckets</p>
						<p class="mt-2 text-3xl font-bold text-surface-900 dark:text-surface-100">
							{data.buckets.buckets?.length ?? 0}
						</p>
					</div>
					<div class="rounded-lg bg-primary-50 p-3 dark:bg-primary-900/20">
						<Database class="h-6 w-6 text-primary-600 dark:text-primary-400" />
					</div>
				</div>
			</Card>
		</div>

		<div bind:this={cards[2]}>
			<Card>
				<div class="flex items-center justify-between">
					<div>
						<p class="text-sm font-medium text-surface-500 dark:text-surface-400">Storage Owner</p>
						<p class="mt-2 text-lg font-semibold text-surface-900 dark:text-surface-100">
							{data.buckets.owner || 'N/A'}
						</p>
					</div>
					<div class="rounded-lg bg-primary-50 p-3 dark:bg-primary-900/20">
						<HardDrive class="h-6 w-6 text-primary-600 dark:text-primary-400" />
					</div>
				</div>
			</Card>
		</div>
	</div>
</div>
