<script lang="ts">
	import { cn } from '$lib/utils/cn.js';

	interface Props {
		class?: string;
		children?: import('svelte').Snippet;
	}

	let { class: className = '', children }: Props = $props();
</script>

<div
	class={cn(
		'rounded-xl border border-surface-200 bg-white p-6 shadow-sm dark:border-surface-800 dark:bg-surface-900',
		className
	)}
>
	{@render children?.()}
</div>
