<script lang="ts">
	import { ArrowDownToLine, ArrowUpFromLine, Eye, PenLine } from 'lucide-svelte';
	import StatCard from '$lib/components/ui/stat-card.svelte';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import { formatBytes } from '$lib/utils/format.js';
	import type { ChargebackEntry } from '$lib/utils/format.js';
	import { get_ns_chargeback } from '$lib/remote/namespaces.remote.js';

	let {
		tenant,
		namespaceName,
	}: {
		tenant: string;
		namespaceName: string;
	} = $props();

	let chargebackData = $derived(
		get_ns_chargeback({ tenant, name: namespaceName, granularity: 'day' })
	);

	let entries = $derived(
		((chargebackData?.current?.chargebackData ?? []) as ChargebackEntry[]).filter(
			(e) => e.startTime
		)
	);

	function sumField(field: keyof ChargebackEntry): number {
		return entries.reduce((acc, e) => acc + ((e[field] as number) ?? 0), 0);
	}

	function sparklinePath(field: keyof ChargebackEntry): string {
		if (entries.length < 2) return '';
		const values = entries.map((e) => (e[field] as number) ?? 0);
		const max = Math.max(...values);
		const min = Math.min(...values);
		const range = max - min || 1;
		const w = 100;
		const h = 28;
		const pad = 2;
		return values
			.map((v, i) => {
				const x = (i / (values.length - 1)) * w;
				const y = pad + ((max - v) / range) * (h - pad * 2);
				return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
			})
			.join(' ');
	}

	const metricsDef = [
		{ label: 'Bytes In', field: 'bytesIn' as keyof ChargebackEntry, icon: ArrowDownToLine },
		{ label: 'Bytes Out', field: 'bytesOut' as keyof ChargebackEntry, icon: ArrowUpFromLine },
		{ label: 'Reads', field: 'reads' as keyof ChargebackEntry, icon: Eye },
		{ label: 'Writes', field: 'writes' as keyof ChargebackEntry, icon: PenLine },
	];

	function formatValue(field: keyof ChargebackEntry): string {
		const total = sumField(field);
		if (field === 'bytesIn' || field === 'bytesOut') return formatBytes(total);
		return total.toLocaleString();
	}
</script>

{#if !chargebackData?.current}
	<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
		{#each Array(4) as _, i (i)}<CardSkeleton />{/each}
	</div>
{:else if entries.length > 0}
	<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
		{#each metricsDef as m, i (m.field)}
			<StatCard label={m.label} value={formatValue(m.field)} icon={m.icon} delay="delay-{i * 75}">
				{#if entries.length > 1}
					<div class="mt-2 h-[32px] w-full">
						<svg viewBox="0 0 100 28" preserveAspectRatio="none" class="h-full w-full">
							<path
								d={sparklinePath(m.field)}
								fill="none"
								stroke="hsl(var(--primary))"
								stroke-width="1.5"
								stroke-linecap="round"
								stroke-linejoin="round"
								vector-effect="non-scaling-stroke"
							/>
						</svg>
					</div>
				{/if}
			</StatCard>
		{/each}
	</div>
{/if}
