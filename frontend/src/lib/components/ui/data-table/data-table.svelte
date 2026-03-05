<script lang="ts" generics="TData">
	import type { Snippet } from 'svelte';
	import type { Table } from '@tanstack/table-core';
	import * as TablePrimitive from '$lib/components/ui/table/index.js';
	import { FlexRender } from '$lib/components/ui/data-table/index.js';
	import { cn } from '$lib/utils.js';

	let {
		table,
		onrowclick,
		noResultsMessage = 'No results.',
		subHeaderRow,
	}: {
		table: Table<TData>;
		onrowclick?: (row: TData) => void;
		noResultsMessage?: string;
		subHeaderRow?: Snippet;
	} = $props();
</script>

<div class="overflow-x-auto rounded-lg border">
	<TablePrimitive.Root>
		<TablePrimitive.Header
			class="bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground"
		>
			{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
				<TablePrimitive.Row class="border-b hover:bg-transparent">
					{#each headerGroup.headers as header (header.id)}
						<TablePrimitive.Head
							class={cn('px-4 py-3 font-medium', header.column.columnDef.meta?.headerClass)}
						>
							{#if !header.isPlaceholder}
								<FlexRender
									content={header.column.columnDef.header}
									context={header.getContext()}
								/>
							{/if}
						</TablePrimitive.Head>
					{/each}
				</TablePrimitive.Row>
			{/each}
			{#if subHeaderRow}
				{@render subHeaderRow()}
			{/if}
		</TablePrimitive.Header>
		<TablePrimitive.Body>
			{#each table.getRowModel().rows as row (row.id)}
				<TablePrimitive.Row
					class={cn('bg-card transition-colors', onrowclick && 'cursor-pointer')}
					onclick={onrowclick ? () => onrowclick(row.original) : undefined}
					onkeydown={onrowclick
						? (e) => {
								if (e.key === 'Enter') onrowclick(row.original);
							}
						: undefined}
					role={onrowclick ? 'button' : undefined}
					tabindex={onrowclick ? 0 : undefined}
				>
					{#each row.getVisibleCells() as cell (cell.id)}
						<TablePrimitive.Cell class={cn('px-4 py-3', cell.column.columnDef.meta?.cellClass)}>
							<FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
						</TablePrimitive.Cell>
					{/each}
				</TablePrimitive.Row>
			{:else}
				<TablePrimitive.Row>
					<TablePrimitive.Cell
						colspan={table.getAllColumns().length}
						class="px-4 py-8 text-center text-muted-foreground"
					>
						{noResultsMessage}
					</TablePrimitive.Cell>
				</TablePrimitive.Row>
			{/each}
		</TablePrimitive.Body>
	</TablePrimitive.Root>
</div>
