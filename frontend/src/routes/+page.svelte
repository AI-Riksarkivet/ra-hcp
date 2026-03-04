<script lang="ts">
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';

	let { data } = $props();

	onMount(() => {
		goto(data.hasToken ? '/overview' : '/login', { replaceState: true });
	});
</script>
