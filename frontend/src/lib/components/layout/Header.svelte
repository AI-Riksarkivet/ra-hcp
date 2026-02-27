<script lang="ts">
	import { LogOut, PanelLeftClose, PanelLeft } from 'lucide-svelte';
	import ThemeToggle from './ThemeToggle.svelte';

	interface Props {
		collapsed: boolean;
		ontoggle: () => void;
	}

	let { collapsed, ontoggle }: Props = $props();
</script>

<header
	class="flex h-16 items-center justify-between border-b border-surface-200 bg-white px-4 dark:border-surface-800 dark:bg-surface-900"
>
	<div class="flex items-center gap-3">
		<button
			onclick={ontoggle}
			class="rounded-lg p-2 text-surface-500 transition-colors hover:bg-surface-100 hover:text-surface-700 dark:text-surface-400 dark:hover:bg-surface-800 dark:hover:text-surface-200"
			aria-label={collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
		>
			{#if collapsed}
				<PanelLeft class="h-5 w-5" />
			{:else}
				<PanelLeftClose class="h-5 w-5" />
			{/if}
		</button>
		<h1 class="text-lg font-semibold text-surface-900 dark:text-surface-100">HCP Admin Console</h1>
	</div>

	<div class="flex items-center gap-2">
		<ThemeToggle />
		<a
			href="/logout"
			class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-surface-600 transition-colors hover:bg-surface-100 hover:text-surface-900 dark:text-surface-400 dark:hover:bg-surface-800 dark:hover:text-surface-100"
		>
			<LogOut class="h-4 w-4" />
			Logout
		</a>
	</div>
</header>
