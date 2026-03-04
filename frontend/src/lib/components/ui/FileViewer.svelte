<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
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
				'txt',
				'md',
				'markdown',
				'json',
				'csv',
				'tsv',
				'xml',
				'yaml',
				'yml',
				'toml',
				'ini',
				'cfg',
				'conf',
				'log',
				'env',
				'sh',
				'bash',
				'zsh',
				'fish',
				'js',
				'ts',
				'jsx',
				'tsx',
				'mjs',
				'cjs',
				'py',
				'rb',
				'rs',
				'go',
				'java',
				'kt',
				'c',
				'cpp',
				'h',
				'hpp',
				'cs',
				'swift',
				'r',
				'lua',
				'pl',
				'php',
				'sql',
				'html',
				'css',
				'scss',
				'less',
				'svelte',
				'vue',
				'dockerfile',
				'makefile',
				'gitignore',
				'editorconfig',
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
			textContent =
				text.length > 512_000 ? text.slice(0, 512_000) + '\n\n... (truncated at 500KB)' : text;
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

<Dialog.Root
	bind:open
	onOpenChange={(o) => {
		if (!o) onclose();
	}}
>
	<Dialog.Content showCloseButton={false} class="sm:max-w-6xl h-[90vh] flex flex-col p-0 gap-0">
		<!-- Header -->
		<div class="flex shrink-0 items-center justify-between border-b px-4 py-3">
			<div class="flex min-w-0 items-center gap-3">
				<FileText class="h-5 w-5 shrink-0 text-muted-foreground" />
				<div class="min-w-0">
					<Dialog.Title class="truncate text-sm font-semibold">
						{filename}
					</Dialog.Title>
					<Dialog.Description class="text-xs text-muted-foreground">
						{#if size != null}{formatBytes(size)} &middot;
						{/if}.{ext} file
					</Dialog.Description>
				</div>
			</div>
			<div class="flex items-center gap-2">
				<Button variant="ghost" size="icon" href={url} download>
					<Download class="h-4 w-4" />
					<span class="sr-only">Download</span>
				</Button>
				<Button variant="ghost" size="icon" onclick={onclose}>
					<X class="h-5 w-5" />
					<span class="sr-only">Close</span>
				</Button>
			</div>
		</div>

		<!-- Content -->
		{#if category === 'image'}
			<div class="flex flex-1 items-center justify-center overflow-auto bg-muted/50 p-4">
				<img src={url} alt={filename} class="max-h-full max-w-full rounded object-contain" />
			</div>
		{:else if category === 'video'}
			<div class="flex flex-1 items-center justify-center overflow-auto bg-muted/50 p-4">
				<video controls class="max-h-full max-w-full rounded" src={url}>
					<track kind="captions" />
					Your browser does not support this video.
				</video>
			</div>
		{:else if category === 'audio'}
			<div class="flex flex-1 items-center justify-center overflow-auto bg-muted/50 p-4">
				<div class="flex flex-col items-center gap-4">
					<div class="flex h-24 w-24 items-center justify-center rounded-full bg-primary/10">
						<FileText class="h-10 w-10 text-primary" />
					</div>
					<audio controls src={url}> Your browser does not support this audio. </audio>
				</div>
			</div>
		{:else if category === 'pdf'}
			<div class="flex-1 overflow-hidden bg-muted/50">
				<iframe src={url} class="h-full w-full border-0" title={filename}></iframe>
			</div>
		{:else if category === 'text'}
			<div class="flex flex-1 flex-col overflow-hidden">
				{#if loading}
					<div class="flex flex-1 items-center justify-center gap-2 text-muted-foreground">
						<Loader2 class="h-5 w-5 animate-spin" />
						<span>Loading file content...</span>
					</div>
				{:else if error}
					<div class="flex flex-1 flex-col items-center justify-center gap-3">
						<AlertCircle class="h-8 w-8 text-destructive" />
						<p class="text-sm text-destructive">{error}</p>
						<Button variant="secondary" size="sm" onclick={() => fetchText(url)}>Retry</Button>
					</div>
				{:else if textContent != null}
					<div class="flex-1 overflow-auto p-4">
						<pre
							class="whitespace-pre-wrap break-words font-mono text-sm leading-relaxed text-foreground">{textContent}</pre>
					</div>
				{:else}
					<div class="flex flex-1 items-center justify-center text-muted-foreground">
						<span>No content to display</span>
					</div>
				{/if}
			</div>
		{:else}
			<!-- Unsupported -->
			<div
				class="flex flex-1 flex-col items-center justify-center gap-3 bg-muted/50 p-8 text-center"
			>
				<div class="flex h-16 w-16 items-center justify-center rounded-full bg-muted">
					<FileText class="h-8 w-8 text-muted-foreground" />
				</div>
				<p class="text-sm font-medium">
					Preview not available for .{ext} files
				</p>
				<p class="text-xs text-muted-foreground">Download the file to view it locally</p>
				<Button href={url} download class="mt-2">
					<Download class="h-4 w-4" />
					Download
				</Button>
				<p class="mt-4 text-xs text-muted-foreground">
					Parquet, DuckDB, and LanceDB viewers coming soon
				</p>
			</div>
		{/if}
	</Dialog.Content>
</Dialog.Root>
