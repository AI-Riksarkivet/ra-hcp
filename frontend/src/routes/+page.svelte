<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let { data } = $props();

	onMount(() => {
		goto(data.hasToken ? '/namespaces' : '/login', { replaceState: true });
	});
</script>
