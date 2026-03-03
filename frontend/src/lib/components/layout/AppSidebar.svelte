<script lang="ts">
	import { page } from '$app/stores';
	import { LayoutDashboard, Database, Users, Server } from 'lucide-svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';

	const overviewItems = [
		{ href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
	] as const;

	const managementItems = [{ href: '/users', label: 'Users & Groups', icon: Users }] as const;

	const storageItems = [{ href: '/buckets', label: 'Buckets', icon: Database }] as const;
</script>

<Sidebar.Root collapsible="icon">
	<Sidebar.Header>
		<Sidebar.Menu>
			<Sidebar.MenuItem>
				<Sidebar.MenuButton size="lg">
					<div class="flex items-center gap-3 overflow-hidden">
						<Server class="h-6 w-6 shrink-0 text-primary" />
						<span class="whitespace-nowrap text-lg font-bold">HCP App</span>
					</div>
				</Sidebar.MenuButton>
			</Sidebar.MenuItem>
		</Sidebar.Menu>
	</Sidebar.Header>

	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupLabel>Overview</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each overviewItems as item}
						{@const active = $page.url.pathname.startsWith(item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={active} tooltipContent={item.label}>
								{#snippet child({ props })}
									<a href={item.href} {...props}>
										<item.icon class="h-5 w-5 shrink-0" />
										<span>{item.label}</span>
									</a>
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>

		<Sidebar.Group>
			<Sidebar.GroupLabel>Management</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each managementItems as item}
						{@const active = $page.url.pathname.startsWith(item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={active} tooltipContent={item.label}>
								{#snippet child({ props })}
									<a href={item.href} {...props}>
										<item.icon class="h-5 w-5 shrink-0" />
										<span>{item.label}</span>
									</a>
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>

		<Sidebar.Group>
			<Sidebar.GroupLabel>Storage</Sidebar.GroupLabel>
			<Sidebar.GroupContent>
				<Sidebar.Menu>
					{#each storageItems as item}
						{@const active = $page.url.pathname.startsWith(item.href)}
						<Sidebar.MenuItem>
							<Sidebar.MenuButton isActive={active} tooltipContent={item.label}>
								{#snippet child({ props })}
									<a href={item.href} {...props}>
										<item.icon class="h-5 w-5 shrink-0" />
										<span>{item.label}</span>
									</a>
								{/snippet}
							</Sidebar.MenuButton>
						</Sidebar.MenuItem>
					{/each}
				</Sidebar.Menu>
			</Sidebar.GroupContent>
		</Sidebar.Group>
	</Sidebar.Content>
</Sidebar.Root>
