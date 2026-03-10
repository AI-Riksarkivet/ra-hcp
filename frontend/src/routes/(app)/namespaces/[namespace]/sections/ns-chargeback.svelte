<script lang="ts">
	import { Chart, Svg, Spline } from 'layerchart';
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

	function sparklineData(field: keyof ChargebackEntry) {
		return entries.map((e, i) => ({
			date: i,
			value: (e[field] as number) ?? 0,
		}));
	}

	let metrics = $derived([
		{
			label: 'Bytes In',
			value: formatBytes(sumField('bytesIn')),
			icon: ArrowDownToLine,
			field: 'bytesIn' as keyof ChargebackEntry,
			color: 'hsl(var(--primary))',
		},
		{
			label: 'Bytes Out',
			value: formatBytes(sumField('bytesOut')),
			icon: ArrowUpFromLine,
			field: 'bytesOut' as keyof ChargebackEntry,
			color: 'hsl(var(--primary))',
		},
		{
			label: 'Reads',
			value: sumField('reads').toLocaleString(),
			icon: Eye,
			field: 'reads' as keyof ChargebackEntry,
			color: 'hsl(var(--primary))',
		},
		{
			label: 'Writes',
			value: sumField('writes').toLocaleString(),
			icon: PenLine,
			field: 'writes' as keyof ChargebackEntry,
			color: 'hsl(var(--primary))',
		},
	]);
</script>

{#await chargebackData}
	<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
		{#each Array(4) as _, i (i)}<CardSkeleton />{/each}
	</div>
{:then}
	{#if entries.length > 0}
		<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
			{#each metrics as m, i (m.field)}
				<StatCard label={m.label} value={m.value} icon={m.icon} delay="delay-{i * 75}">
					{#if entries.length > 1}
						<div class="mt-2 h-[32px] w-full">
							<Chart
								data={sparklineData(m.field)}
								x="date"
								y="value"
								padding={{ top: 4, bottom: 4, left: 0, right: 0 }}
							>
								<Svg>
									<Spline class="stroke-primary fill-none" style="stroke-width: 1.5" />
								</Svg>
							</Chart>
						</div>
					{/if}
				</StatCard>
			{/each}
		</div>
	{/if}
{/await}
