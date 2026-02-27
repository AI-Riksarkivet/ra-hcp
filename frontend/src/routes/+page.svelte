<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let { data } = $props();

	onMount(() => {
		goto(data.hasToken ? '/dashboard' : '/login', { replaceState: true });
	});
</script>
