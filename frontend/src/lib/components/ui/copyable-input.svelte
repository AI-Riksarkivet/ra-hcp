<script lang="ts">
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Copy, Check, Eye, EyeOff } from 'lucide-svelte';

	let {
		value,
		label = '',
		secret = false,
	}: {
		value: string;
		label?: string;
		secret?: boolean;
	} = $props();

	let revealed = $state(false);
	let copied = $state(false);

	async function copy() {
		try {
			await navigator.clipboard.writeText(value);
		} catch {
			const ta = document.createElement('textarea');
			ta.value = value;
			ta.style.position = 'fixed';
			ta.style.opacity = '0';
			document.body.appendChild(ta);
			ta.select();
			document.execCommand('copy');
			document.body.removeChild(ta);
		}
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}
</script>

<div class="space-y-1">
	{#if label}
		<Label class="text-xs">{label}</Label>
	{/if}
	<div class="flex items-center gap-1">
		<Input
			readonly
			type={secret && !revealed ? 'password' : 'text'}
			{value}
			class="h-8 font-mono text-xs"
		/>
		{#if secret}
			<Tooltip.Root>
				<Tooltip.Trigger>
					{#snippet child({ props })}
						<Button
							{...props}
							variant="ghost"
							size="icon"
							class="h-8 w-8 shrink-0"
							onclick={() => (revealed = !revealed)}
						>
							{#if revealed}<EyeOff class="h-3.5 w-3.5" />{:else}<Eye class="h-3.5 w-3.5" />{/if}
						</Button>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Content>{revealed ? 'Hide' : 'Reveal'}</Tooltip.Content>
			</Tooltip.Root>
		{/if}
		<Tooltip.Root>
			<Tooltip.Trigger>
				{#snippet child({ props })}
					<Button {...props} variant="ghost" size="icon" class="h-8 w-8 shrink-0" onclick={copy}>
						{#if copied}<Check class="h-3.5 w-3.5 text-emerald-500" />{:else}<Copy
								class="h-3.5 w-3.5"
							/>{/if}
					</Button>
				{/snippet}
			</Tooltip.Trigger>
			<Tooltip.Content>{copied ? 'Copied!' : 'Copy'}</Tooltip.Content>
		</Tooltip.Root>
	</div>
</div>
