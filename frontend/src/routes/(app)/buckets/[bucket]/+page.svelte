<script lang="ts">
	import { page } from '$app/state';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Progress } from '$lib/components/ui/progress/index.js';
	import {
		Upload,
		Trash2,
		Download,
		Folder,
		FileText,
		Image,
		FileArchive,
		FileCode,
		X,
		CheckCircle,
		AlertCircle,
		Loader2,
		Search,
		Link,
		Copy,
		Check,
	} from 'lucide-svelte';
	import FileViewer from '$lib/components/ui/FileViewer.svelte';
	import {
		formatBytes,
		formatDate,
		parseQuotaBytes,
		getStorageUsed,
		calcQuotaPercent,
		matchesDateFilter,
	} from '$lib/utils/format.js';
	import type { ChargebackEntry } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import { useSelection } from '$lib/utils/use-selection.svelte.js';
	import { useDelete } from '$lib/utils/use-delete.svelte.js';
	import BackButton from '$lib/components/ui/back-button.svelte';
	import StorageProgressBar from '$lib/components/ui/storage-progress-bar.svelte';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import BulkDeleteDialog from '$lib/components/ui/bulk-delete-dialog.svelte';
	import {
		get_objects,
		delete_object,
		bulk_delete_objects,
		bulk_presign,
		generate_presigned_url,
	} from '$lib/buckets.remote.js';
	import { get_tenant_chargeback } from '$lib/tenant-info.remote.js';
	import { get_namespaces, type Namespace } from '$lib/namespaces.remote.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Input } from '$lib/components/ui/input/index.js';

	let tenant = $derived(page.data.tenant as string | undefined);
	let chargebackData = $derived(tenant ? get_tenant_chargeback({ tenant }) : undefined);
	let nsData = $derived(tenant ? get_namespaces({ tenant }) : undefined);

	let bucket = $derived(page.params.bucket ?? '');

	// Bucket-specific storage from chargeback (bucket name = namespace name in HCP)
	let bucketStorageUsed = $derived(
		getStorageUsed((chargebackData?.current?.chargebackData ?? []) as ChargebackEntry[], bucket)
	);

	// Bucket-specific quota from namespace info
	let bucketQuotaStr = $derived.by(() => {
		const nsList = (nsData?.current ?? []) as Namespace[];
		const ns = nsList.find((n) => n.name === bucket);
		return ns?.hardQuota ?? null;
	});

	let bucketQuotaBytes = $derived(bucketQuotaStr ? parseQuotaBytes(bucketQuotaStr) : null);
	let bucketQuotaPercent = $derived(calcQuotaPercent(bucketStorageUsed, bucketQuotaStr));
	let prefix = $derived(page.url.searchParams.get('prefix') ?? '');
	let objectData = $derived(get_objects({ bucket, prefix }));

	interface FileUpload {
		file: File;
		key: string;
		preview: string | null;
		status: 'pending' | 'uploading' | 'done' | 'error';
		progress: number;
		error?: string;
	}

	let uploadOpen = $state(false);
	let selectedFiles = $state<FileUpload[]>([]);
	let uploading = $state(false);
	let dragover = $state(false);

	interface S3Object {
		key: string;
		size: number;
		last_modified: string;
		etag: string;
		storage_class: string;
		owner: { display_name?: string; id?: string; DisplayName?: string; ID?: string } | null;
	}

	function getOwnerName(obj: S3Object): string {
		return obj.owner?.display_name ?? obj.owner?.DisplayName ?? '';
	}

	let rawObjects = $derived((objectData.current?.objects ?? []) as S3Object[]);
	let commonPrefixes = $derived((objectData.current?.commonPrefixes ?? []) as string[]);
	let folderEntries = $derived(
		commonPrefixes.map(
			(p): S3Object => ({
				key: p,
				size: 0,
				last_modified: '',
				etag: '',
				storage_class: '',
				owner: null,
			})
		)
	);
	let objects = $derived([...folderEntries, ...rawObjects]);
	let keyCount = $derived(objectData.current?.keyCount ?? 0);

	function navigatePrefix(p: string) {
		goto(`/buckets/${bucket}?prefix=${encodeURIComponent(p)}`);
	}
	function downloadUrl(key: string): string {
		return `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${encodeURIComponent(key)}`;
	}
	function getDisplayName(key: string): string {
		return key.split('/').filter(Boolean).pop() ?? key;
	}
	function isObjFolder(obj: S3Object): boolean {
		return obj.size === 0 && obj.key.endsWith('/');
	}

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

	function uploadFile(index: number): Promise<void> {
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
		await objectData.refresh();
	}

	function closeUpload() {
		for (const f of selectedFiles) {
			if (f.preview) URL.revokeObjectURL(f.preview);
		}
		selectedFiles = [];
		uploadOpen = false;
	}

	let allDone = $derived(
		selectedFiles.length > 0 && selectedFiles.every((f) => f.status === 'done')
	);
	let totalProgress = $derived.by(() => {
		if (selectedFiles.length === 0) return 0;
		return Math.round(selectedFiles.reduce((sum, f) => sum + f.progress, 0) / selectedFiles.length);
	});
	let parentPrefix = $derived.by(() => {
		if (!prefix) return '';
		const parts = prefix.replace(/\/$/, '').split('/');
		parts.pop();
		return parts.length > 0 ? parts.join('/') + '/' : '';
	});

	let search = $state('');
	let ownerFilter = $state('');
	let sizeFilter = $state('');
	let dateFilter = $state('');

	let uniqueOwners = $derived([...new Set(rawObjects.map(getOwnerName).filter(Boolean))]);

	let filteredObjects = $derived(
		objects.filter((obj) => {
			if (search) {
				const q = search.toLowerCase();
				if (
					!getDisplayName(obj.key).toLowerCase().includes(q) &&
					!obj.key.toLowerCase().includes(q)
				)
					return false;
			}
			if (ownerFilter && getOwnerName(obj) !== ownerFilter && !isObjFolder(obj)) return false;
			if (sizeFilter && !isObjFolder(obj)) {
				const s = obj.size;
				if (sizeFilter === '<1KB' && s >= 1024) return false;
				if (sizeFilter === '1KB-1MB' && (s < 1024 || s >= 1048576)) return false;
				if (sizeFilter === '1MB-100MB' && (s < 1048576 || s >= 104857600)) return false;
				if (sizeFilter === '>100MB' && s < 104857600) return false;
			}
			if (dateFilter && obj.last_modified) {
				if (!matchesDateFilter(obj.last_modified, dateFilter)) return false;
			}
			return true;
		})
	);

	let hasActiveFilters = $derived(!!ownerFilter || !!sizeFilter || !!dateFilter);
	function clearFilters() {
		ownerFilter = '';
		sizeFilter = '';
		dateFilter = '';
	}

	let selectableObjects = $derived(filteredObjects.filter((obj) => !isObjFolder(obj)));

	const { selected, allSelected, toggleAll, toggleOne } = useSelection(
		() => selectableObjects,
		(o) => o.key
	);

	// --- File Viewer ---
	let viewerOpen = $state(false);
	let viewerIndex = $state(-1);

	let viewerObject = $derived(viewerIndex >= 0 ? selectableObjects[viewerIndex] : undefined);
	let viewerUrl = $derived(viewerObject ? downloadUrl(viewerObject.key) : '');
	let viewerFilename = $derived(viewerObject ? getDisplayName(viewerObject.key) : '');
	let viewerSize = $derived(viewerObject?.size ?? 0);
	let viewerHasPrev = $derived(viewerIndex > 0);
	let viewerHasNext = $derived(viewerIndex < selectableObjects.length - 1);

	function openViewer(obj: { key: string; size: number }) {
		viewerIndex = selectableObjects.findIndex((o) => o.key === obj.key);
		viewerOpen = true;
	}

	function viewerPrev() {
		if (viewerHasPrev) viewerIndex--;
	}
	function viewerNext() {
		if (viewerHasNext) viewerIndex++;
	}

	// --- Presigned URL ---
	const EXPIRY_PRESETS = [
		{ label: '5 minutes', value: 300 },
		{ label: '1 hour', value: 3600 },
		{ label: '6 hours', value: 21600 },
		{ label: '24 hours', value: 86400 },
		{ label: '7 days', value: 604800 },
	];

	let shareTarget = $state<string | null>(null);
	let shareMethod = $state<'get_object' | 'put_object'>('get_object');
	let shareExpiry = $state(3600);
	let shareGenerating = $state(false);
	let shareUrl = $state('');
	let shareCopied = $state(false);

	function openShare(key: string) {
		shareTarget = key;
		shareMethod = 'get_object';
		shareExpiry = 3600;
		shareUrl = '';
		shareCopied = false;
	}

	function closeShare() {
		shareTarget = null;
		shareUrl = '';
	}

	async function handleGenerateUrl() {
		if (!shareTarget) return;
		shareGenerating = true;
		shareUrl = '';
		try {
			const result = await generate_presigned_url({
				bucket,
				key: shareTarget,
				expires_in: shareExpiry,
				method: shareMethod,
			});
			shareUrl = result.url;
		} catch {
			toast.error('Failed to generate presigned URL');
		} finally {
			shareGenerating = false;
		}
	}

	function copyShareUrl() {
		navigator.clipboard.writeText(shareUrl);
		shareCopied = true;
		setTimeout(() => (shareCopied = false), 2000);
	}

	let downloading = $state(false);

	async function bulkDownload() {
		const keys = [...selected].filter((k) => !k.endsWith('/'));
		if (keys.length === 0) return;
		downloading = true;
		try {
			const result = await bulk_presign({ bucket, keys, expires_in: 3600 });
			for (const item of result.urls) {
				const a = document.createElement('a');
				a.href = item.url;
				a.download = item.key.split('/').pop() ?? item.key;
				a.style.display = 'none';
				document.body.appendChild(a);
				a.click();
				document.body.removeChild(a);
				// Small delay to avoid browser blocking multiple downloads
				await new Promise((r) => setTimeout(r, 150));
			}
			toast.success(
				`Started downloading ${result.urls.length} file${result.urls.length !== 1 ? 's' : ''}`
			);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to download objects');
		} finally {
			downloading = false;
		}
	}

	const del = useDelete({ entityName: 'object' });

	function handleConfirmDelete() {
		del.confirmDelete(() => delete_object({ bucket, key: del.deleteTarget }).updates(objectData));
	}

	async function handleConfirmBulkDelete() {
		const keys = [...selected];
		del.confirmBulkDelete(
			keys,
			async (_key, isLast) => {
				if (!isLast) return; // batch call on last item only
				await bulk_delete_objects({ bucket, keys }).updates(objectData);
			},
			() => selected.clear()
		);
	}
