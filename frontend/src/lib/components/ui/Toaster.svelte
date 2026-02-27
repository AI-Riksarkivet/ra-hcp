<script lang="ts">
	import { CheckCircle, XCircle, Info, X } from 'lucide-svelte';
	import { getToasts, removeToast } from '$lib/stores/toast.svelte.js';
	import { fly } from 'svelte/transition';

	const iconMap = {
		success: CheckCircle,
		error: XCircle,
		info: Info
	};

	const colorMap = {
		success:
			'border-emerald-200 bg-emerald-50 text-emerald-800 dark:border-emerald-800 dark:bg-emerald-900/20 dark:text-emerald-300',
		error:
			'border-red-200 bg-red-50 text-red-800 dark:border-red-800 dark:bg-red-900/20 dark:text-red-300',
		info: 'border-primary-200 bg-primary-50 text-primary-800 dark:border-primary-800 dark:bg-primary-900/20 dark:text-primary-300'
	};

	const iconColorMap = {
		success: 'text-emerald-500',
		error: 'text-red-500',
		info: 'text-primary-500'
	};
</script>

<div class="pointer-events-none fixed bottom-4 right-4 z-[100] flex flex-col gap-2">
	{#each getToasts() as t (t.id)}
		{@const Icon = iconMap[t.type]}
		<div
			class="pointer-events-auto flex w-80 items-center gap-3 rounded-lg border p-3 shadow-lg {colorMap[t.type]}"
			transition:fly={{ x: 100, duration: 250 }}
			role="alert"
		>
			<Icon class="h-5 w-5 shrink-0 {iconColorMap[t.type]}" />
			<p class="flex-1 text-sm font-medium">{t.message}</p>
			<button
				onclick={() => removeToast(t.id)}
				class="shrink-0 rounded p-0.5 opacity-60 transition-opacity hover:opacity-100"
			>
				<X class="h-4 w-4" />
			</button>
		</div>
	{/each}
</div>
