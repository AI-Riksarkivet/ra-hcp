<script lang="ts">
	import { cn } from '$lib/utils/cn.js';

	interface Props {
		type?: string;
		name?: string;
		id?: string;
		value?: string;
		placeholder?: string;
		required?: boolean;
		disabled?: boolean;
		error?: string;
		label?: string;
		class?: string;
	}

	let {
		type = 'text',
		name,
		id,
		value = $bindable(''),
		placeholder,
		required = false,
		disabled = false,
		error,
		label,
		class: className = ''
	}: Props = $props();
</script>

<div class="flex flex-col gap-1.5">
	{#if label}
		<label for={id ?? name} class="text-sm font-medium text-surface-700 dark:text-surface-300">
			{label}
		</label>
	{/if}
	<input
		{type}
		{name}
		id={id ?? name}
		bind:value
		{placeholder}
		{required}
		{disabled}
		class={cn(
			'rounded-lg border bg-white px-3 py-2 text-sm shadow-sm transition-colors placeholder:text-surface-400 focus:border-primary-500 focus:outline-none focus:ring-2 focus:ring-primary-500/20 disabled:cursor-not-allowed disabled:opacity-50 dark:bg-surface-900 dark:text-surface-100 dark:placeholder:text-surface-600',
			error
				? 'border-danger text-danger'
				: 'border-surface-300 dark:border-surface-700',
			className
		)}
	/>
	{#if error}
		<p class="text-sm text-danger">{error}</p>
	{/if}
</div>
