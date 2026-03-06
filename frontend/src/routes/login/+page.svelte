<script lang="ts">
	import { enhance } from '$app/forms';
	import { Server } from 'lucide-svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';

	let { form }: { form: { error?: string } | null } = $props();
	let loading = $state(false);
</script>

<svelte:head>
	<title>Login - HCP Admin Console</title>
</svelte:head>

<div class="flex min-h-screen items-center justify-center bg-background px-4">
	<div class="w-full max-w-sm">
		<div class="mb-8 text-center">
			<div class="mx-auto mb-4 flex h-14 w-14 items-center justify-center rounded-xl bg-primary/10">
				<Server class="h-7 w-7 text-primary" />
			</div>
			<h1 class="text-2xl font-bold">HCP Admin Console</h1>
			<p class="mt-1 text-sm text-muted-foreground">Sign in to your HCP tenant</p>
		</div>

		{#if form?.error}
			<div
				class="mb-4 rounded-lg border border-destructive/20 bg-destructive/10 p-3 text-sm text-destructive"
			>
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
			class="rounded-xl border bg-card p-6 shadow-sm"
		>
			<div class="space-y-4">
				<div class="space-y-2">
					<Label for="tenant">Tenant</Label>
					<Input id="tenant" name="tenant" placeholder="Tenant name (optional)" />
				</div>
				<div class="space-y-2">
					<Label for="username">Username</Label>
					<Input id="username" name="username" placeholder="Enter your HCP username" required />
				</div>
				<div class="space-y-2">
					<Label for="password">Password</Label>
					<Input
						id="password"
						type="password"
						name="password"
						placeholder="Enter your password"
						required
					/>
				</div>
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
