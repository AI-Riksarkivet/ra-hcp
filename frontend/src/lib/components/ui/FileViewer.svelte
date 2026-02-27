<script lang="ts">
	import { Dialog } from 'bits-ui';
	import { X, Download, FileText, Loader2, AlertCircle } from 'lucide-svelte';
	import { formatBytes } from '$lib/utils/format.js';

	interface Props {
		open: boolean;
		url: string;
		filename: string;
		size?: number;
		onclose: () => void;
	}

	let { open = $bindable(), url, filename, size, onclose }: Props = $props();

	let textContent = $state<string | null>(null);
	let loading = $state(false);
	let error = $state<string | null>(null);

	const ext = $derived(filename.split('.').pop()?.toLowerCase() ?? '');
	const category = $derived(getCategory(ext));

	function getCategory(e: string): 'image' | 'video' | 'audio' | 'pdf' | 'text' | 'unsupported' {
		if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp', 'ico', 'avif'].includes(e))
			return 'image';
		if (['mp4', 'webm', 'ogg', 'mov'].includes(e)) return 'video';
		if (['mp3', 'wav', 'flac', 'aac', 'm4a'].includes(e)) return 'audio';
		if (e === 'pdf') return 'pdf';
		if (
			[
				'txt', 'md', 'markdown', 'json', 'csv', 'tsv', 'xml', 'yaml', 'yml', 'toml',
				'ini', 'cfg', 'conf', 'log', 'env', 'sh', 'bash', 'zsh', 'fish',
				'js', 'ts', 'jsx', 'tsx', 'mjs', 'cjs',
				'py', 'rb', 'rs', 'go', 'java', 'kt', 'c', 'cpp', 'h', 'hpp', 'cs',
				'swift', 'r', 'lua', 'pl', 'php', 'sql',
				'html', 'css', 'scss', 'less', 'svelte', 'vue',
				'dockerfile', 'makefile', 'gitignore', 'editorconfig'
			].includes(e)
		)
			return 'text';
		return 'unsupported';
	}

	async function fetchText(fetchUrl: string) {
		loading = true;
		error = null;
		textContent = null;
		try {
			const res = await fetch(fetchUrl, { credentials: 'same-origin' });
			if (!res.ok) {
				throw new Error(`Failed to load file (HTTP ${res.status})`);
			}
			const text = await res.text();
			textContent = text.length > 512_000
				? text.slice(0, 512_000) + '\n\n... (truncated at 500KB)'
				: text;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load file';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		if (open && category === 'text' && url) {
			fetchText(url);
		}
	});
</script>

