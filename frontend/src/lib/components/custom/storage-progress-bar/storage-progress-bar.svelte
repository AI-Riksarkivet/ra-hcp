<script lang="ts">
	import { cn } from '$lib/utils/cn.js';

	let {
		percent,
		class: className,
	}: {
		percent: number;
		class?: string;
	} = $props();
</script>

<div class={cn('h-1.5 w-full overflow-hidden rounded-full bg-muted', className)}>
	<div
		class="h-full rounded-full transition-all duration-500 {percent > 90
			? 'bg-destructive'
			: percent > 70
				? 'bg-yellow-500'
				: 'bg-primary'}"
		style="width: {percent}%"
	></div>
</div>
