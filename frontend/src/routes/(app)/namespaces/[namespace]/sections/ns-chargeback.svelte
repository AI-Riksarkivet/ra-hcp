<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { ArrowDownToLine, ArrowUpFromLine, Eye, PenLine } from 'lucide-svelte';
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
		const w = 120;
		const h = 40;
		const pad = 4;
		return values
			.map((v, i) => {
				const x = (i / (values.length - 1)) * w;
				const y = pad + ((max - v) / range) * (h - pad * 2);
				return `${i === 0 ? 'M' : 'L'}${x.toFixed(1)},${y.toFixed(1)}`;
			})
			.join(' ');
	}

	function areaPath(field: keyof ChargebackEntry): string {
		const line = sparklinePath(field);
		if (!line) return '';
		return `${line} L120,40 L0,40 Z`;
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
	<CardSkeleton />
{:else if entries.length > 0}
	<Card.Root>
		<Card.Header>
			<Card.Title>I/O Activity</Card.Title>
			<Card.Description>Namespace chargeback metrics (7 day)</Card.Description>
		</Card.Header>
		<Card.Content>
			<div class="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
				{#each metricsDef as m (m.field)}
					<div class="space-y-2">
						<div class="flex items-center gap-2 text-sm text-muted-foreground">
							<m.icon class="h-3.5 w-3.5" />
							{m.label}
						</div>
						<p class="text-xl font-semibold">{formatValue(m.field)}</p>
						{#if entries.length > 1}
							<svg viewBox="0 0 120 40" preserveAspectRatio="none" class="h-[40px] w-full">
								<defs>
									<linearGradient id="grad-{m.field}" x1="0" y1="0" x2="0" y2="1">
										<stop offset="0%" stop-color="hsl(var(--primary))" stop-opacity="0.3" />
										<stop offset="100%" stop-color="hsl(var(--primary))" stop-opacity="0.02" />
									</linearGradient>
								</defs>
								<path d={areaPath(m.field)} fill="url(#grad-{m.field})" />
								<path
									d={sparklinePath(m.field)}
									fill="none"
									stroke="hsl(var(--primary))"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									vector-effect="non-scaling-stroke"
								/>
							</svg>
						{/if}
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
{/if}
