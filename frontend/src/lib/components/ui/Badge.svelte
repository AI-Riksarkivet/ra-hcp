<script lang="ts">
	import { cn } from '$lib/utils/cn.js';

	interface Props {
		variant?: 'default' | 'success' | 'warning' | 'danger';
		class?: string;
		children?: import('svelte').Snippet;
	}

	let { variant = 'default', class: className = '', children }: Props = $props();

	const variants = {
		default: 'bg-surface-100 text-surface-700 dark:bg-surface-800 dark:text-surface-300',
		success: 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/30 dark:text-emerald-400',
		warning: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-400',
		danger: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-400'
	};
</script>

<span
	class={cn(
		'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium',
		variants[variant],
		className
	)}
>
	{@render children?.()}
</span>
