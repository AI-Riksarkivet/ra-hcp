<script lang="ts">
	import { LogOut, PanelLeftClose, PanelLeft } from 'lucide-svelte';
	import { Avatar, Tooltip } from 'bits-ui';
	import ThemeToggle from './ThemeToggle.svelte';

	interface Props {
		collapsed: boolean;
		ontoggle: () => void;
		username: string;
	}

	let { collapsed, ontoggle, username }: Props = $props();

	let initials = $derived(
		username
			.split(/[\s._@-]+/)
			.filter(Boolean)
			.slice(0, 2)
			.map((s) => s[0].toUpperCase())
			.join('') || 'U'
	);
</script>

<header
	class="flex h-16 items-center justify-between border-b border-surface-200 bg-white px-4 dark:border-surface-800 dark:bg-surface-900"
>
	<div class="flex items-center gap-3">
		<Tooltip.Root>
			<Tooltip.Trigger
				onclick={ontoggle}
				class="rounded-lg p-2 text-surface-500 transition-colors hover:bg-surface-100 hover:text-surface-700 dark:text-surface-400 dark:hover:bg-surface-800 dark:hover:text-surface-200"
			>
				{#if collapsed}
					<PanelLeft class="h-5 w-5" />
				{:else}
					<PanelLeftClose class="h-5 w-5" />
				{/if}
			</Tooltip.Trigger>
			<Tooltip.Portal>
				<Tooltip.Content
					sideOffset={8}
					class="z-50 rounded-lg border border-surface-200 bg-white px-3 py-1.5 text-sm shadow-lg dark:border-surface-700 dark:bg-surface-800"
				>
					{collapsed ? 'Expand sidebar' : 'Collapse sidebar'}
				</Tooltip.Content>
			</Tooltip.Portal>
		</Tooltip.Root>
		<h1 class="text-lg font-semibold text-surface-900 dark:text-surface-100">HCP Admin Console</h1>
	</div>

	<div class="flex items-center gap-3">
		<ThemeToggle />

		<div class="flex items-center gap-2">
			<Avatar.Root
				class="flex h-8 w-8 items-center justify-center rounded-full bg-primary-100 text-xs font-semibold text-primary-700 dark:bg-primary-900/30 dark:text-primary-400"
			>
				<Avatar.Fallback>{initials}</Avatar.Fallback>
			</Avatar.Root>
			<span class="hidden text-sm font-medium text-surface-700 dark:text-surface-300 sm:inline">
				{username}
			</span>
		</div>

		<Tooltip.Root>
			<Tooltip.Trigger
				class="inline-flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-surface-600 transition-colors hover:bg-surface-100 hover:text-surface-900 dark:text-surface-400 dark:hover:bg-surface-800 dark:hover:text-surface-100"
			>
				<a href="/logout" class="inline-flex items-center gap-2">
					<LogOut class="h-4 w-4" />
					<span class="hidden sm:inline">Logout</span>
				</a>
			</Tooltip.Trigger>
			<Tooltip.Portal>
				<Tooltip.Content
					sideOffset={8}
					class="z-50 rounded-lg border border-surface-200 bg-white px-3 py-1.5 text-sm shadow-lg sm:hidden dark:border-surface-700 dark:bg-surface-800"
				>
					Sign out
				</Tooltip.Content>
			</Tooltip.Portal>
		</Tooltip.Root>
	</div>
</header>
