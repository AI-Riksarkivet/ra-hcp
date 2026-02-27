<script lang="ts">
	import { Moon, Sun } from 'lucide-svelte';
	import { Tooltip } from 'bits-ui';
	import { browser } from '$app/environment';

	let dark = $state(false);

	if (browser) {
		dark = document.documentElement.classList.contains('dark');
	}

	function toggle() {
		dark = !dark;
		if (browser) {
			document.documentElement.classList.toggle('dark', dark);
			localStorage.setItem('theme', dark ? 'dark' : 'light');
		}
	}
</script>

<Tooltip.Root>
	<Tooltip.Trigger
		onclick={toggle}
		class="rounded-lg p-2 text-surface-500 transition-colors hover:bg-surface-100 hover:text-surface-700 dark:text-surface-400 dark:hover:bg-surface-800 dark:hover:text-surface-200"
	>
		{#if dark}
			<Sun class="h-5 w-5" />
		{:else}
			<Moon class="h-5 w-5" />
		{/if}
	</Tooltip.Trigger>
	<Tooltip.Portal>
		<Tooltip.Content
			sideOffset={8}
			class="z-50 rounded-lg border border-surface-200 bg-white px-3 py-1.5 text-sm shadow-lg dark:border-surface-700 dark:bg-surface-800"
		>
			{dark ? 'Light mode' : 'Dark mode'}
		</Tooltip.Content>
	</Tooltip.Portal>
</Tooltip.Root>
