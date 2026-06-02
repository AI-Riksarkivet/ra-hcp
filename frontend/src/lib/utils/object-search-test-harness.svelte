<script lang="ts">
	import { objectListQuery } from './object-search.js';

	// Self-contained harness for interaction tests: a search box whose computed
	// server-side listing query (prefix + flat) is rendered for assertions. This
	// exercises the exact derivation the bucket object browser ships with.
	let {
		navigatedPrefix = '',
		initialFlat = false,
	}: {
		navigatedPrefix?: string;
		initialFlat?: boolean;
	} = $props();

	let search = $state('');
	let q = $derived(objectListQuery(navigatedPrefix, search, initialFlat));
</script>

<div class="space-y-2 p-4">
	<input
		class="rounded border px-3 py-1 text-sm"
		placeholder="Search…"
		data-testid="search"
		bind:value={search}
	/>
	<div data-testid="query-prefix">{q.prefix}</div>
	<div data-testid="query-flat">{String(q.flat)}</div>
</div>
