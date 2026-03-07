<script lang="ts">
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { KeyRound, Copy, Check, Eye, EyeOff } from 'lucide-svelte';
	import { get_s3_credentials } from '$lib/buckets.remote.js';

	let {
		tenant,
	}: {
		tenant: string;
	} = $props();

	let credsData = $derived(get_s3_credentials());
	let creds = $derived(
		credsData?.current as
			| { access_key_id: string; secret_access_key: string; username: string; endpoint_url: string }
			| undefined
	);
	let showSecret = $state(false);
	let copied = $state<string | null>(null);

	async function copyToClipboard(value: string, label: string) {
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
		copied = label;
		setTimeout(() => {
			if (copied === label) copied = null;
		}, 2000);
	}
</script>

<div class="rounded-lg border p-5">
	<div class="flex items-center gap-2">
		<KeyRound class="h-4 w-4 text-muted-foreground" />
		<h3 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
			S3 Credentials
		</h3>
	</div>
	{#await credsData}
		<div class="mt-3 space-y-3">
			{#each Array(3) as _, i (i)}
				<div class="space-y-1">
					<div class="h-3 w-20 animate-pulse rounded bg-muted"></div>
					<div class="h-8 w-full animate-pulse rounded bg-muted"></div>
				</div>
			{/each}
		</div>
	{:then}
		{#if creds && creds.access_key_id}
			<div class="mt-3 space-y-3">
				<div class="space-y-1">
					<Label class="text-xs">Access Key ID</Label>
					<div class="flex items-center gap-1">
						<Input readonly value={creds.access_key_id} class="h-8 font-mono text-xs" />
						<Tooltip.Root>
							<Tooltip.Trigger>
								{#snippet child({ props })}
									<Button
										variant="ghost"
										size="icon"
										class="h-8 w-8 shrink-0"
										onclick={() => copyToClipboard(creds!.access_key_id, 'access_key')}
										{...props}
									>
										{#if copied === 'access_key'}<Check
												class="h-3.5 w-3.5 text-emerald-500"
											/>{:else}<Copy class="h-3.5 w-3.5" />{/if}
									</Button>
								{/snippet}
							</Tooltip.Trigger>
							<Tooltip.Content>{copied === 'access_key' ? 'Copied!' : 'Copy'}</Tooltip.Content>
						</Tooltip.Root>
					</div>
				</div>
				<div class="space-y-1">
					<Label class="text-xs">Secret Access Key</Label>
					<div class="flex items-center gap-1">
						<Input
							readonly
							type={showSecret ? 'text' : 'password'}
							value={creds.secret_access_key}
							class="h-8 font-mono text-xs"
						/>
						<Tooltip.Root>
							<Tooltip.Trigger>
								{#snippet child({ props })}
									<Button
										variant="ghost"
										size="icon"
										class="h-8 w-8 shrink-0"
										onclick={() => (showSecret = !showSecret)}
										{...props}
									>
										{#if showSecret}<EyeOff class="h-3.5 w-3.5" />{:else}<Eye
												class="h-3.5 w-3.5"
											/>{/if}
									</Button>
								{/snippet}
							</Tooltip.Trigger>
							<Tooltip.Content>{showSecret ? 'Hide' : 'Reveal'}</Tooltip.Content>
						</Tooltip.Root>
						<Tooltip.Root>
							<Tooltip.Trigger>
								{#snippet child({ props })}
									<Button
										variant="ghost"
										size="icon"
										class="h-8 w-8 shrink-0"
										onclick={() => copyToClipboard(creds!.secret_access_key, 'secret_key')}
										{...props}
									>
										{#if copied === 'secret_key'}<Check
												class="h-3.5 w-3.5 text-emerald-500"
											/>{:else}<Copy class="h-3.5 w-3.5" />{/if}
									</Button>
								{/snippet}
							</Tooltip.Trigger>
							<Tooltip.Content>{copied === 'secret_key' ? 'Copied!' : 'Copy'}</Tooltip.Content>
						</Tooltip.Root>
					</div>
				</div>
				{#if creds.endpoint_url}
					<div class="space-y-1">
						<Label class="text-xs">S3 Endpoint URL</Label>
						<div class="flex items-center gap-1">
							<Input readonly value={creds.endpoint_url} class="h-8 font-mono text-xs" />
							<Tooltip.Root>
								<Tooltip.Trigger>
									{#snippet child({ props })}
										<Button
											variant="ghost"
											size="icon"
											class="h-8 w-8 shrink-0"
											onclick={() => copyToClipboard(creds!.endpoint_url, 'endpoint')}
											{...props}
										>
											{#if copied === 'endpoint'}<Check
													class="h-3.5 w-3.5 text-emerald-500"
												/>{:else}<Copy class="h-3.5 w-3.5" />{/if}
										</Button>
									{/snippet}
								</Tooltip.Trigger>
								<Tooltip.Content>{copied === 'endpoint' ? 'Copied!' : 'Copy'}</Tooltip.Content>
							</Tooltip.Root>
						</div>
					</div>
				{/if}
			</div>
		{:else}
			<p class="mt-3 text-center text-sm text-muted-foreground">Could not load S3 credentials.</p>
		{/if}
	{/await}
</div>
