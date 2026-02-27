<script lang="ts">
	import Sidebar from '$lib/components/layout/Sidebar.svelte';
	import Header from '$lib/components/layout/Header.svelte';

	let { data, children } = $props();
	let collapsed = $state(false);

	function toggleSidebar() {
		collapsed = !collapsed;
	}
</script>

<div class="flex h-screen overflow-hidden bg-surface-50 dark:bg-surface-950">
	<Sidebar {collapsed} />
	<div class="flex flex-1 flex-col overflow-hidden">
		<Header {collapsed} ontoggle={toggleSidebar} username={data.username} />
		<main class="flex-1 overflow-y-auto p-6">
			{@render children()}
		</main>
	</div>
</div>
