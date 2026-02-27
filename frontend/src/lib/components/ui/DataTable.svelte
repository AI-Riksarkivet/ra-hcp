<script lang="ts" generics="T">
	import { cn } from '$lib/utils/cn.js';

	interface Column<T> {
		key: string;
		label: string;
		render?: (item: T) => string;
		class?: string;
	}

	interface Props {
		columns: Column<T>[];
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
		emptyMessage = 'No data available'
	}: Props = $props();

	function getCellValue(item: T, col: Column<T>): string {
		if (col.render) return col.render(item);
		const value = (item as Record<string, unknown>)[col.key];
		return value != null ? String(value) : '';
	}
</script>

<div class={cn('overflow-x-auto rounded-lg border border-surface-200 dark:border-surface-800', className)}>
	<table class="w-full text-left text-sm">
		<thead class="border-b border-surface-200 bg-surface-50 text-xs uppercase tracking-wide text-surface-500 dark:border-surface-800 dark:bg-surface-900 dark:text-surface-400">
			<tr>
				{#each columns as col}
					<th class={cn('px-4 py-3 font-medium', col.class)}>{col.label}</th>
				{/each}
			</tr>
		</thead>
		<tbody class="divide-y divide-surface-100 dark:divide-surface-800">
			{#if data.length === 0}
				<tr>
					<td colspan={columns.length} class="px-4 py-8 text-center text-surface-500">
						{emptyMessage}
					</td>
				</tr>
			{:else}
				{#each data as item}
					<tr
						class={cn(
							'bg-white dark:bg-surface-900',
							onrowclick && 'cursor-pointer hover:bg-surface-50 dark:hover:bg-surface-800'
						)}
						onclick={() => onrowclick?.(item)}
						onkeydown={(e) => e.key === 'Enter' && onrowclick?.(item)}
						role={onrowclick ? 'button' : undefined}
						tabindex={onrowclick ? 0 : undefined}
					>
						{#each columns as col}
							<td class={cn('px-4 py-3', col.class)}>
								{getCellValue(item, col)}
							</td>
						{/each}
					</tr>
				{/each}
			{/if}
		</tbody>
	</table>
</div>
