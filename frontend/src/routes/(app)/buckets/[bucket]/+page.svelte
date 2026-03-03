<script lang="ts">
	import { page } from '$app/state';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as AlertDialog from '$lib/components/ui/alert-dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Progress } from '$lib/components/ui/progress/index.js';
	import {
		ArrowLeft,
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
	} from 'lucide-svelte';
	import FileViewer from '$lib/components/ui/FileViewer.svelte';
	import { formatBytes, formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import { get_objects, delete_object, bulk_delete_objects } from '$lib/buckets.remote.js';

	let bucket = $derived(page.params.bucket ?? '');
	let prefix = $derived(page.url.searchParams.get('prefix') ?? '');
	let objectData = $derived(get_objects({ bucket, prefix }));

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

	let objects = $derived((objectData.current?.objects ?? []) as any[]);
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
	function isObjFolder(obj: { size: number; key: string }): boolean {
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
	let filteredObjects = $derived(
		objects.filter((obj: { key: string }) => {
			if (!search) return true;
			const q = search.toLowerCase();
			return getDisplayName(obj.key).toLowerCase().includes(q) || obj.key.toLowerCase().includes(q);
		})
	);

	let selected = $state<Set<string>>(new Set());
	let selectableObjects = $derived(
		filteredObjects.filter((obj: { size: number; key: string }) => !isObjFolder(obj))
	);
	let allSelected = $derived(
		selectableObjects.length > 0 &&
			selectableObjects.every((obj: { key: string }) => selected.has(obj.key))
	);

	function toggleAll() {
		if (allSelected) {
			selected = new Set();
		} else {
			selected = new Set(selectableObjects.map((obj: { key: string }) => obj.key));
		}
	}
	function toggleOne(key: string) {
		const next = new Set(selected);
		if (next.has(key)) {
			next.delete(key);
		} else {
			next.add(key);
		}
		selected = next;
	}

	let deleteTarget = $state<string | null>(null);
	let bulkDeleteOpen = $state(false);
	let deleting = $state(false);

	async function confirmDelete() {
		if (!deleteTarget) return;
		deleting = true;
		try {
			await delete_object({ bucket, key: deleteTarget }).updates(objectData);
			toast.success(`Deleted ${getDisplayName(deleteTarget)}`);
		} catch {
			toast.error('Failed to delete object');
		} finally {
			deleting = false;
			deleteTarget = null;
		}
	}

	async function confirmBulkDelete() {
		deleting = true;
		const keys = [...selected];
		try {
			await bulk_delete_objects({ bucket, keys }).updates(objectData);
			toast.success(`Deleted ${keys.length} object${keys.length !== 1 ? 's' : ''}`);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to delete objects');
		}
		selected = new Set();
		deleting = false;
		bulkDeleteOpen = false;
	}
</script>

<svelte:head><title>{bucket} - HCP Admin Console</title></svelte:head>

<div class="space-y-6">
	<div class="flex items-center justify-between">
		<div class="flex items-center gap-4">
			<Tooltip.Root>
				<Tooltip.Trigger>
					{#snippet child({ props })}
						<a
							href="/buckets"
							class="rounded-lg p-2 text-muted-foreground transition-colors hover:bg-accent hover:text-foreground"
							{...props}><ArrowLeft class="h-5 w-5" /></a
						>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Content>Back to buckets</Tooltip.Content>
			</Tooltip.Root>
			<div>
				<h2 class="text-2xl font-bold">{bucket}</h2>
				{#if prefix}<p class="mt-1 text-sm text-muted-foreground">
						<code class="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{prefix}</code>
					</p>{/if}
			</div>
			{#await objectData then od}
				<Badge variant="secondary">{od.keyCount} objects</Badge>
			{/await}
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

			<!-- svelte-ignore a11y_no_static_element_interactions -->
			<div
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
					{#each selectedFiles as item, i}
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
		<TableSkeleton rows={5} columns={6} />
	{:then _}
		<div class="relative">
			<Search class="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
			<input
				type="text"
				bind:value={search}
				placeholder="Search objects..."
				class="w-full rounded-lg border bg-background py-2 pl-10 pr-3 text-sm shadow-sm transition-colors placeholder:text-muted-foreground focus:border-ring focus:outline-none focus:ring-2 focus:ring-ring/20"
			/>
		</div>

		{#if selected.size > 0}
			<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
				<span class="text-sm font-medium">{selected.size} selected</span>
				<Button variant="destructive" size="sm" onclick={() => (bulkDeleteOpen = true)}
					><Trash2 class="h-3.5 w-3.5" />Delete Selected</Button
				>
				<Button variant="ghost" size="sm" onclick={() => (selected = new Set())}
					>Deselect All</Button
				>
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
						<th class="w-32 px-4 py-3 font-medium">Size</th>
						<th class="w-48 px-4 py-3 font-medium">Last Modified</th>
						<th class="w-24 px-4 py-3 font-medium">Actions</th>
					</tr>
				</thead>
				<tbody class="divide-y">
					{#if objects.length === 0}<tr
							><td colspan="6" class="px-4 py-8 text-center text-muted-foreground"
								>No objects in this bucket</td
							></tr
						>
					{:else if filteredObjects.length === 0}<tr
							><td colspan="6" class="px-4 py-8 text-center text-muted-foreground"
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
								<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
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
									>{folder ? '-' : formatBytes(obj.size)}</td
								>
								<td class="px-4 py-3 text-muted-foreground"
									>{obj.last_modified ? formatDate(obj.last_modified) : '-'}</td
								>
								<!-- svelte-ignore a11y_no_noninteractive_element_interactions -->
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
															onclick={() => (deleteTarget = obj.key)}
															class="rounded-lg p-1.5 text-muted-foreground transition-colors hover:bg-destructive/10 hover:text-destructive"
															{...props}><Trash2 class="h-4 w-4" /></button
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
			onclose={() => (viewerOpen = false)}
		/>{/if}
</div>

<AlertDialog.Root
	open={deleteTarget !== null}
	onOpenChange={(open) => {
		if (!open) deleteTarget = null;
	}}
>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title>Delete Object</AlertDialog.Title>
			<AlertDialog.Description
				>Are you sure you want to delete "<strong
					>{deleteTarget ? getDisplayName(deleteTarget) : ''}</strong
				>"? This action cannot be undone.</AlertDialog.Description
			>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel disabled={deleting}>Cancel</AlertDialog.Cancel>
			<Button variant="destructive" onclick={confirmDelete} disabled={deleting}
				>{deleting ? 'Deleting...' : 'Delete'}</Button
			>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>

<AlertDialog.Root bind:open={bulkDeleteOpen}>
	<AlertDialog.Content>
		<AlertDialog.Header>
			<AlertDialog.Title
				>Delete {selected.size} Object{selected.size !== 1 ? 's' : ''}</AlertDialog.Title
			>
			<AlertDialog.Description
				>Are you sure you want to delete {selected.size} object{selected.size !== 1 ? 's' : ''}?
				This action cannot be undone.</AlertDialog.Description
			>
		</AlertDialog.Header>
		<AlertDialog.Footer>
			<AlertDialog.Cancel disabled={deleting}>Cancel</AlertDialog.Cancel>
			<Button variant="destructive" onclick={confirmBulkDelete} disabled={deleting}
				>{deleting
					? 'Deleting...'
					: `Delete ${selected.size} Object${selected.size !== 1 ? 's' : ''}`}</Button
			>
		</AlertDialog.Footer>
	</AlertDialog.Content>
</AlertDialog.Root>
