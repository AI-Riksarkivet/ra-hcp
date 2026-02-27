<script lang="ts">
	import { Moon, Sun } from 'lucide-svelte';
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

<button
	onclick={toggle}
	class="rounded-lg p-2 text-surface-500 transition-colors hover:bg-surface-100 hover:text-surface-700 dark:text-surface-400 dark:hover:bg-surface-800 dark:hover:text-surface-200"
	aria-label="Toggle theme"
>
	{#if dark}
		<Sun class="h-5 w-5" />
	{:else}
		<Moon class="h-5 w-5" />
	{/if}
</button>
