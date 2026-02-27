<script lang="ts">
	import { ArrowLeft, File, Folder } from 'lucide-svelte';
	import Card from '$lib/components/ui/Card.svelte';
	import DataTable from '$lib/components/ui/DataTable.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import { formatBytes, formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	let { data } = $props();

	const columns = [
		{
			key: 'key',
			label: 'Name',
			render: (obj: { key: string; size: number }) => {
				const name = obj.key.split('/').pop() ?? obj.key;
				return obj.size === 0 && obj.key.endsWith('/') ? `📁 ${name}` : name;
			}
		},
		{
			key: 'size',
			label: 'Size',
			render: (obj: { size: number }) => formatBytes(obj.size),
			class: 'w-32'
		},
		{
			key: 'last_modified',
			label: 'Last Modified',
			render: (obj: { last_modified: string }) => formatDate(obj.last_modified),
			class: 'w-48'
		}
	];

	function navigatePrefix(prefix: string) {
		goto(`/buckets/${data.bucket}?prefix=${encodeURIComponent(prefix)}`);
	}

	let parentPrefix = $derived(() => {
		if (!data.prefix) return null;
		const parts = data.prefix.replace(/\/$/, '').split('/');
		parts.pop();
		return parts.length > 0 ? parts.join('/') + '/' : '';
	});
</script>

<svelte:head>
	<title>{data.bucket} - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center gap-4">
		<a
			href="/buckets"
			class="rounded-lg p-2 text-surface-500 transition-colors hover:bg-surface-100 hover:text-surface-700 dark:text-surface-400 dark:hover:bg-surface-800"
		>
			<ArrowLeft class="h-5 w-5" />
		</a>
		<div>
			<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-100">{data.bucket}</h2>
			{#if data.prefix}
				<p class="mt-1 text-sm text-surface-500 dark:text-surface-400">
					Prefix: <code class="rounded bg-surface-100 px-1.5 py-0.5 font-mono text-xs dark:bg-surface-800">{data.prefix}</code>
				</p>
			{/if}
		</div>
		<Badge>{data.keyCount} objects</Badge>
	</div>

	{#if data.prefix}
		<button
			onclick={() => navigatePrefix(parentPrefix?.() ?? '')}
			class="flex items-center gap-2 text-sm text-primary-600 hover:underline dark:text-primary-400"
		>
			<Folder class="h-4 w-4" />
			.. (parent directory)
		</button>
	{/if}

	<DataTable
		{columns}
		data={data.objects}
		onrowclick={(obj) => {
			if (obj.size === 0 && obj.key.endsWith('/')) {
				navigatePrefix(obj.key);
			}
		}}
		emptyMessage="No objects in this bucket"
	/>
</div>
