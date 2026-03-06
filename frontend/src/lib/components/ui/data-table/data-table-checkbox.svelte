<script lang="ts">
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';

	let {
		checked = false,
		onCheckedChange,
		disabled = false,
		hidden = false,
	}: {
		checked?: boolean;
		onCheckedChange?: (value: boolean) => void;
		disabled?: boolean;
		hidden?: boolean;
	} = $props();
</script>

{#if !hidden}
	<span
		onclick={(e: MouseEvent) => e.stopPropagation()}
		onkeydown={(e: KeyboardEvent) => e.stopPropagation()}
		role="presentation"
	>
		<Checkbox {checked} onCheckedChange={(v) => onCheckedChange?.(!!v)} {disabled} />
	</span>
{/if}
