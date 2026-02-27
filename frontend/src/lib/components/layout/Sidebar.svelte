<script lang="ts">
	import { page } from '$app/stores';
	import {
		LayoutDashboard,
		Database,
		Building2,
		Users,
		Server
	} from 'lucide-svelte';
	import { cn } from '$lib/utils/cn.js';
	import { onMount } from 'svelte';

	interface Props {
		collapsed: boolean;
	}

	let { collapsed }: Props = $props();
	let sidebarEl: HTMLElement | undefined = $state();

	const navItems = [
		{ href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
		{ href: '/buckets', label: 'Buckets', icon: Database },
		{ href: '/tenants', label: 'Tenants', icon: Building2 },
		{ href: '/users', label: 'Users', icon: Users }
	] as const;

	onMount(async () => {
		if (!sidebarEl) return;
		const { gsap } = await import('gsap');

		$effect(() => {
			gsap.to(sidebarEl!, {
				width: collapsed ? 64 : 256,
				duration: 0.3,
				ease: 'power2.out'
			});
		});
	});
</script>

<aside
	bind:this={sidebarEl}
	class="flex h-full flex-col border-r border-surface-200 bg-white dark:border-surface-800 dark:bg-surface-900"
	style="width: {collapsed ? '64px' : '256px'}"
>
	<div class="flex h-16 items-center border-b border-surface-200 px-4 dark:border-surface-800">
		<div class="flex items-center gap-3 overflow-hidden">
			<Server class="h-6 w-6 shrink-0 text-primary-600 dark:text-primary-400" />
			{#if !collapsed}
				<span class="whitespace-nowrap text-lg font-bold text-surface-900 dark:text-surface-100">
					HCP App
				</span>
			{/if}
		</div>
	</div>

	<nav class="flex-1 space-y-1 p-3">
		{#each navItems as item}
			{@const active = $page.url.pathname.startsWith(item.href)}
			<a
				href={item.href}
				class={cn(
					'flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium transition-colors',
					active
						? 'bg-primary-50 text-primary-700 dark:bg-primary-900/20 dark:text-primary-400'
						: 'text-surface-600 hover:bg-surface-100 hover:text-surface-900 dark:text-surface-400 dark:hover:bg-surface-800 dark:hover:text-surface-100'
				)}
				title={collapsed ? item.label : undefined}
			>
				<item.icon class="h-5 w-5 shrink-0" />
				{#if !collapsed}
					<span class="whitespace-nowrap">{item.label}</span>
				{/if}
			</a>
		{/each}
	</nav>
</aside>
