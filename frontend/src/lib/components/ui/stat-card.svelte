<script lang="ts">
	import type { Snippet } from 'svelte';
	import type { IconProps } from 'lucide-svelte';
	import { SvelteComponentTyped } from 'svelte';
	import * as Card from '$lib/components/ui/card/index.js';

	type LucideIcon = new (
		...args: ConstructorParameters<typeof SvelteComponentTyped<IconProps>>
	) => SvelteComponentTyped<IconProps>;

	let {
		label,
		value,
		icon: Icon,
		delay = '',
		children,
	}: {
		label: string;
		value: string;
		icon: LucideIcon;
		delay?: string;
		children?: Snippet;
	} = $props();
</script>

<div class="animate-in fade-in slide-in-from-bottom-2 duration-300 {delay}">
	<Card.Root class="h-full">
		<Card.Content class="pt-6">
			<div class="flex items-center justify-between">
				<div class="min-w-0 flex-1">
					<p class="text-sm font-medium text-muted-foreground">{label}</p>
					<p class="mt-1 text-2xl font-bold">{value}</p>
					{#if children}
						{@render children()}
					{/if}
				</div>
				<div class="ml-4 rounded-lg bg-primary/10 p-3">
					<Icon class="h-6 w-6 text-primary" />
				</div>
			</div>
		</Card.Content>
	</Card.Root>
</div>