<Dialog.Root bind:open onOpenChange={(o) => { if (!o) onclose(); }}>
	<Dialog.Portal>
		<Dialog.Overlay class="fixed inset-0 z-50 bg-black/60" />
		<Dialog.Content
			class="fixed inset-4 z-50 flex flex-col overflow-hidden rounded-xl border border-surface-200 bg-white shadow-2xl dark:border-surface-800 dark:bg-surface-900 sm:inset-8 lg:inset-16"
		>
			<!-- Header -->
			<div class="flex shrink-0 items-center justify-between border-b border-surface-200 px-4 py-3 dark:border-surface-800">
				<div class="flex min-w-0 items-center gap-3">
					<FileText class="h-5 w-5 shrink-0 text-surface-400" />
					<div class="min-w-0">
						<Dialog.Title class="truncate text-sm font-semibold text-surface-900 dark:text-surface-100">
							{filename}
						</Dialog.Title>
						<p class="text-xs text-surface-500">
							{#if size != null}{formatBytes(size)} &middot; {/if}.{ext} file
						</p>
					</div>
				</div>
				<div class="flex items-center gap-2">
					<a
						href={url}
						download
						class="rounded-lg p-2 text-surface-400 transition-colors hover:bg-surface-100 hover:text-surface-700 dark:hover:bg-surface-800 dark:hover:text-surface-300"
						title="Download"
					>
						<Download class="h-4 w-4" />
					</a>
					<button
						onclick={onclose}
						class="rounded-lg p-2 text-surface-400 transition-colors hover:bg-surface-100 hover:text-surface-700 dark:hover:bg-surface-800 dark:hover:text-surface-300"
					>
						<X class="h-5 w-5" />
					</button>
				</div>
			</div>

			<!-- Content -->
			{#if category === 'image'}
				<div class="flex flex-1 items-center justify-center overflow-auto bg-surface-50 p-4 dark:bg-surface-950">
					<img
						src={url}
						alt={filename}
						class="max-h-full max-w-full rounded object-contain"
					/>
				</div>
			{:else if category === 'video'}
				<div class="flex flex-1 items-center justify-center overflow-auto bg-surface-50 p-4 dark:bg-surface-950">
					<!-- svelte-ignore a11y_media_has_caption -->
					<video controls class="max-h-full max-w-full rounded" src={url}>
						Your browser does not support this video.
					</video>
				</div>
			{:else if category === 'audio'}
				<div class="flex flex-1 items-center justify-center overflow-auto bg-surface-50 p-4 dark:bg-surface-950">
					<div class="flex flex-col items-center gap-4">
						<div class="flex h-24 w-24 items-center justify-center rounded-full bg-primary-100 dark:bg-primary-900/30">
							<FileText class="h-10 w-10 text-primary-600 dark:text-primary-400" />
						</div>
						<audio controls src={url}>
							Your browser does not support this audio.
						</audio>
					</div>
				</div>
			{:else if category === 'pdf'}
				<div class="flex-1 overflow-hidden bg-surface-50 dark:bg-surface-950">
					<iframe src={url} class="h-full w-full border-0" title={filename}></iframe>
				</div>
			{:else if category === 'text'}
				<div class="flex flex-1 flex-col overflow-hidden">
					{#if loading}
						<div class="flex flex-1 items-center justify-center gap-2 text-surface-500">
							<Loader2 class="h-5 w-5 animate-spin" />
							<span>Loading file content...</span>
						</div>
					{:else if error}
						<div class="flex flex-1 flex-col items-center justify-center gap-3">
							<AlertCircle class="h-8 w-8 text-red-400" />
							<p class="text-sm text-red-500">{error}</p>
							<button
								onclick={() => fetchText(url)}
								class="rounded-lg bg-surface-100 px-3 py-1.5 text-sm font-medium text-surface-700 hover:bg-surface-200 dark:bg-surface-800 dark:text-surface-300 dark:hover:bg-surface-700"
							>
								Retry
							</button>
						</div>
					{:else if textContent != null}
						<div class="flex-1 overflow-auto bg-white p-4 dark:bg-surface-900">
							<pre class="whitespace-pre-wrap break-words font-mono text-sm leading-relaxed text-surface-800 dark:text-surface-200">{textContent}</pre>
						</div>
					{:else}
						<div class="flex flex-1 items-center justify-center text-surface-400">
							<span>No content to display</span>
						</div>
					{/if}
				</div>
			{:else}
				<!-- Unsupported / future: parquet, duckdb, lancedb -->
				<div class="flex flex-1 flex-col items-center justify-center gap-3 bg-surface-50 p-8 text-center dark:bg-surface-950">
					<div class="flex h-16 w-16 items-center justify-center rounded-full bg-surface-100 dark:bg-surface-800">
						<FileText class="h-8 w-8 text-surface-400" />
					</div>
					<p class="text-sm font-medium text-surface-700 dark:text-surface-300">
						Preview not available for .{ext} files
					</p>
					<p class="text-xs text-surface-500">
						Download the file to view it locally
					</p>
					<a
						href={url}
						download
						class="mt-2 inline-flex items-center gap-2 rounded-lg bg-primary-600 px-4 py-2 text-sm font-medium text-white hover:bg-primary-700"
					>
						<Download class="h-4 w-4" />
						Download
					</a>
					<p class="mt-4 text-xs text-surface-400">
						Parquet, DuckDB, and LanceDB viewers coming soon
					</p>
				</div>
			{/if}
		</Dialog.Content>
	</Dialog.Portal>
</Dialog.Root>
