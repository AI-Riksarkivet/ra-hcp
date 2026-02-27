<script lang="ts">
	import { enhance } from '$app/forms';
	import { invalidateAll } from '$app/navigation';
	import { Dialog, Tooltip, Progress } from 'bits-ui';
	import {
		ArrowLeft, Upload, Trash2, Download, Folder, FileText,
		Image, FileArchive, FileCode, X, CheckCircle, AlertCircle, Loader2
	} from 'lucide-svelte';
	import Button from '$lib/components/ui/Button.svelte';
	import Badge from '$lib/components/ui/Badge.svelte';
	import FileViewer from '$lib/components/ui/FileViewer.svelte';
	import { formatBytes, formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from '$lib/stores/toast.svelte.js';

	// File viewer state
	let viewerOpen = $state(false);
	let viewerUrl = $state('');
	let viewerFilename = $state('');
	let viewerSize = $state(0);

	function openViewer(obj: { key: string; size: number }) {
		viewerUrl = downloadUrl(obj.key);
		viewerFilename = getDisplayName(obj.key);
		viewerSize = obj.size;
		viewerOpen = true;
	}

	interface FileUpload {
		file: File;
		preview: string | null;
		status: 'pending' | 'uploading' | 'done' | 'error';
		progress: number;
		error?: string;
	}

	let { data, form } = $props();
	let uploadOpen = $state(false);
	let selectedFiles = $state<FileUpload[]>([]);
	let uploading = $state(false);
	let dragover = $state(false);

	function navigatePrefix(prefix: string) {
		goto(`/buckets/${data.bucket}?prefix=${encodeURIComponent(prefix)}`);
	}

	function downloadUrl(key: string): string {
		return `/api/v1/buckets/${encodeURIComponent(data.bucket)}/objects/${encodeURIComponent(key)}`;
	}

	function getDisplayName(key: string): string {
		return key.split('/').filter(Boolean).pop() ?? key;
	}

	function isObjFolder(obj: { size: number; key: string }): boolean {
		return obj.size === 0 && obj.key.endsWith('/');
	}

	function getFileIcon(name: string) {
		const ext = name.split('.').pop()?.toLowerCase() ?? '';
		if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return Image;
		if (['zip', 'tar', 'gz', 'rar', '7z'].includes(ext)) return FileArchive;
		if (['js', 'ts', 'py', 'json', 'html', 'css', 'xml', 'yaml', 'yml', 'toml'].includes(ext)) return FileCode;
		return FileText;
	}

	function isImageFile(file: File): boolean {
		return file.type.startsWith('image/');
	}

	function addFiles(files: FileList | null) {
		if (!files) return;
		for (const file of files) {
			const preview = isImageFile(file) ? URL.createObjectURL(file) : null;
			selectedFiles = [...selectedFiles, { file, preview, status: 'pending', progress: 0 }];
		}
	}

	function removeFile(index: number) {
		const removed = selectedFiles[index];
		if (removed.preview) URL.revokeObjectURL(removed.preview);
		selectedFiles = selectedFiles.filter((_, i) => i !== index);
	}

	function handleDrop(e: DragEvent) {
		e.preventDefault();
		dragover = false;
		addFiles(e.dataTransfer?.files ?? null);
	}

	function uploadFile(index: number): Promise<void> {
		return new Promise((resolve) => {
			const item = selectedFiles[index];
			const key = (data.prefix || '') + item.file.name;
			const formData = new FormData();
			formData.append('file', item.file);

			const xhr = new XMLHttpRequest();
			xhr.open('POST', `/api/v1/buckets/${encodeURIComponent(data.bucket)}/objects/${encodeURIComponent(key)}`);

			xhr.upload.onprogress = (e) => {
				if (e.lengthComputable) {
					selectedFiles[index] = { ...selectedFiles[index], progress: Math.round((e.loaded / e.total) * 100) };
				}
			};

			xhr.onload = () => {
				if (xhr.status >= 200 && xhr.status < 300) {
					selectedFiles[index] = { ...selectedFiles[index], status: 'done', progress: 100 };
				} else {
					const err = (() => { try { return JSON.parse(xhr.responseText); } catch { return { detail: 'Upload failed' }; } })();
					selectedFiles[index] = { ...selectedFiles[index], status: 'error', error: err.detail };
				}
				resolve();
			};

			xhr.onerror = () => {
				selectedFiles[index] = { ...selectedFiles[index], status: 'error', error: 'Network error' };
				resolve();
			};

			selectedFiles[index] = { ...selectedFiles[index], status: 'uploading', progress: 0 };
			xhr.send(formData);
		});
	}

	async function uploadAll() {
		if (selectedFiles.length === 0) return;
		uploading = true;

		for (let i = 0; i < selectedFiles.length; i++) {
			if (selectedFiles[i].status === 'pending') {
				await uploadFile(i);
			}
		}

		uploading = false;
		const doneCount = selectedFiles.filter((f) => f.status === 'done').length;
		const errCount = selectedFiles.filter((f) => f.status === 'error').length;
		if (doneCount > 0) toast.success(`Uploaded ${doneCount} file${doneCount !== 1 ? 's' : ''} successfully`);
		if (errCount > 0) toast.error(`${errCount} file${errCount !== 1 ? 's' : ''} failed to upload`);
		await invalidateAll();
	}

	function closeUpload() {
		for (const f of selectedFiles) {
			if (f.preview) URL.revokeObjectURL(f.preview);
		}
		selectedFiles = [];
		uploadOpen = false;
	}

	let allDone = $derived(selectedFiles.length > 0 && selectedFiles.every((f) => f.status === 'done'));
	let totalProgress = $derived.by(() => {
		if (selectedFiles.length === 0) return 0;
		return Math.round(selectedFiles.reduce((sum, f) => sum + f.progress, 0) / selectedFiles.length);
	});

	let parentPrefix = $derived.by(() => {
		if (!data.prefix) return '';
		const parts = data.prefix.replace(/\/$/, '').split('/');
		parts.pop();
		return parts.length > 0 ? parts.join('/') + '/' : '';
	});
</script>

<svelte:head>
	<title>{data.bucket} - HCP Admin Console</title>
</svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-4">
			<Tooltip.Root>
				<Tooltip.Trigger
					class="rounded-lg p-2 text-surface-500 transition-colors hover:bg-surface-100 hover:text-surface-700 dark:text-surface-400 dark:hover:bg-surface-800"
				>
					<a href="/buckets"><ArrowLeft class="h-5 w-5" /></a>
				</Tooltip.Trigger>
				<Tooltip.Portal>
					<Tooltip.Content
						sideOffset={8}
						class="z-50 rounded-lg border border-surface-200 bg-white px-3 py-1.5 text-sm shadow-lg dark:border-surface-700 dark:bg-surface-800"
					>
						Back to buckets
					</Tooltip.Content>
				</Tooltip.Portal>
			</Tooltip.Root>
			<div>
				<h2 class="text-2xl font-bold text-surface-900 dark:text-surface-100">{data.bucket}</h2>
				{#if data.prefix}
					<p class="mt-1 text-sm text-surface-500 dark:text-surface-400">
						<code class="rounded bg-surface-100 px-1.5 py-0.5 font-mono text-xs dark:bg-surface-800">{data.prefix}</code>
					</p>
				{/if}
			</div>
			<Badge>{data.keyCount} objects</Badge>
		</div>
		<Button onclick={() => (uploadOpen = true)}>
			<Upload class="h-4 w-4" />
			Upload Files
		</Button>
	</div>

	{#if form?.error}
		<div class="rounded-lg border border-red-200 bg-red-50 p-3 text-sm text-red-700 dark:border-red-800 dark:bg-red-900/20 dark:text-red-400">
			{form.error}
		</div>
	{/if}

	<!-- Upload Modal -->
	<Dialog.Root bind:open={uploadOpen} onOpenChange={(open) => { if (!open) closeUpload(); }}>
		<Dialog.Portal>
			<Dialog.Overlay class="fixed inset-0 z-50 bg-black/50" />
			<Dialog.Content class="fixed left-1/2 top-1/2 z-50 w-full max-w-lg -translate-x-1/2 -translate-y-1/2 rounded-xl border border-surface-200 bg-white p-6 shadow-xl dark:border-surface-800 dark:bg-surface-900">
				<div class="mb-4 flex items-center justify-between">
					<Dialog.Title class="text-lg font-semibold text-surface-900 dark:text-surface-100">
						Upload Files to {data.bucket}
					</Dialog.Title>
					<button onclick={closeUpload} class="rounded-lg p-1 text-surface-400 hover:text-surface-600 dark:hover:text-surface-300">
						<X class="h-5 w-5" />
					</button>
				</div>

				{#if data.prefix}
					<p class="mb-4 text-sm text-surface-500 dark:text-surface-400">
						Prefix: <code class="rounded bg-surface-100 px-1.5 py-0.5 font-mono text-xs dark:bg-surface-800">{data.prefix}</code>
					</p>
				{/if}

				<!-- Drop zone -->
				<!-- svelte-ignore a11y_no_static_element_interactions -->
				<div
					class="mb-4 rounded-lg border-2 border-dashed p-8 text-center transition-colors {dragover ? 'border-primary-500 bg-primary-50 dark:bg-primary-900/10' : 'border-surface-300 dark:border-surface-700'}"
					ondragover={(e) => { e.preventDefault(); dragover = true; }}
					ondragleave={() => (dragover = false)}
					ondrop={handleDrop}
				>
					<Upload class="mx-auto mb-2 h-8 w-8 text-surface-400" />
					<p class="text-sm text-surface-600 dark:text-surface-400">
						Drag & drop files here, or
						<label class="cursor-pointer font-medium text-primary-600 hover:underline dark:text-primary-400">
							browse
							<input
								type="file"
								multiple
								class="hidden"
								onchange={(e) => addFiles(e.currentTarget.files)}
							/>
						</label>
					</p>
				</div>

				<!-- Overall progress bar -->
				{#if uploading}
					<div class="mb-4">
						<div class="mb-1 flex items-center justify-between text-xs text-surface-500">
							<span>Uploading...</span>
							<span>{totalProgress}%</span>
						</div>
						<Progress.Root
							value={totalProgress}
							max={100}
							class="relative h-2 w-full overflow-hidden rounded-full bg-surface-200 dark:bg-surface-700"
						>
							<div
								class="h-full rounded-full bg-primary-600 transition-all duration-200 dark:bg-primary-500"
								style="width: {totalProgress}%"
							></div>
						</Progress.Root>
					</div>
				{/if}

				<!-- Selected files with previews -->
				{#if selectedFiles.length > 0}
					<div class="mb-4 max-h-64 space-y-2 overflow-y-auto">
						{#each selectedFiles as item, i}
							<div class="flex items-center gap-3 rounded-lg border border-surface-200 p-2 dark:border-surface-800">
								<!-- Preview -->
								{#if item.preview}
									<img src={item.preview} alt={item.file.name} class="h-12 w-12 rounded object-cover" />
								{:else}
									{@const Icon = getFileIcon(item.file.name)}
									<div class="flex h-12 w-12 items-center justify-center rounded bg-surface-100 dark:bg-surface-800">
										<Icon class="h-6 w-6 text-surface-400" />
									</div>
								{/if}

								<!-- File info + progress -->
								<div class="min-w-0 flex-1">
									<p class="truncate text-sm font-medium text-surface-900 dark:text-surface-100">
										{item.file.name}
									</p>
									<p class="text-xs text-surface-500">{formatBytes(item.file.size)}</p>
									{#if item.status === 'uploading'}
										<Progress.Root
											value={item.progress}
											max={100}
											class="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-surface-200 dark:bg-surface-700"
										>
											<div
												class="h-full rounded-full bg-primary-500 transition-all duration-150"
												style="width: {item.progress}%"
											></div>
										</Progress.Root>
									{/if}
								</div>

								<!-- Status -->
								{#if item.status === 'uploading'}
									<span class="text-xs font-medium text-primary-500">{item.progress}%</span>
								{:else if item.status === 'done'}
									<CheckCircle class="h-5 w-5 text-emerald-500" />
								{:else if item.status === 'error'}
									<Tooltip.Root>
										<Tooltip.Trigger class="cursor-default">
											<AlertCircle class="h-5 w-5 text-red-500" />
										</Tooltip.Trigger>
										<Tooltip.Portal>
											<Tooltip.Content
												sideOffset={8}
												class="z-[60] max-w-xs rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm text-red-700 shadow-lg dark:border-red-800 dark:bg-red-900/20 dark:text-red-300"
											>
												{item.error}
											</Tooltip.Content>
										</Tooltip.Portal>
									</Tooltip.Root>
								{:else}
									<button
										onclick={() => removeFile(i)}
										class="rounded p-1 text-surface-400 hover:text-red-500"
										title="Remove"
									>
										<X class="h-4 w-4" />
									</button>
								{/if}
							</div>
						{/each}
					</div>
				{/if}

				<!-- Actions -->
				<div class="flex justify-end gap-2">
					<Button variant="ghost" onclick={closeUpload} disabled={uploading}>
						{allDone ? 'Close' : 'Cancel'}
					</Button>
					{#if !allDone}
						<Button
							onclick={uploadAll}
							disabled={uploading || selectedFiles.length === 0 || selectedFiles.every((f) => f.status !== 'pending')}
						>
							{#if uploading}
								Uploading...
							{:else}
								Upload {selectedFiles.filter((f) => f.status === 'pending').length} file{selectedFiles.filter((f) => f.status === 'pending').length !== 1 ? 's' : ''}
							{/if}
						</Button>
					{/if}
				</div>
			</Dialog.Content>
		</Dialog.Portal>
	</Dialog.Root>

	{#if data.prefix}
		<button
			onclick={() => navigatePrefix(parentPrefix)}
			class="flex items-center gap-2 text-sm text-primary-600 hover:underline dark:text-primary-400"
		>
			<Folder class="h-4 w-4" />
			.. (parent directory)
		</button>
	{/if}

	<div class="overflow-x-auto rounded-lg border border-surface-200 dark:border-surface-800">
		<table class="w-full text-left text-sm">
			<thead class="border-b border-surface-200 bg-surface-50 text-xs uppercase tracking-wide text-surface-500 dark:border-surface-800 dark:bg-surface-900 dark:text-surface-400">
				<tr>
					<th class="px-4 py-3 font-medium">Name</th>
					<th class="w-32 px-4 py-3 font-medium">Size</th>
					<th class="w-48 px-4 py-3 font-medium">Last Modified</th>
					<th class="w-24 px-4 py-3 font-medium">Actions</th>
				</tr>
			</thead>
			<tbody class="divide-y divide-surface-100 dark:divide-surface-800">
				{#if data.objects.length === 0}
					<tr>
						<td colspan="4" class="px-4 py-8 text-center text-surface-500">
							No objects in this bucket
						</td>
					</tr>
				{:else}
					{#each data.objects as obj}
						{@const folder = isObjFolder(obj)}
						<tr
							class="cursor-pointer bg-white transition-colors hover:bg-surface-50 dark:bg-surface-900 dark:hover:bg-surface-800"
							onclick={folder ? () => navigatePrefix(obj.key) : () => openViewer(obj)}
							onkeydown={(e: KeyboardEvent) => { if (e.key === 'Enter') { folder ? navigatePrefix(obj.key) : openViewer(obj); } }}
							role="button"
							tabindex={0}
						>
							<td class="px-4 py-3">
								<span class="flex items-center gap-2">
									{#if folder}
										<Folder class="h-4 w-4 text-amber-500" />
									{:else}
										{@const Icon = getFileIcon(obj.key)}
										<Icon class="h-4 w-4 text-surface-400" />
									{/if}
									<span class="font-medium text-surface-900 dark:text-surface-100">
										{getDisplayName(obj.key)}
									</span>
								</span>
							</td>
							<td class="px-4 py-3 text-surface-500 dark:text-surface-400">
								{folder ? '-' : formatBytes(obj.size)}
							</td>
							<td class="px-4 py-3 text-surface-500 dark:text-surface-400">
								{obj.last_modified ? formatDate(obj.last_modified) : '-'}
							</td>
							<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
							<td class="px-4 py-3" onclick={(e: MouseEvent) => e.stopPropagation()}>
								{#if !folder}
									<span class="flex items-center gap-1">
										<Tooltip.Root>
											<Tooltip.Trigger
												class="rounded-lg p-1.5 text-surface-400 transition-colors hover:bg-primary-50 hover:text-primary-600 dark:hover:bg-primary-900/20 dark:hover:text-primary-400"
											>
												<a href={downloadUrl(obj.key)} download>
													<Download class="h-4 w-4" />
												</a>
											</Tooltip.Trigger>
											<Tooltip.Portal>
												<Tooltip.Content
													sideOffset={8}
													class="z-50 rounded-lg border border-surface-200 bg-white px-3 py-1.5 text-sm shadow-lg dark:border-surface-700 dark:bg-surface-800"
												>
													Download
												</Tooltip.Content>
											</Tooltip.Portal>
										</Tooltip.Root>
										<Tooltip.Root>
											<Tooltip.Trigger class="cursor-default">
												<form method="POST" action="?/delete" use:enhance={() => {
													return async ({ result }) => {
														if (result.type === 'success') {
															toast.success(`Deleted ${getDisplayName(obj.key)}`);
															await invalidateAll();
														} else {
															toast.error('Failed to delete object');
														}
													};
												}}>
													<input type="hidden" name="key" value={obj.key} />
													<button
														type="submit"
														class="rounded-lg p-1.5 text-surface-400 transition-colors hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-900/20 dark:hover:text-red-400"
													>
														<Trash2 class="h-4 w-4" />
													</button>
												</form>
											</Tooltip.Trigger>
											<Tooltip.Portal>
												<Tooltip.Content
													sideOffset={8}
													class="z-50 rounded-lg border border-surface-200 bg-white px-3 py-1.5 text-sm shadow-lg dark:border-surface-700 dark:bg-surface-800"
												>
													Delete
												</Tooltip.Content>
											</Tooltip.Portal>
										</Tooltip.Root>
									</span>
								{/if}
							</td>
						</tr>
					{/each}
				{/if}
			</tbody>
		</table>
	</div>

	<!-- File Viewer -->
	{#if viewerOpen}
		<FileViewer
			bind:open={viewerOpen}
			url={viewerUrl}
			filename={viewerFilename}
			size={viewerSize}
			onclose={() => (viewerOpen = false)}
		/>
	{/if}
</div>
