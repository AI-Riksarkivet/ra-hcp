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

	const W = 120;
	const H = 48;
	const PAD = 4;

	interface SparkPoint {
		x: number;
		y: number;
		value: number;
		label: string;
	}

	function sparkPoints(field: keyof ChargebackEntry): SparkPoint[] {
		if (entries.length < 2) return [];
		const values = entries.map((e) => (e[field] as number) ?? 0);
		const max = Math.max(...values);
		const min = Math.min(...values);
		const range = max - min || 1;
		return values.map((v, i) => ({
			x: (i / (values.length - 1)) * W,
			y: PAD + ((max - v) / range) * (H - PAD * 2),
			value: v,
			label: entries[i].startTime
				? new Date(entries[i].startTime!).toLocaleDateString()
				: `Day ${i + 1}`,
		}));
	}

	function linePath(points: SparkPoint[]): string {
		return points
			.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x.toFixed(1)},${p.y.toFixed(1)}`)
			.join(' ');
	}

	function areaPath(points: SparkPoint[]): string {
		if (!points.length) return '';
		return `${linePath(points)} L${W},${H} L0,${H} Z`;
	}

	const metricsDef = [
		{ label: 'Bytes In', field: 'bytesIn' as keyof ChargebackEntry, icon: ArrowDownToLine },
		{
			label: 'Bytes Out',
			field: 'bytesOut' as keyof ChargebackEntry,
			icon: ArrowUpFromLine,
		},
		{ label: 'Reads', field: 'reads' as keyof ChargebackEntry, icon: Eye },
		{ label: 'Writes', field: 'writes' as keyof ChargebackEntry, icon: PenLine },
	];

	function formatTotal(field: keyof ChargebackEntry): string {
		const total = sumField(field);
		if (field === 'bytesIn' || field === 'bytesOut') return formatBytes(total);
		return total.toLocaleString();
	}

	function formatPointValue(field: keyof ChargebackEntry, value: number): string {
		if (field === 'bytesIn' || field === 'bytesOut') return formatBytes(value);
		return value.toLocaleString();
	}

	let hoverIndex: Record<string, number | null> = $state({
		bytesIn: null,
		bytesOut: null,
		reads: null,
		writes: null,
	});

	function handleMouseMove(field: string, points: SparkPoint[], event: MouseEvent) {
		const svg = event.currentTarget as SVGSVGElement;
		const rect = svg.getBoundingClientRect();
		const mouseX = ((event.clientX - rect.left) / rect.width) * W;
		let closest = 0;
		let minDist = Infinity;
		for (let i = 0; i < points.length; i++) {
			const dist = Math.abs(points[i].x - mouseX);
			if (dist < minDist) {
				minDist = dist;
				closest = i;
			}
		}
		hoverIndex[field] = closest;
	}

	function handleMouseLeave(field: string) {
		hoverIndex[field] = null;
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
					{@const points = sparkPoints(m.field)}
					{@const hi = hoverIndex[m.field]}
					{@const hoveredPoint = hi != null ? points[hi] : null}
					<div class="space-y-2">
						<div class="flex items-center gap-2 text-sm text-muted-foreground">
							<m.icon class="h-3.5 w-3.5" />
							{m.label}
						</div>
						<div class="flex items-baseline gap-2">
							<p class="text-xl font-semibold">{formatTotal(m.field)}</p>
							{#if hoveredPoint}
								<span class="animate-in fade-in text-xs text-muted-foreground duration-150">
									{hoveredPoint.label}: {formatPointValue(m.field, hoveredPoint.value)}
								</span>
							{/if}
						</div>
						{#if points.length > 1}
							<svg
								viewBox="0 0 {W} {H}"
								preserveAspectRatio="none"
								class="h-[48px] w-full cursor-crosshair"
								role="img"
								aria-label="{m.label} sparkline"
								onmousemove={(e) => handleMouseMove(m.field, points, e)}
								onmouseleave={() => handleMouseLeave(m.field)}
							>
								<defs>
									<linearGradient id="grad-{m.field}" x1="0" y1="0" x2="0" y2="1">
										<stop offset="0%" stop-color="hsl(var(--primary))" stop-opacity="0.3" />
										<stop offset="100%" stop-color="hsl(var(--primary))" stop-opacity="0.02" />
									</linearGradient>
								</defs>
								<path d={areaPath(points)} fill="url(#grad-{m.field})" />
								<path
									d={linePath(points)}
									fill="none"
									stroke="hsl(var(--primary))"
									stroke-width="2"
									stroke-linecap="round"
									stroke-linejoin="round"
									vector-effect="non-scaling-stroke"
								/>
								{#if hoveredPoint}
									<line
										x1={hoveredPoint.x}
										y1={PAD}
										x2={hoveredPoint.x}
										y2={H}
										stroke="hsl(var(--muted-foreground))"
										stroke-width="1"
										stroke-dasharray="2,2"
										vector-effect="non-scaling-stroke"
									/>
									<circle
										cx={hoveredPoint.x}
										cy={hoveredPoint.y}
										r="2"
										fill="hsl(var(--primary))"
										stroke="hsl(var(--background))"
										stroke-width="1.5"
										vector-effect="non-scaling-stroke"
									/>
								{/if}
							</svg>
						{/if}
					</div>
				{/each}
			</div>
		</Card.Content>
	</Card.Root>
{/if}
