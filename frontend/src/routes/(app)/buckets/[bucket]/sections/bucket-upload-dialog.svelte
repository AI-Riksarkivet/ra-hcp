<script lang="ts">
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Progress } from '$lib/components/ui/progress/index.js';
	import {
		Upload,
		X,
		CheckCircle,
		AlertCircle,
		FileText,
		Image,
		FileArchive,
		FileCode,
	} from 'lucide-svelte';
	import { formatBytes } from '$lib/utils/format.js';
	import { cn } from '$lib/utils.js';
	import { toast } from 'svelte-sonner';
	import {
		create_multipart_upload,
		complete_multipart_upload,
		abort_multipart_upload,
	} from '$lib/remote/buckets.remote.js';

	const MULTIPART_THRESHOLD = 100 * 1024 * 1024; // 100 MB
	const PART_SIZE = 25 * 1024 * 1024; // 25 MB
	const CONCURRENT_PARTS = 6; // parallel part uploads

	let {
		open = $bindable(false),
		bucket,
		prefix,
		onuploaded,
	}: {
		open: boolean;
		bucket: string;
		prefix: string;
		onuploaded: () => void;
	} = $props();

	interface FileUpload {
		file: File;
		key: string;
		preview: string | null;
		status: 'pending' | 'uploading' | 'done' | 'error';
		progress: number;
		error?: string;
	}

	let selectedFiles = $state<FileUpload[]>([]);
	let uploading = $state(false);
	let dragover = $state(false);

	function getFileIcon(name: string) {
		const ext = name.split('.').pop()?.toLowerCase() ?? '';
		if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return Image;
		if (['zip', 'tar', 'gz', 'rar', '7z'].includes(ext)) return FileArchive;
		if (['js', 'ts', 'py', 'json', 'html', 'css', 'xml', 'yaml', 'yml', 'toml'].includes(ext))
			return FileCode;
		return FileText;
	}

	function isImageFile(file: File): boolean {
		return file.type.startsWith('image/');
	}

	function addFiles(files: FileList | null) {
		if (!files) return;
		for (const file of files) {
			const preview = isImageFile(file) ? URL.createObjectURL(file) : null;
			const key = (prefix || '') + file.name;
			selectedFiles = [...selectedFiles, { file, key, preview, status: 'pending', progress: 0 }];
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

	function simpleUpload(index: number): Promise<void> {
		return new Promise((resolve) => {
			const item = selectedFiles[index];
			const formData = new FormData();
			formData.append('file', item.file);
			const xhr = new XMLHttpRequest();
			xhr.open(
				'POST',
				`/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${encodeURIComponent(item.key)}`
			);
			xhr.upload.onprogress = (e) => {
				if (e.lengthComputable) {
					selectedFiles[index] = {
						...selectedFiles[index],
						progress: Math.round((e.loaded / e.total) * 100),
					};
				}
			};
			xhr.onload = () => {
				if (xhr.status >= 200 && xhr.status < 300) {
					selectedFiles[index] = { ...selectedFiles[index], status: 'done', progress: 100 };
				} else {
					const err = (() => {
						try {
							return JSON.parse(xhr.responseText);
						} catch {
							return { detail: 'Upload failed' };
						}
					})();
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

	function uploadPartXhr(
		bucket: string,
		key: string,
		uploadId: string,
		partNumber: number,
		blob: Blob
	): Promise<string> {
		return new Promise((resolve, reject) => {
			const formData = new FormData();
			formData.append('file', blob);
			const xhr = new XMLHttpRequest();
			xhr.open(
				'PUT',
				`/api/v1/buckets/${encodeURIComponent(bucket)}/multipart/${encodeURIComponent(key)}?upload_id=${encodeURIComponent(uploadId)}&part_number=${partNumber}`
			);
			xhr.onload = () => {
				if (xhr.status >= 200 && xhr.status < 300) {
					try {
						const data = JSON.parse(xhr.responseText);
						resolve(data.etag as string);
					} catch {
						reject(new Error('Invalid response from part upload'));
					}
				} else {
					reject(new Error(`Part ${partNumber} upload failed (HTTP ${xhr.status})`));
				}
			};
			xhr.onerror = () => reject(new Error(`Part ${partNumber} network error`));
			xhr.send(formData);
		});
	}

	async function multipartUpload(index: number): Promise<void> {
		const item = selectedFiles[index];
		selectedFiles[index] = { ...selectedFiles[index], status: 'uploading', progress: 0 };

		let uploadId: string | null = null;
		try {
			const init = await create_multipart_upload({ bucket, key: item.key });
			uploadId = init.upload_id;

			const totalParts = Math.ceil(item.file.size / PART_SIZE);
			const parts: { PartNumber: number; ETag: string }[] = new Array(totalParts);
			let completedParts = 0;

			// Upload parts with bounded concurrency
			const queue = Array.from({ length: totalParts }, (_, i) => i);
			const workers = Array.from({ length: Math.min(CONCURRENT_PARTS, totalParts) }, async () => {
				while (queue.length > 0) {
					const i = queue.shift()!;
					const start = i * PART_SIZE;
					const end = Math.min(start + PART_SIZE, item.file.size);
					const blob = item.file.slice(start, end);
					const partNumber = i + 1;

					const etag = await uploadPartXhr(bucket, item.key, uploadId!, partNumber, blob);
					parts[i] = { PartNumber: partNumber, ETag: etag };
					completedParts++;

					selectedFiles[index] = {
						...selectedFiles[index],
						progress: Math.round((completedParts / totalParts) * 100),
					};
				}
			});
			await Promise.all(workers);

			await complete_multipart_upload({
				bucket,
				key: item.key,
				upload_id: uploadId,
				parts,
			});
			selectedFiles[index] = { ...selectedFiles[index], status: 'done', progress: 100 };
		} catch (err) {
			if (uploadId) {
				try {
					await abort_multipart_upload({ bucket, key: item.key, upload_id: uploadId });
				} catch {
					// best-effort abort
				}
			}
			selectedFiles[index] = {
				...selectedFiles[index],
				status: 'error',
				error: err instanceof Error ? err.message : 'Multipart upload failed',
			};
		}
	}

	function uploadFile(index: number): Promise<void> {
		const item = selectedFiles[index];
		if (item.file.size >= MULTIPART_THRESHOLD) {
			return multipartUpload(index);
		}
		return simpleUpload(index);
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
		if (doneCount > 0)
			toast.success(`Uploaded ${doneCount} file${doneCount !== 1 ? 's' : ''} successfully`);
		if (errCount > 0) toast.error(`${errCount} file${errCount !== 1 ? 's' : ''} failed to upload`);
		onuploaded();
	}

	function closeUpload() {
		for (const f of selectedFiles) {
			if (f.preview) URL.revokeObjectURL(f.preview);
		}
		selectedFiles = [];
		open = false;
	}

	let allDone = $derived(
		selectedFiles.length > 0 && selectedFiles.every((f) => f.status === 'done')
	);
	let totalProgress = $derived.by(() => {
		if (selectedFiles.length === 0) return 0;
		return Math.round(selectedFiles.reduce((sum, f) => sum + f.progress, 0) / selectedFiles.length);
	});
</script>

<Dialog.Root
	bind:open
	onOpenChange={(o) => {
		if (!o) closeUpload();
	}}
>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header><Dialog.Title>Upload Files to {bucket}</Dialog.Title></Dialog.Header>
		{#if prefix}<p class="text-sm text-muted-foreground">
				Prefix: <code class="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{prefix}</code>
			</p>{/if}

		<div
			role="region"
			aria-label="File drop zone"
			class={cn(
				'rounded-lg border-2 border-dashed p-8 text-center transition-colors',
				dragover ? 'border-primary bg-primary/5' : 'border-border'
			)}
			ondragover={(e) => {
				e.preventDefault();
				dragover = true;
			}}
			ondragleave={() => (dragover = false)}
			ondrop={handleDrop}
		>
			<Upload class="mx-auto mb-2 h-8 w-8 text-muted-foreground" />
			<p class="text-sm text-muted-foreground">
				Drag & drop files here, or <label
					class="cursor-pointer font-medium text-primary hover:underline"
					>browse<input
						type="file"
						multiple
						class="hidden"
						onchange={(e) => addFiles(e.currentTarget.files)}
					/></label
				>
			</p>
		</div>

		{#if uploading}
			<div>
				<div class="mb-1 flex items-center justify-between text-xs text-muted-foreground">
					<span>Uploading...</span><span>{totalProgress}%</span>
				</div>
				<Progress value={totalProgress} max={100} class="h-2" />
			</div>
		{/if}

		{#if selectedFiles.length > 0}
			<div class="max-h-64 space-y-2 overflow-y-auto">
				{#each selectedFiles as item, i (item.key)}
					<div class="flex items-center gap-3 rounded-lg border p-2">
						{#if item.preview}<img
								src={item.preview}
								alt={item.file.name}
								class="h-12 w-12 rounded object-cover"
							/>
						{:else}{@const Icon = getFileIcon(item.file.name)}
							<div class="flex h-12 w-12 items-center justify-center rounded bg-muted">
								<Icon class="h-6 w-6 text-muted-foreground" />
							</div>{/if}
						<div class="min-w-0 flex-1">
							<p class="truncate text-sm font-medium">{item.file.name}</p>
							{#if item.status === 'pending'}<Input
									value={item.key}
									oninput={(e) => {
										selectedFiles[i] = { ...selectedFiles[i], key: e.currentTarget.value };
									}}
									class="mt-1 h-auto px-2 py-0.5 font-mono text-xs text-muted-foreground"
									placeholder="Object key"
								/>
							{:else}<p class="mt-0.5 truncate font-mono text-xs text-muted-foreground">
									{item.key}
								</p>{/if}
							<p class="text-xs text-muted-foreground">{formatBytes(item.file.size)}</p>
							{#if item.status === 'uploading'}<Progress
									value={item.progress}
									max={100}
									class="mt-1 h-1.5"
								/>{/if}
						</div>
						{#if item.status === 'uploading'}<span class="text-xs font-medium text-primary"
								>{item.progress}%</span
							>
						{:else if item.status === 'done'}<CheckCircle class="h-5 w-5 text-emerald-500" />
						{:else if item.status === 'error'}
							<Tooltip.Root>
								<Tooltip.Trigger
									>{#snippet child({ props })}<span {...props}
											><AlertCircle class="h-5 w-5 text-destructive" /></span
										>{/snippet}</Tooltip.Trigger
								>
								<Tooltip.Content
									class="max-w-xs border-destructive/20 bg-destructive/10 text-destructive"
									>{item.error}</Tooltip.Content
								>
							</Tooltip.Root>
						{:else}<Button
								variant="ghost"
								size="icon"
								class="h-7 w-7 text-muted-foreground hover:text-destructive"
								onclick={() => removeFile(i)}
								title="Remove"><X class="h-4 w-4" /></Button
							>{/if}
					</div>
				{/each}
			</div>
		{/if}

		<Dialog.Footer>
			<Button variant="ghost" onclick={closeUpload} disabled={uploading}
				>{allDone ? 'Close' : 'Cancel'}</Button
			>
			{#if !allDone}<Button
					onclick={uploadAll}
					disabled={uploading ||
						selectedFiles.length === 0 ||
						selectedFiles.every((f) => f.status !== 'pending')}
				>
					{#if uploading}Uploading...{:else}Upload {selectedFiles.filter(
							(f) => f.status === 'pending'
						).length} file{selectedFiles.filter((f) => f.status === 'pending').length !== 1
							? 's'
							: ''}{/if}
				</Button>{/if}
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
