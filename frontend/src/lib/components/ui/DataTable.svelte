<script lang="ts" generics="T extends Record<string, any>">
	import {
		createTable,
		getCoreRowModel,
		getSortedRowModel,
		type ColumnDef,
		type SortingState,
		type TableOptionsResolved,
	} from '@tanstack/table-core';
	import * as Table from '$lib/components/ui/table/index.js';
	import { cn } from '$lib/utils/cn.js';

	interface Props {
		columns: ColumnDef<T, any>[];
		data: T[];
		class?: string;
		onrowclick?: (item: T) => void;
		emptyMessage?: string;
	}

	let {
		columns,
		data,
		class: className = '',
		onrowclick,
		emptyMessage = 'No data available',
	}: Props = $props();

	let sorting = $state<SortingState>([]);

	const options = $derived<TableOptionsResolved<T>>({
		data,
		columns,
		state: {
			sorting,
			columnFilters: [],
			columnVisibility: {},
			rowSelection: {},
			expanded: {},
			grouping: [],
			columnPinning: { left: [], right: [] },
			rowPinning: { top: [], bottom: [] },
			pagination: { pageIndex: 0, pageSize: data.length || 10 },
			globalFilter: undefined,
			columnOrder: [],
		},
		onSortingChange(updater) {
			sorting = typeof updater === 'function' ? updater(sorting) : updater;
		},
		getCoreRowModel: getCoreRowModel(),
		getSortedRowModel: getSortedRowModel(),
		renderFallbackValue: '',
		onStateChange() {},
		onColumnFiltersChange() {},
		onColumnVisibilityChange() {},
		onRowSelectionChange() {},
		onExpandedChange() {},
		onGroupingChange() {},
		onColumnPinningChange() {},
		onRowPinningChange() {},
		onPaginationChange() {},
		onGlobalFilterChange() {},
		onColumnOrderChange() {},
	});

	const table = $derived(createTable(options));
</script>

<div class={cn('overflow-x-auto rounded-lg border', className)}>
	<Table.Root>
		<Table.Header>
			{#each table.getHeaderGroups() as headerGroup}
				<Table.Row>
					{#each headerGroup.headers as header}
						<Table.Head>
							{#if typeof header.column.columnDef.header === 'string'}
								{header.column.columnDef.header}
							{:else if typeof header.column.columnDef.header === 'function'}
								{@const result = header.column.columnDef.header(header.getContext())}
								{#if typeof result === 'string'}
									{result}
								{/if}
							{/if}
						</Table.Head>
					{/each}
				</Table.Row>
			{/each}
		</Table.Header>
		<Table.Body>
			{#if table.getRowModel().rows.length === 0}
				<Table.Row>
					<Table.Cell colspan={columns.length} class="text-center text-muted-foreground py-8">
						{emptyMessage}
					</Table.Cell>
				</Table.Row>
			{:else}
				{#each table.getRowModel().rows as row}
					<Table.Row
						class={cn(onrowclick && 'cursor-pointer')}
						onclick={() => onrowclick?.(row.original)}
						onkeydown={(e: KeyboardEvent) => e.key === 'Enter' && onrowclick?.(row.original)}
						role={onrowclick ? 'button' : undefined}
						tabindex={onrowclick ? 0 : undefined}
					>
						{#each row.getVisibleCells() as cell}
							<Table.Cell>
								{#if typeof cell.column.columnDef.cell === 'function'}
									{@const result = cell.column.columnDef.cell(cell.getContext())}
									{#if typeof result === 'string'}
										{result}
									{:else}
										{cell.getValue()}
									{/if}
								{:else}
									{cell.getValue()}
								{/if}
							</Table.Cell>
						{/each}
					</Table.Row>
				{/each}
			{/if}
		</Table.Body>
	</Table.Root>
</div>
