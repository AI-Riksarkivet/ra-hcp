<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Plus, X } from 'lucide-svelte';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import SaveButton from '$lib/components/ui/save-button.svelte';
	import { toast } from 'svelte-sonner';
	import {
		get_search_security,
		update_search_security,
		type SearchSecurity,
	} from '$lib/tenant-info.remote.js';

	let {
		tenant,
	}: {
		tenant: string;
	} = $props();

	let securityData = $derived(get_search_security({ tenant }));
	let security = $derived((securityData?.current ?? {}) as SearchSecurity);

	// ---- Local state ----
	let syncVersion = $state(0);
	let localAllowAddresses = $state<string[]>([]);
	let localDenyAddresses = $state<string[]>([]);
	let localAllowIfInBoth = $state(false);

	$effect(() => {
		const s = security;
		void syncVersion;
		localAllowAddresses = [...(s.ipSettings?.allowAddresses ?? [])];
		localDenyAddresses = [...(s.ipSettings?.denyAddresses ?? [])];
		localAllowIfInBoth = s.ipSettings?.allowIfInBothLists ?? false;
	});

	function arraysEqual(a: string[], b: string[]): boolean {
		if (a.length !== b.length) return false;
		return a.every((v, i) => v === b[i]);
	}

	let dirty = $derived(
		!arraysEqual(localAllowAddresses, security.ipSettings?.allowAddresses ?? []) ||
			!arraysEqual(localDenyAddresses, security.ipSettings?.denyAddresses ?? []) ||
			localAllowIfInBoth !== (security.ipSettings?.allowIfInBothLists ?? false)
	);

	let saving = $state(false);

	async function save() {
		if (!securityData) return;
		saving = true;
		try {
			await update_search_security({
				tenant,
				body: {
					ipSettings: {
						allowAddresses: localAllowAddresses.filter(Boolean),
						denyAddresses: localDenyAddresses.filter(Boolean),
						allowIfInBothLists: localAllowIfInBoth,
					},
				},
			}).updates(securityData);
			syncVersion++;
			toast.success('Search security updated');
		} catch {
			toast.error('Failed to update search security');
		} finally {
			saving = false;
		}
	}

	// ---- IP input helpers ----
	let allowInput = $state('');
	let denyInput = $state('');

	function addAllowAddress() {
		const val = allowInput.trim();
		if (val && !localAllowAddresses.includes(val)) {
			localAllowAddresses = [...localAllowAddresses, val];
		}
		allowInput = '';
	}

	function removeAllowAddress(index: number) {
		localAllowAddresses = localAllowAddresses.filter((_, i) => i !== index);
	}

	function addDenyAddress() {
		const val = denyInput.trim();
		if (val && !localDenyAddresses.includes(val)) {
			localDenyAddresses = [...localDenyAddresses, val];
		}
		denyInput = '';
	}

	function removeDenyAddress(index: number) {
		localDenyAddresses = localDenyAddresses.filter((_, i) => i !== index);
	}

	function handleAllowKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addAllowAddress();
		}
	}

	function handleDenyKeydown(e: KeyboardEvent) {
		if (e.key === 'Enter') {
			e.preventDefault();
			addDenyAddress();
		}
	}
</script>

{#await securityData}
	<CardSkeleton />
{:then}
	<Card.Root>
		<Card.Header>
			<Card.Title>Search Security</Card.Title>
			<Card.Description>
				Controls which IP addresses can access the HCP metadata query API.
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-6">
			<!-- Allow list -->
			<div class="space-y-2">
				<Label>Allow List</Label>
				<div class="flex gap-2">
					<Input
						placeholder="IP address or CIDR (e.g. 10.0.0.0/8)"
						bind:value={allowInput}
						onkeydown={handleAllowKeydown}
					/>
					<Button variant="outline" size="icon" onclick={addAllowAddress}>
						<Plus class="h-4 w-4" />
					</Button>
				</div>
				{#if localAllowAddresses.length > 0}
					<div class="flex flex-wrap gap-1.5">
						{#each localAllowAddresses as addr, i (addr)}
							<Badge variant="secondary" class="gap-1 pr-1">
								{addr}
								<button
									class="rounded-full p-0.5 hover:bg-muted-foreground/20"
									onclick={() => removeAllowAddress(i)}
								>
									<X class="h-3 w-3" />
								</button>
							</Badge>
						{/each}
					</div>
				{:else}
					<p class="text-xs text-muted-foreground">
						No allow list configured. All addresses are allowed by default.
					</p>
				{/if}
			</div>

			<!-- Deny list -->
			<div class="space-y-2">
				<Label>Deny List</Label>
				<div class="flex gap-2">
					<Input
						placeholder="IP address or CIDR (e.g. 192.168.1.0/24)"
						bind:value={denyInput}
						onkeydown={handleDenyKeydown}
					/>
					<Button variant="outline" size="icon" onclick={addDenyAddress}>
						<Plus class="h-4 w-4" />
					</Button>
				</div>
				{#if localDenyAddresses.length > 0}
					<div class="flex flex-wrap gap-1.5">
						{#each localDenyAddresses as addr, i (addr)}
							<Badge variant="destructive" class="gap-1 pr-1">
								{addr}
								<button
									class="rounded-full p-0.5 hover:bg-destructive-foreground/20"
									onclick={() => removeDenyAddress(i)}
								>
									<X class="h-3 w-3" />
								</button>
							</Badge>
						{/each}
					</div>
				{:else}
					<p class="text-xs text-muted-foreground">No deny list configured.</p>
				{/if}
			</div>

			<!-- Toggle -->
			<div class="flex items-center gap-2">
				<Switch id="allow-if-both" bind:checked={localAllowIfInBoth} />
				<Label for="allow-if-both" class="text-sm">Allow if in both lists</Label>
			</div>
			<p class="text-xs text-muted-foreground">
				When enabled, addresses that appear in both allow and deny lists will be allowed.
			</p>
		</Card.Content>
		<Card.Footer>
			<SaveButton {dirty} {saving} onclick={save} />
		</Card.Footer>
	</Card.Root>
{/await}
