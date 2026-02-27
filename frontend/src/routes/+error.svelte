<script lang="ts">
	import { page } from '$app/stores';
	import Button from '$lib/components/ui/Button.svelte';
</script>

<div class="flex min-h-screen items-center justify-center bg-surface-50 dark:bg-surface-950">
	<div class="text-center">
		<h1 class="text-6xl font-bold text-surface-300 dark:text-surface-700">
			{$page.status}
		</h1>
		<p class="mt-4 text-lg text-surface-600 dark:text-surface-400">
			{$page.error?.message ?? 'Something went wrong'}
		</p>
		<div class="mt-8">
			<Button onclick={() => window.location.href = '/'}>
				Go Home
			</Button>
		</div>
	</div>
</div>
