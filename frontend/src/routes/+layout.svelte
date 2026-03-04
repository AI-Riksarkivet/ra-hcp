<script lang="ts">
	import '../app.css';
	import { ModeWatcher } from 'mode-watcher';
	import { Toaster } from '$lib/components/ui/sonner/index.js';
	import { browser } from '$app/environment';
	let { children } = $props();
</script>

<ModeWatcher />
{@render children()}
{#if browser}
	<Toaster />
{/if}
