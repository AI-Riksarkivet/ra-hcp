<script lang="ts">
	import { LogOut } from 'lucide-svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as Avatar from '$lib/components/ui/avatar/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import ThemeToggle from './ThemeToggle.svelte';

	interface Props {
		username: string;
	}

	let { username }: Props = $props();

	let initials = $derived(
		username
			.split(/[\s._@-]+/)
			.filter(Boolean)
			.slice(0, 2)
			.map((s) => s[0].toUpperCase())
			.join('') || 'U'
	);
</script>

<header class="flex h-16 shrink-0 items-center gap-2 border-b px-4 transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12">
	<div class="flex flex-1 items-center gap-2">
		<Sidebar.Trigger />
		<Separator orientation="vertical" class="mx-2 data-[orientation=vertical]:h-4" />
		<h1 class="text-lg font-semibold">HCP Admin Console</h1>
	</div>

	<div class="flex items-center gap-2">
		<ThemeToggle />

		<div class="flex items-center gap-2">
			<Avatar.Root class="h-8 w-8">
				<Avatar.Fallback class="bg-primary/10 text-xs font-semibold text-primary">{initials}</Avatar.Fallback>
			</Avatar.Root>
			<span class="hidden text-sm font-medium sm:inline">
				{username}
			</span>
		</div>

		<Tooltip.Root>
			<Tooltip.Trigger>
				{#snippet child({ props })}
					<a href="/logout" {...props}>
						<Button variant="ghost" size="sm">
							<LogOut class="h-4 w-4" />
							<span class="hidden sm:inline">Logout</span>
						</Button>
					</a>
				{/snippet}
			</Tooltip.Trigger>
			<Tooltip.Content class="sm:hidden">
				Sign out
			</Tooltip.Content>
		</Tooltip.Root>
	</div>
</header>
