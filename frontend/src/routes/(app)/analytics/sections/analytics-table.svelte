<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
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
	import { Search, SlidersHorizontal } from 'lucide-svelte';
	import {
		DataTable,
		createSvelteTable,
		getCoreRowModel,
		renderSnippet,
	} from '$lib/components/ui/data-table/index.js';
	import type { ColumnDef, PaginationState, VisibilityState } from '@tanstack/table-core';

	let {
		bucket,
		path,
		table: tableName,
	}: { bucket: string; path: string; table: string } = $props();

	const PAGE_SIZE = 50;

	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: PAGE_SIZE });
	let columnVisibility = $state<VisibilityState>({});
	let filterInput = $state('');
	let activeFilter = $state('');

	// Row detail dialog state
	let detailOpen = $state(false);
	let detailRow = $state<Record<string, unknown> | null>(null);

	// Reset pagination, filter, and column visibility when the selected table changes.
	let resetTable = (() => {
		let prev = '';
		return (current: string) => {
			if (prev && prev !== current) {
				pagination = { pageIndex: 0, pageSize: PAGE_SIZE };
				columnVisibility = {};
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

	let hiddenCount = $derived(Object.values(columnVisibility).filter((v) => v === false).length);

	function applyFilter() {
		activeFilter = filterInput.trim();
		pagination = { pageIndex: 0, pageSize: pagination.pageSize };
	}

	function openDetail(row: Record<string, unknown>) {
		detailRow = row;
		detailOpen = true;
	}

	function formatDetailValue(val: unknown): string {
		if (val == null) return 'null';
		if (typeof val === 'object') return JSON.stringify(val, null, 2);
		return String(val);
	}

	let columns = $derived.by((): ColumnDef<Record<string, unknown>>[] => {
		return fields.map((field): ColumnDef<Record<string, unknown>> => {
			if (field.is_binary) {
				return {
					id: field.name,
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
					id: field.name,
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
				id: field.name,
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
				get columnVisibility() {
					return columnVisibility;
				},
			},
			onPaginationChange: (updater) => {
				pagination = typeof updater === 'function' ? updater(pagination) : updater;
			},
			onColumnVisibilityChange: (updater) => {
				columnVisibility = typeof updater === 'function' ? updater(columnVisibility) : updater;
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
			{#if fields.length > 0}
				<DropdownMenu.Root>
					<DropdownMenu.Trigger>
						{#snippet child({ props })}
							<Button variant="outline" size="sm" {...props}>
								<SlidersHorizontal class="mr-2 h-4 w-4" />
								Columns
								{#if hiddenCount > 0}
									<Badge variant="secondary" class="ml-1.5"
										>{fields.length - hiddenCount}/{fields.length}</Badge
									>
								{/if}
							</Button>
						{/snippet}
					</DropdownMenu.Trigger>
					<DropdownMenu.Content align="end" class="max-h-72 w-48 overflow-y-auto">
						{#each fields as field (field.name)}
							<DropdownMenu.CheckboxItem
								checked={columnVisibility[field.name] !== false}
								onCheckedChange={(checked) => {
									columnVisibility = { ...columnVisibility, [field.name]: checked };
								}}
							>
								<span class="truncate">{field.name}</span>
								{#if field.is_vector}
									<Badge variant="outline" class="ml-auto text-[10px]">vec</Badge>
								{:else if field.is_binary}
									<Badge variant="outline" class="ml-auto text-[10px]">bin</Badge>
								{/if}
							</DropdownMenu.CheckboxItem>
						{/each}
					</DropdownMenu.Content>
				</DropdownMenu.Root>
			{/if}
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
			<DataTable table={tanstackTable} onrowclick={openDetail} noResultsMessage="No rows found." />
		{/if}
	</Card.Content>
</Card.Root>

<!-- Row Detail Dialog -->
<Dialog.Root bind:open={detailOpen}>
	<Dialog.Content class="sm:max-w-2xl">
		<Dialog.Header>
			<Dialog.Title>Row Detail</Dialog.Title>
			<Dialog.Description>All fields for the selected row</Dialog.Description>
		</Dialog.Header>
		{#if detailRow}
			<div class="max-h-[60vh] overflow-y-auto">
				<div class="grid gap-3">
					{#each fields as field (field.name)}
						{@const val = detailRow[field.name]}
						<div class="rounded-md border p-3">
							<div class="mb-1 flex items-center gap-2">
								<span class="text-xs font-semibold">{field.name}</span>
								<span class="text-xs text-muted-foreground">{field.type}</span>
								{#if field.is_vector}
									<Badge variant="outline" class="text-[10px]">vector</Badge>
								{:else if field.is_binary}
									<Badge variant="outline" class="text-[10px]">binary</Badge>
								{/if}
							</div>
							{#if field.is_binary}
								{@const binVal = val as BinaryCellMeta | null}
								{#if binVal?.size}
									<img
										src={cellUrl(
											bucket,
											tableName,
											field.name,
											rows.indexOf(detailRow) + offset,
											path || undefined
										)}
										alt={field.name}
										class="max-h-64 rounded object-contain"
									/>
								{:else}
									<span class="text-sm text-muted-foreground">null</span>
								{/if}
							{:else if field.is_vector}
								{@const vecVal = val as VectorValue | null}
								{#if vecVal && vecVal.type === 'vector'}
									<div class="space-y-1">
										<div class="flex flex-wrap gap-2 text-xs">
											<Badge variant="secondary">dim: {vecVal.dim}</Badge>
											<Badge variant="secondary">norm: {vecVal.norm?.toFixed(4)}</Badge>
											<Badge variant="secondary">min: {vecVal.min?.toFixed(4)}</Badge>
											<Badge variant="secondary">max: {vecVal.max?.toFixed(4)}</Badge>
											<Badge variant="secondary">mean: {vecVal.mean?.toFixed(4)}</Badge>
										</div>
										{#if vecVal.preview?.length}
											<div
												class="mt-2 rounded bg-muted p-2 font-mono text-xs leading-relaxed break-all"
											>
												[{vecVal.preview
													.slice(0, 16)
													.map((v) => v?.toFixed(4))
													.join(', ')}{vecVal.preview.length > 16 ? ', ...' : ''}]
											</div>
										{/if}
									</div>
								{:else}
									<span class="text-sm text-muted-foreground">null</span>
								{/if}
							{:else}
								<pre
									class="max-h-48 overflow-auto whitespace-pre-wrap rounded bg-muted p-2 font-mono text-xs">{formatDetailValue(
										val
									)}</pre>
							{/if}
						</div>
					{/each}
				</div>
			</div>
		{/if}
	</Dialog.Content>
</Dialog.Root>
