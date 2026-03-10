<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { get_lance_rows, get_lance_schema } from '$lib/remote/lance.remote.js';
	import {
		cellUrl,
		type LanceField,
		type VectorValue,
		type BinaryCellMeta,
	} from '$lib/types/lance.js';
	import { ChevronLeft, ChevronRight } from 'lucide-svelte';

	let { bucket, path, table }: { bucket: string; path: string; table: string } = $props();

	const pageSize = 50;

	// Overridable derived: resets to 0 whenever `table` changes,
	// but can be temporarily overridden by prevPage/nextPage.
	let currentOffset = $derived.by(() => {
		void table;
		return 0;
	});

	let schemaData = $derived(get_lance_schema({ bucket, path: path || undefined, table }));
	let fields = $derived((schemaData?.current?.fields ?? []) as LanceField[]);

	let rowsData = $derived(
		get_lance_rows({
			bucket,
			path: path || undefined,
			table,
			limit: pageSize,
			offset: currentOffset,
		})
	);
	let rows = $derived((rowsData?.current?.rows ?? []) as Record<string, unknown>[]);
	let total = $derived((rowsData?.current?.total ?? 0) as number);
	let error = $derived(rowsData?.current?.error ?? null);

	let columnNames = $derived(fields.map((f) => f.name));
	let vectorColumns = $derived(new Set(fields.filter((f) => f.is_vector).map((f) => f.name)));
	let binaryColumns = $derived(new Set(fields.filter((f) => f.is_binary).map((f) => f.name)));

	let currentPage = $derived(Math.floor(currentOffset / pageSize) + 1);
	let totalPages = $derived(Math.ceil(total / pageSize));

	function prevPage() {
		currentOffset = Math.max(0, currentOffset - pageSize);
	}

	function nextPage() {
		if (currentOffset + pageSize < total) {
			currentOffset = currentOffset + pageSize;
		}
	}

	function formatCell(value: unknown, colName: string, rowIndex: number): string {
		if (value == null) return '';
		if (vectorColumns.has(colName)) {
			const v = value as VectorValue;
			if (v.type === 'vector') {
				return `vec[${v.dim}] ‖${v.norm?.toFixed(2)}‖`;
			}
		}
		if (typeof value === 'object') {
			return JSON.stringify(value);
		}
		return String(value);
	}
</script>

<Card.Root>
	<Card.Header>
		<div class="flex items-center justify-between">
			<Card.Title class="text-sm">
				Data — {table}
				{#if total > 0}
					<Badge variant="secondary" class="ml-2">{total.toLocaleString()} rows</Badge>
				{/if}
			</Card.Title>
			{#if totalPages > 1}
				<div class="flex items-center gap-2">
					<Button variant="outline" size="sm" onclick={prevPage} disabled={currentOffset === 0}>
						<ChevronLeft class="h-4 w-4" />
					</Button>
					<span class="text-xs text-muted-foreground">
						{currentPage} / {totalPages}
					</span>
					<Button
						variant="outline"
						size="sm"
						onclick={nextPage}
						disabled={currentOffset + pageSize >= total}
					>
						<ChevronRight class="h-4 w-4" />
					</Button>
				</div>
			{/if}
		</div>
	</Card.Header>
	<Card.Content>
		{#if error}
			<ErrorBanner message={String(error)} />
		{:else if rows.length === 0}
			<TableSkeleton rows={5} columns={4} />
		{:else}
			<div class="overflow-x-auto">
				<table class="w-full text-xs">
					<thead>
						<tr class="border-b">
							{#each columnNames as col (col)}
								<th class="px-3 py-2 text-left font-medium text-muted-foreground">{col}</th>
							{/each}
						</tr>
					</thead>
					<tbody>
						{#each rows as row, rowIdx (rowIdx)}
							<tr class="border-b transition-colors hover:bg-muted/50">
								{#each columnNames as col (col)}
									<td class="max-w-[300px] truncate px-3 py-2">
										{#if binaryColumns.has(col) && row[col] != null}
											{@const val = row[col] as BinaryCellMeta}
											{#if val.size}
												<img
													src={cellUrl(
														bucket,
														table,
														col,
														currentOffset + rowIdx,
														path || undefined
													)}
													alt={col}
													class="h-12 w-12 rounded object-cover"
													loading="lazy"
													onerror={(e) => {
														const target = e.currentTarget as HTMLImageElement;
														const span = document.createElement('span');
														span.className = 'text-xs text-muted-foreground';
														span.textContent = `${val.size} bytes`;
														target.replaceWith(span);
													}}
												/>
											{:else}
												<span class="text-muted-foreground">null</span>
											{/if}
										{:else if vectorColumns.has(col) && row[col] != null}
											{@const v = row[col] as VectorValue}
											<span class="font-mono">vec[{v.dim}] ‖{v.norm?.toFixed(2)}‖</span>
										{:else}
											{formatCell(row[col], col, rowIdx)}
										{/if}
									</td>
								{/each}
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
		{/if}
	</Card.Content>
</Card.Root>
