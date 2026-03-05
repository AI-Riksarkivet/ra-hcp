<script lang="ts">
	import { LogOut, Moon, Sun, ChevronDown } from 'lucide-svelte';
	import { toggleMode, mode } from 'mode-watcher';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';

	interface Props {
		username: string;
		tenant?: string;
	}

	let { username, tenant }: Props = $props();
</script>

<header
	class="flex h-16 shrink-0 items-center gap-2 border-b px-4 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12"
>
	<div class="flex flex-1 items-center gap-2">
		<Sidebar.Trigger />
		<Separator orientation="vertical" class="mx-2 data-[orientation=vertical]:h-4" />
		<h1 class="text-lg font-semibold">
			{#if tenant}
				Tenant: {tenant}
			{:else}
				HCP Admin Console
			{/if}
		</h1>
	</div>

	<DropdownMenu.Root>
		<DropdownMenu.Trigger>
			{#snippet child({ props })}
				<Button {...props} variant="outline" size="sm" class="gap-1.5">
					<span class="text-sm font-medium">{username}</span>
					<ChevronDown class="h-4 w-4 opacity-50" />
				</Button>
			{/snippet}
		</DropdownMenu.Trigger>
		<DropdownMenu.Content align="end" class="w-48">
			<DropdownMenu.Label>{username}</DropdownMenu.Label>
			<DropdownMenu.Separator />
			<DropdownMenu.Item onclick={toggleMode}>
				{#if mode.current === 'dark'}
					<Sun class="h-4 w-4" />
					Light mode
				{:else}
					<Moon class="h-4 w-4" />
					Dark mode
				{/if}
			</DropdownMenu.Item>
			<DropdownMenu.Separator />
			<DropdownMenu.Item
				variant="destructive"
				onclick={() => {
					window.location.href = '/logout';
				}}
			>
				<LogOut class="h-4 w-4" />
				Logout
			</DropdownMenu.Item>
		</DropdownMenu.Content>
	</DropdownMenu.Root>
</header>
