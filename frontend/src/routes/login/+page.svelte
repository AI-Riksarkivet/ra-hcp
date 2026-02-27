<script lang="ts">
	import { enhance } from '$app/forms';
	import { goto } from '$app/navigation';
	import { onMount } from 'svelte';
	import { Server } from 'lucide-svelte';
	import Input from '$lib/components/ui/Input.svelte';
	import Button from '$lib/components/ui/Button.svelte';

	interface Props {
		data: { hasToken: boolean };
		form: { error?: string; success?: boolean } | null;
	}

	let { data, form }: Props = $props();
	let loading = $state(false);

	// Redirect if already logged in
	onMount(() => {
		if (data.hasToken) {
			goto('/dashboard', { replaceState: true });
		}
	});

	// Redirect on successful login
	$effect(() => {
		if (form?.success) {
			goto('/dashboard', { replaceState: true });
		}
	});
</script>

<svelte:head>
	<title>Login - HCP Admin Console</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-surface-50 px-4 dark:bg-surface-950">
	<div class="w-full max-w-sm">
		<div class="mb-8 text-center">
			<div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-primary-100 dark:bg-primary-900/30">
				<Server class="h-7 w-7 text-primary-600 dark:text-primary-400" />
			</div>
			<h1 class="text-2xl font-bold text-surface-900 dark:text-surface-100">HCP Admin Console</h1>
			<p class="mt-1 text-sm text-surface-500 dark:text-surface-400">Sign in to manage your HCP infrastructure</p>
		</div>

		{#if form?.error}
			<div class="mb-4 rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
				{form.error}
			</div>
		{/if}

		<form
			method="POST"
			use:enhance={() => {
				loading = true;
				return async ({ update }) => {
					loading = false;
					await update();
				};
			}}
			class="rounded-xl border border-surface-200 bg-white p-6 shadow-sm dark:border-surface-800 dark:bg-surface-900"
		>
			<div class="space-y-4">
				<Input
					name="username"
					label="Username"
					placeholder="Enter your HCP username"
					required
				/>
				<Input
					type="password"
					name="password"
					label="Password"
					placeholder="Enter your password"
					required
				/>
			</div>
			<div class="mt-6">
				<Button type="submit" class="w-full" disabled={loading}>
					{#if loading}
						Signing in...
					{:else}
						Sign in
					{/if}
				</Button>
			</div>
		</form>
	</div>
</div>