</script>

<svelte:head><title>{bucket} - HCP Admin Console</title></svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-4">
			<BackButton href="/buckets" label="Back to buckets" />
			<div>
				<h2 class="text-2xl font-bold">{bucket}</h2>
				{#if prefix}<p class="mt-1 text-sm text-muted-foreground">
						<code class="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{prefix}</code>
					</p>{/if}
			</div>
			{#await objectData then od}
				<Badge variant="secondary">{od.keyCount} objects</Badge>
			{/await}
			{#if tenant && (bucketStorageUsed > 0 || bucketQuotaBytes)}
				<Tooltip.Root>
					<Tooltip.Trigger>
						{#snippet child({ props })}
							<span class="flex items-center gap-1.5 text-xs text-muted-foreground" {...props}>
								<span
									>{formatBytes(bucketStorageUsed)}{bucketQuotaStr
										? ` / ${bucketQuotaStr}`
										: ''}</span
								>
								{#if bucketQuotaPercent !== null}
									<StorageProgressBar percent={bucketQuotaPercent} class="w-16" />
								{/if}
							</span>
						{/snippet}
					</Tooltip.Trigger>
					<Tooltip.Content>Bucket storage usage</Tooltip.Content>
				</Tooltip.Root>
			{/if}
		</div>
		<Button onclick={() => (uploadOpen = true)}><Upload class="h-4 w-4" />Upload Files</Button>
	</div>

	<!-- Upload Modal -->
	<Dialog.Root
		bind:open={uploadOpen}
		onOpenChange={(open) => {
			if (!open) closeUpload();
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
				class="rounded-lg border-2 border-dashed p-8 text-center transition-colors {dragover
					? 'border-primary bg-primary/5'
					: 'border-border'}"
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
								{#if item.status === 'pending'}<input
										type="text"
										value={item.key}
										oninput={(e) => {
											selectedFiles[i] = { ...selectedFiles[i], key: e.currentTarget.value };
										}}
										class="mt-1 w-full rounded border bg-background px-2 py-0.5 font-mono text-xs text-muted-foreground"
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
							{:else}<button
									onclick={() => removeFile(i)}
									class="rounded p-1 text-muted-foreground hover:text-destructive"
									title="Remove"><X class="h-4 w-4" /></button
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

	{#if prefix}<button
			onclick={() => navigatePrefix(parentPrefix)}
			class="flex items-center gap-2 text-sm text-primary hover:underline"
			><Folder class="h-4 w-4" />.. (parent directory)</button
		>{/if}

	{#await objectData}
		<TableSkeleton rows={5} columns={7} />
	{:then _}
		<div class="space-y-2">
			<div class="relative">
				<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
				<input
					type="text"
					bind:value={search}
					placeholder="Search objects..."
					class="w-full rounded-lg border bg-background py-2 pl-10 pr-3 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20"
				/>
			</div>
			<div class="flex flex-wrap items-center gap-2">
				{#if uniqueOwners.length > 0}
					<select bind:value={ownerFilter} class="h-8 rounded-md border bg-background px-2 text-xs">
						<option value="">All owners</option>
						{#each uniqueOwners as o (o)}<option value={o}>{o}</option>{/each}
					</select>
				{/if}
				<select bind:value={sizeFilter} class="h-8 rounded-md border bg-background px-2 text-xs">
					<option value="">All sizes</option>
					<option value="<1KB">&lt; 1 KB</option>
					<option value="1KB-1MB">1 KB - 1 MB</option>
					<option value="1MB-100MB">1 MB - 100 MB</option>
					<option value=">100MB">&gt; 100 MB</option>
				</select>
				<select bind:value={dateFilter} class="h-8 rounded-md border bg-background px-2 text-xs">
					<option value="">All dates</option>
					<option value="24h">Last 24 hours</option>
					<option value="7d">Last 7 days</option>
					<option value="30d">Last 30 days</option>
				</select>
				{#if hasActiveFilters}
					<Button variant="ghost" size="sm" class="h-7 px-2 text-xs" onclick={clearFilters}>
						Clear filters
					</Button>
				{/if}
				<span class="ml-auto text-xs text-muted-foreground"
					>{filteredObjects.length} of {objects.length} items</span
				>
			</div>
		</div>

		{#if selected.size > 0}
			<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
				<span class="text-sm font-medium">{selected.size} selected</span>
				<Button size="sm" onclick={bulkDownload} disabled={downloading}
					>{#if downloading}<Loader2 class="h-3.5 w-3.5 animate-spin" />{:else}<Download
							class="h-3.5 w-3.5"
						/>{/if}Download Selected</Button
				>
				<Button variant="destructive" size="sm" onclick={() => del.requestBulkDelete()}
					><Trash2 class="h-3.5 w-3.5" />Delete Selected</Button
				>
				<Button variant="ghost" size="sm" onclick={() => selected.clear()}>Deselect All</Button>
			</div>
		{/if}

		<div class="overflow-x-auto rounded-lg border">
			<table class="w-full text-left text-sm">
				<thead class="border-b bg-muted/50 text-xs uppercase tracking-wide text-muted-foreground">
					<tr>
						<th class="w-10 px-4 py-3"
							><input
								type="checkbox"
								checked={allSelected}
								onchange={toggleAll}
								class="h-4 w-4 rounded border-input"
								disabled={selectableObjects.length === 0}
							/></th
						>
						<th class="px-4 py-3 font-medium">Name</th>
						<th class="px-4 py-3 font-medium">Key</th>
						<th class="w-32 px-4 py-3 font-medium">Owner</th>
						<th class="w-32 px-4 py-3 font-medium">Size</th>
						<th class="w-48 px-4 py-3 font-medium">Last Modified</th>
						<th class="w-24 px-4 py-3 font-medium">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y">
					{#if objects.length === 0}<tr
							><td colspan="7" class="px-4 py-8 text-center text-muted-foreground"
								>No objects in this bucket</td
							></tr
						>
					{:else if filteredObjects.length === 0}<tr
							><td colspan="7" class="px-4 py-8 text-center text-muted-foreground"
								>No results matching "{search}"</td
							></tr
						>
					{:else}
						{#each filteredObjects as obj (obj.key)}
							{@const folder = isObjFolder(obj)}
							<tr
								class="cursor-pointer bg-card transition-colors hover:bg-accent/50"
								onclick={folder ? () => navigatePrefix(obj.key) : () => openViewer(obj)}
								onkeydown={(e: KeyboardEvent) => {
									if (e.key === 'Enter') {
										folder ? navigatePrefix(obj.key) : openViewer(obj);
									}
								}}
								role="button"
								tabindex={0}
							>
								<td class="px-4 py-3" onclick={(e: MouseEvent) => e.stopPropagation()}>
									{#if !folder}<input
											type="checkbox"
											checked={selected.has(obj.key)}
											onchange={() => toggleOne(obj.key)}
											class="h-4 w-4 rounded border-input"
										/>{/if}
								</td>
								<td class="px-4 py-3">
									<span class="flex items-center gap-2">
										{#if folder}<Folder class="h-4 w-4 text-amber-500" />{:else}{@const Icon =
												getFileIcon(obj.key)}<Icon class="h-4 w-4 text-muted-foreground" />{/if}
										<span class="font-medium">{getDisplayName(obj.key)}</span>
									</span>
								</td>
								<td class="px-4 py-3">
									<Tooltip.Root>
										<Tooltip.Trigger
											>{#snippet child({ props })}<span
													class="block max-w-xs truncate font-mono text-xs text-muted-foreground"
													{...props}>{obj.key}</span
												>{/snippet}</Tooltip.Trigger
										>
										<Tooltip.Content class="max-w-lg break-all font-mono text-xs"
											>{obj.key}</Tooltip.Content
										>
									</Tooltip.Root>
								</td>
								<td class="px-4 py-3 text-muted-foreground"
									>{folder ? '-' : getOwnerName(obj) || '-'}</td
								>
								<td class="px-4 py-3 text-muted-foreground"
									>{folder ? '-' : formatBytes(obj.size)}</td
								>
								<td class="px-4 py-3 text-muted-foreground"
									>{obj.last_modified ? formatDate(obj.last_modified) : '-'}</td
								>
								<td class="px-4 py-3" onclick={(e: MouseEvent) => e.stopPropagation()}>
									{#if !folder}
										<span class="flex items-center gap-1">
											<Tooltip.Root>
												<Tooltip.Trigger
													>{#snippet child({ props })}<a
															href={downloadUrl(obj.key)}
															download
															class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-primary"
															{...props}><Download class="h-4 w-4" /></a
														>{/snippet}</Tooltip.Trigger
												>
												<Tooltip.Content>Download</Tooltip.Content>
											</Tooltip.Root>
											<Tooltip.Root>
												<Tooltip.Trigger
													>{#snippet child({ props })}<button
															type="button"
															{...props}
															onclick={() => openShare(obj.key)}
															class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-primary/10 hover:text-primary"
															><Link class="h-4 w-4" /></button
														>{/snippet}</Tooltip.Trigger
												>
												<Tooltip.Content>Share</Tooltip.Content>
											</Tooltip.Root>
											<Tooltip.Root>
												<Tooltip.Trigger
													>{#snippet child({ props })}<button
															type="button"
															{...props}
															onclick={() => del.requestDelete(obj.key)}
															class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
															><Trash2 class="h-4 w-4" /></button
														>{/snippet}</Tooltip.Trigger
												>
												<Tooltip.Content>Delete</Tooltip.Content>
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
	{/await}

	{#if viewerOpen}<FileViewer
			bind:open={viewerOpen}
			url={viewerUrl}
			filename={viewerFilename}
			size={viewerSize}
			objectKey={viewerObject?.key}
			lastModified={viewerObject?.last_modified}
			etag={viewerObject?.etag}
			storageClass={viewerObject?.storage_class}
			hasPrev={viewerHasPrev}
			hasNext={viewerHasNext}
			onprev={viewerPrev}
			onnext={viewerNext}
			currentIndex={viewerIndex}
			totalCount={selectableObjects.length}
			onclose={() => (viewerOpen = false)}
		/>{/if}
</div>

<DeleteConfirmDialog
	bind:open={del.deleteDialogOpen}
	name={del.deleteTarget ? getDisplayName(del.deleteTarget) : ''}
	itemType="object"
	loading={del.deleting}
	onconfirm={handleConfirmDelete}
/>

<Dialog.Root
	open={shareTarget !== null}
	onOpenChange={(open) => {
		if (!open) closeShare();
	}}
>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Generate Presigned URL</Dialog.Title>
			<Dialog.Description>
				Create a temporary URL for accessing this object without credentials.
			</Dialog.Description>
		</Dialog.Header>
		<div class="space-y-4">
			<div class="rounded-lg bg-muted/50 p-3">
				<div class="grid gap-1 text-sm">
					<span class="text-muted-foreground">Bucket</span>
					<span class="font-mono font-medium">{bucket}</span>
					<span class="mt-1 text-muted-foreground">Key</span>
					<span class="break-all font-mono font-medium"
						>{shareTarget ? getDisplayName(shareTarget) : ''}</span
					>
				</div>
			</div>

			<div class="space-y-2">
				<Label>Method</Label>
				<div class="flex gap-2">
					<Button
						variant={shareMethod === 'get_object' ? 'default' : 'outline'}
						size="sm"
						onclick={() => (shareMethod = 'get_object')}
					>
						Download
					</Button>
					<Button
						variant={shareMethod === 'put_object' ? 'default' : 'outline'}
						size="sm"
						onclick={() => (shareMethod = 'put_object')}
					>
						Upload
					</Button>
				</div>
			</div>

			<div class="space-y-2">
				<Label for="share-expiry">Expiry</Label>
				<div class="flex flex-wrap gap-2">
					{#each EXPIRY_PRESETS as preset (preset.value)}
						<Button
							variant={shareExpiry === preset.value ? 'default' : 'outline'}
							size="sm"
							onclick={() => (shareExpiry = preset.value)}
						>
							{preset.label}
						</Button>
					{/each}
				</div>
			</div>

			{#if !shareUrl}
				<Button onclick={handleGenerateUrl} disabled={shareGenerating} class="w-full">
					{#if shareGenerating}
						<Loader2 class="h-4 w-4 animate-spin" />
						Generating...
					{:else}
						Generate URL
					{/if}
				</Button>
			{:else}
				<div class="space-y-2">
					<Label>Presigned URL</Label>
					<div class="flex items-center gap-2">
						<Input readonly value={shareUrl} class="font-mono text-xs" />
						<Tooltip.Root>
							<Tooltip.Trigger>
								{#snippet child({ props })}
									<Button {...props} variant="ghost" size="icon" onclick={copyShareUrl}>
										{#if shareCopied}
											<Check class="h-4 w-4 text-emerald-500" />
										{:else}
											<Copy class="h-4 w-4" />
										{/if}
									</Button>
								{/snippet}
							</Tooltip.Trigger>
							<Tooltip.Content>{shareCopied ? 'Copied!' : 'Copy'}</Tooltip.Content>
						</Tooltip.Root>
					</div>
				</div>
			{/if}
		</div>
		<Dialog.Footer>
			<Button variant="ghost" onclick={closeShare}>Close</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>

<BulkDeleteDialog
	bind:open={del.bulkDeleteOpen}
	count={selected.size}
	itemType="object"
	loading={del.deleting}
	onconfirm={handleConfirmBulkDelete}
/>
