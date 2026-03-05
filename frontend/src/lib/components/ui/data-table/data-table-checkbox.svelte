<script lang="ts">
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import type { ComponentProps } from 'svelte';

	let {
		checked = $bindable(false),
		indeterminate = $bindable(false),
		onCheckedChange,
		...restProps
	}: ComponentProps<typeof Checkbox> & {
		onCheckedChange?: (value: boolean) => void;
	} = $props();
</script>

<Checkbox
	bind:checked={() => checked, (v) => onCheckedChange?.(!!v)}
	bind:indeterminate
	{...restProps}
/>
