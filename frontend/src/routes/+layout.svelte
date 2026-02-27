<script lang="ts">
	import '../app.css';
	import { Tooltip } from 'bits-ui';
	import Toaster from '$lib/components/ui/Toaster.svelte';

	let { children } = $props();
</script>

<Tooltip.Provider delayDuration={300} skipDelayDuration={150}>
	{@render children()}
</Tooltip.Provider>
<Toaster />
