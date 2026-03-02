<script lang="ts">
	import { Moon, Sun } from 'lucide-svelte';
	import { toggleMode, mode } from 'mode-watcher';
	import { Button } from '$lib/components/ui/button/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
</script>

<Tooltip.Root>
	<Tooltip.Trigger>
		{#snippet child({ props })}
			<Button variant="ghost" size="icon" onclick={toggleMode} {...props}>
				{#if mode.current === 'dark'}
					<Sun class="h-5 w-5" />
				{:else}
					<Moon class="h-5 w-5" />
				{/if}
				<span class="sr-only">Toggle theme</span>
			</Button>
		{/snippet}
	</Tooltip.Trigger>
	<Tooltip.Content>{mode.current === 'dark' ? 'Light mode' : 'Dark mode'}</Tooltip.Content>
</Tooltip.Root>
