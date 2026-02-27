<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import Header from '$lib/components/layout/Header.svelte';

	let { children, data } = $props();
	let collapsed = $state(false);

	onMount(() => {
		if (!data.authenticated) {
			goto('/login', { replaceState: true });
		}
	});

	function toggleSidebar() {
		collapsed = !collapsed;
	}
</script>

{#if data.authenticated}
	<div class="flex h-screen overflow-hidden bg-surface-50 dark:bg-surface-950">
		<Sidebar {collapsed} />
		<div class="flex flex-1 flex-col overflow-hidden">
			<Header {collapsed} ontoggle={toggleSidebar} />
			<main class="flex-1 overflow-y-auto p-6">
				{@render children()}
			</main>
		</div>
	</div>
{/if}
