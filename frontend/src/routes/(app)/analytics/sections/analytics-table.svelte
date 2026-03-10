<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import ErrorBanner from '$lib/components/ui/error-banner.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { get_lance_rows, get_lance_schema } from '$lib/remote/lance.remote.js';
	import {
		cellUrl,
		type LanceField,
		type VectorValue,
		type BinaryCellMeta,
	} from '$lib/types/lance.js';
	import { Search } from 'lucide-svelte';
	import {
		DataTable,
		createSvelteTable,
		getCoreRowModel,
		renderSnippet,
	} from '$lib/components/ui/data-table/index.js';
	import type { ColumnDef, PaginationState } from '@tanstack/table-core';

	let {
		bucket,
		path,
		table: tableName,
	}: { bucket: string; path: string; table: string } = $props();

	const PAGE_SIZE = 50;

	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: PAGE_SIZE });
	let filterInput = $state('');
	let activeFilter = $state('');

	// Reset pagination and filter when the selected table changes.
	// Uses a closure to track the previous value without capturing the prop at init time.
	let resetTable = (() => {
		let prev = '';
		return (current: string) => {
			if (prev && prev !== current) {
				pagination = { pageIndex: 0, pageSize: PAGE_SIZE };
				filterInput = '';
				activeFilter = '';
			}
			prev = current;
		};
	})();
	$effect.pre(() => {
		resetTable(tableName);
	});

	let offset = $derived(pagination.pageIndex * pagination.pageSize);

	let schemaData = $derived(
		get_lance_schema({ bucket, path: path || undefined, table: tableName })
	);
	let fields = $derived((schemaData?.current?.fields ?? []) as LanceField[]);

	let rowsData = $derived(
		get_lance_rows({
			bucket,
			path: path || undefined,
			table: tableName,
			limit: pagination.pageSize,
			offset,
			filter: activeFilter || undefined,
		})
	);
	let rows = $derived((rowsData?.current?.rows ?? []) as Record<string, unknown>[]);
	let total = $derived((rowsData?.current?.total ?? 0) as number);
	let error = $derived(rowsData?.current?.error ?? null);

	function applyFilter() {
		activeFilter = filterInput.trim();
		pagination = { pageIndex: 0, pageSize: pagination.pageSize };
	}

	let columns = $derived.by((): ColumnDef<Record<string, unknown>>[] => {
		return fields.map((field): ColumnDef<Record<string, unknown>> => {
			if (field.is_binary) {
				return {
					accessorKey: field.name,
					header: field.name,
					cell: ({ row }) => {
						const val = row.original[field.name] as BinaryCellMeta | null;
						const rowIndex = row.index;
						return renderSnippet(binaryCell, {
							val,
							column: field.name,
							rowIndex,
						});
					},
					meta: { cellClass: 'px-4 py-3' },
				};
			}

			if (field.is_vector) {
				return {
					accessorKey: field.name,
					header: field.name,
					cell: ({ row }) => {
						const val = row.original[field.name] as VectorValue | null;
						return renderSnippet(vectorCell, { val });
					},
					meta: { cellClass: 'px-4 py-3' },
				};
			}

			return {
				accessorKey: field.name,
				header: field.name,
				cell: ({ row }) => {
					const val = row.original[field.name];
					if (val == null) return '';
					if (typeof val === 'object') return JSON.stringify(val);
					return String(val);
				},
				meta: { cellClass: 'max-w-[300px] truncate px-4 py-3' },
			};
		});
	});

	let tanstackTable = $derived(
		createSvelteTable({
			get data() {
				return rows;
			},
			get columns() {
				return columns;
			},
			state: {
				get pagination() {
					return pagination;
				},
			},
			onPaginationChange: (updater) => {
				pagination = typeof updater === 'function' ? updater(pagination) : updater;
			},
			getCoreRowModel: getCoreRowModel(),
			manualPagination: true,
			get rowCount() {
				return total;
			},
		})
	);
</script>

{#snippet binaryCell(props: { val: BinaryCellMeta | null; column: string; rowIndex: number })}
	{#if props.val?.size}
		<img
			src={cellUrl(bucket, tableName, props.column, offset + props.rowIndex, path || undefined)}
			alt={props.column}
			class="h-12 w-12 rounded object-cover"
			loading="lazy"
			onerror={(e) => {
				const target = e.currentTarget as HTMLImageElement;
				const span = document.createElement('span');
				span.className = 'text-xs text-muted-foreground';
				span.textContent = `${props.val?.size} bytes`;
				target.replaceWith(span);
			}}
		/>
	{:else}
		<span class="text-muted-foreground">null</span>
	{/if}
{/snippet}

{#snippet vectorCell(props: { val: VectorValue | null })}
	{#if props.val && props.val.type === 'vector'}
		<Badge variant="outline" class="font-mono text-xs">
			vec[{props.val.dim}] ‖{props.val.norm?.toFixed(2)}‖
		</Badge>
	{:else}
		<span class="text-muted-foreground">null</span>
	{/if}
{/snippet}

<Card.Root>
	<Card.Header>
		<div class="flex items-center justify-between">
			<Card.Title class="text-sm">
				Data — {tableName}
				{#if total > 0}
					<Badge variant="secondary" class="ml-2">{total.toLocaleString()} rows</Badge>
				{/if}
			</Card.Title>
		</div>
	</Card.Header>
	<Card.Content class="space-y-3">
		<form
			class="flex max-w-lg items-center gap-2"
			onsubmit={(e) => {
				e.preventDefault();
				applyFilter();
			}}
		>
			<div class="relative flex-1">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<Input
					bind:value={filterInput}
					placeholder="Lance filter (e.g. label = 'cat' AND score > 0.5)"
					class="pl-10 text-xs"
				/>
			</div>
			<Button type="submit" variant="outline" size="sm">Filter</Button>
		</form>

		{#if error}
			<ErrorBanner message={String(error)} />
		{:else if fields.length === 0}
			<TableSkeleton rows={5} columns={4} />
		{:else}
			<DataTable table={tanstackTable} noResultsMessage="No rows found." />
		{/if}
	</Card.Content>
</Card.Root>
