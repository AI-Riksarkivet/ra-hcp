<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-svelte';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import { formatBytes } from '$lib/utils/format.js';
	import type { ChargebackEntry } from '$lib/utils/format.js';
	import type { ChargebackReport } from '$lib/remote/tenant-info.remote.js';
	import type { RemoteQuery } from '@sveltejs/kit';

	let {
		chargebackData,
	}: {
		chargebackData: RemoteQuery<ChargebackReport>;
	} = $props();

	// Aggregate chargeback entries by namespace (HCP may return multiple rows per namespace)
	let entries = $derived.by(() => {
		const raw = (chargebackData?.current?.chargebackData ?? []) as ChargebackEntry[];
		const map = new Map<string, ChargebackEntry>();
		for (const e of raw) {
			const name = e.namespaceName ?? '';
			const existing = map.get(name);
			if (!existing) {
				map.set(name, { ...e });
			} else {
				existing.objectCount = Math.max(existing.objectCount ?? 0, e.objectCount ?? 0);
				existing.storageCapacityUsed = Math.max(
					existing.storageCapacityUsed ?? 0,
					e.storageCapacityUsed ?? 0
				);
				existing.ingestedVolume = (existing.ingestedVolume ?? 0) + (e.ingestedVolume ?? 0);
				existing.bytesIn = (existing.bytesIn ?? 0) + (e.bytesIn ?? 0);
				existing.bytesOut = (existing.bytesOut ?? 0) + (e.bytesOut ?? 0);
				existing.reads = (existing.reads ?? 0) + (e.reads ?? 0);
				existing.writes = (existing.writes ?? 0) + (e.writes ?? 0);
				existing.deletes = (existing.deletes ?? 0) + (e.deletes ?? 0);
			}
		}
		return [...map.values()];
	});

	type SortKey = keyof ChargebackEntry;

	let sortColumn = $state<SortKey>('storageCapacityUsed');
	let sortDirection = $state<'asc' | 'desc'>('desc');

	function toggleSort(key: SortKey) {
		if (sortColumn === key) {
			sortDirection = sortDirection === 'asc' ? 'desc' : 'asc';
		} else {
			sortColumn = key;
			sortDirection = 'desc';
		}
	}

	interface ColumnDef {
		key: SortKey;
		label: string;
		format: (value: number) => string;
		align: 'left' | 'right';
	}

	const columns: ColumnDef[] = [
		{ key: 'namespaceName' as SortKey, label: 'Namespace', format: () => '', align: 'left' },
		{ key: 'objectCount', label: 'Objects', format: (v) => v.toLocaleString(), align: 'right' },
		{
			key: 'ingestedVolume',
			label: 'Ingested Volume',
			format: (v) => formatBytes(v),
			align: 'right',
		},
		{
			key: 'storageCapacityUsed',
			label: 'Storage Used',
			format: (v) => formatBytes(v),
			align: 'right',
		},
		{ key: 'bytesIn', label: 'Bytes In', format: (v) => formatBytes(v), align: 'right' },
		{ key: 'bytesOut', label: 'Bytes Out', format: (v) => formatBytes(v), align: 'right' },
		{ key: 'reads', label: 'Reads', format: (v) => v.toLocaleString(), align: 'right' },
		{ key: 'writes', label: 'Writes', format: (v) => v.toLocaleString(), align: 'right' },
		{ key: 'deletes', label: 'Deletes', format: (v) => v.toLocaleString(), align: 'right' },
	];

	let sortedEntries = $derived.by(() => {
		const sorted = [...entries].sort((a, b) => {
			const aVal = a[sortColumn] ?? 0;
			const bVal = b[sortColumn] ?? 0;
			if (typeof aVal === 'string' && typeof bVal === 'string') {
				return sortDirection === 'asc' ? aVal.localeCompare(bVal) : bVal.localeCompare(aVal);
			}
			const aNum = Number(aVal);
			const bNum = Number(bVal);
			return sortDirection === 'asc' ? aNum - bNum : bNum - aNum;
		});
		return sorted;
	});

	function sumColumn(key: SortKey): number {
		return entries.reduce((acc, e) => acc + (Number(e[key]) || 0), 0);
	}
</script>

{#await chargebackData}
	<CardSkeleton />
{:then}
	<Card.Root>
		<Card.Header>
			<Card.Title>Namespace Chargeback</Card.Title>
			<Card.Description>Storage and I/O breakdown per namespace</Card.Description>
		</Card.Header>
		<Card.Content>
			{#if entries.length === 0}
				<p class="text-sm text-muted-foreground">No chargeback data available.</p>
			{:else}
				<div class="overflow-x-auto">
					<Table.Root>
						<Table.Header>
							<Table.Row>
								{#each columns as col (col.key)}
									<Table.Head
										class="{col.align === 'right' ? 'text-right' : ''} cursor-pointer select-none"
									>
										<button
											class="inline-flex items-center gap-1 hover:text-foreground"
											onclick={() => toggleSort(col.key)}
										>
											{col.label}
											{#if sortColumn === col.key}
												{#if sortDirection === 'asc'}
													<ArrowUp class="h-3.5 w-3.5" />
												{:else}
													<ArrowDown class="h-3.5 w-3.5" />
												{/if}
											{:else}
												<ArrowUpDown class="h-3.5 w-3.5 opacity-30" />
											{/if}
										</button>
									</Table.Head>
								{/each}
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each sortedEntries as entry (entry.namespaceName)}
								<Table.Row>
									{#each columns as col (col.key)}
										{#if col.key === 'namespaceName'}
											<Table.Cell>
												<a
													href="/namespaces/{entry.namespaceName}"
													class="text-primary underline-offset-4 hover:underline"
												>
													{entry.namespaceName}
												</a>
											</Table.Cell>
										{:else}
											<Table.Cell class="text-right">
												{col.format(Number(entry[col.key]) || 0)}
											</Table.Cell>
										{/if}
									{/each}
								</Table.Row>
							{/each}
						</Table.Body>
						<Table.Footer>
							<Table.Row class="font-medium">
								{#each columns as col (col.key)}
									{#if col.key === 'namespaceName'}
										<Table.Cell class="font-medium">Total</Table.Cell>
									{:else}
										<Table.Cell class="text-right font-medium">
											{col.format(sumColumn(col.key))}
										</Table.Cell>
									{/if}
								{/each}
							</Table.Row>
						</Table.Footer>
					</Table.Root>
				</div>
			{/if}
		</Card.Content>
	</Card.Root>
{/await}
