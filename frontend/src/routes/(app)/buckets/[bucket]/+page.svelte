<script lang="ts">
	import { page } from '$app/state';
	import {
		type ColumnDef,
		type ColumnFiltersState,
		type PaginationState,
		type RowSelectionState,
		type SortingState,
		type VisibilityState,
		getCoreRowModel,
		getFilteredRowModel,
		getPaginationRowModel,
		getSortedRowModel,
	} from '@tanstack/table-core';
	import { createRawSnippet } from 'svelte';
	import ChevronDown from 'lucide-svelte/icons/chevron-down';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Progress } from '$lib/components/ui/progress/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import {
		FlexRender,
		createSvelteTable,
		renderComponent,
		renderSnippet,
	} from '$lib/components/ui/data-table/index.js';
	import DataTableCheckbox from '$lib/components/ui/data-table/data-table-checkbox.svelte';
	import DataTableActions from './data-table/data-table-actions.svelte';
	import DataTableHeaderButton from '$lib/components/ui/data-table/data-table-header-button.svelte';
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
		Link,
		Copy,
		Check,
	} from 'lucide-svelte';
	import FileViewer from '$lib/components/ui/FileViewer.svelte';
	import { formatBytes, formatDate } from '$lib/utils/format.js';
	import { goto } from '$app/navigation';
	import { toast } from 'svelte-sonner';
	import TableSkeleton from '$lib/components/ui/skeleton/table-skeleton.svelte';
	import DeleteConfirmDialog from '$lib/components/ui/delete-confirm-dialog.svelte';
	import {
		get_objects,
		delete_object,
		bulk_delete_objects,
		bulk_presign,
		generate_presigned_url,
	} from '$lib/buckets.remote.js';

	// ── Route state ────────────────────────────────────────────────
	let bucket = $derived(page.params.bucket ?? '');
	let prefix = $derived(page.url.searchParams.get('prefix') ?? '');
	let objectData = $derived(get_objects({ bucket, prefix }));

	// ── Data model ─────────────────────────────────────────────────
	interface S3Object {
		key: string;
		size: number;
		last_modified: string;
		etag: string;
		storage_class: string;
		owner: {
			display_name?: string;
			id?: string;
			DisplayName?: string;
			ID?: string;
		} | null;
		isFolder: boolean;
	}

	function getOwnerName(obj: S3Object): string {
		return obj.owner?.display_name ?? obj.owner?.DisplayName ?? '';
	}
	function getDisplayName(key: string): string {
		return key.split('/').filter(Boolean).pop() ?? key;
	}
	function downloadUrlFor(key: string): string {
		return `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${encodeURIComponent(key)}`;
	}
	function getFileIcon(name: string) {
		const ext = name.split('.').pop()?.toLowerCase() ?? '';
		if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg', 'bmp'].includes(ext)) return Image;
		if (['zip', 'tar', 'gz', 'rar', '7z'].includes(ext)) return FileArchive;
		if (['js', 'ts', 'py', 'json', 'html', 'css', 'xml', 'yaml', 'yml', 'toml'].includes(ext))
			return FileCode;
		return FileText;
	}
	function navigatePrefix(p: string) {
		goto(`/buckets/${bucket}?prefix=${encodeURIComponent(p)}`);
	}

	let rawObjects = $derived(
		((objectData.current?.objects ?? []) as Omit<S3Object, 'isFolder'>[]).map(
			(o) => ({ ...o, isFolder: false }) as S3Object
		)
	);
	let commonPrefixes = $derived((objectData.current?.commonPrefixes ?? []) as string[]);
	let folderEntries = $derived<S3Object[]>(
		commonPrefixes.map((p) => ({
			key: p,
			size: 0,
			last_modified: '',
			etag: '',
			storage_class: '',
			owner: null,
			isFolder: true,
		}))
	);
	let data = $derived<S3Object[]>([...folderEntries, ...rawObjects]);
	let keyCount = $derived(objectData.current?.keyCount ?? 0);

	// ── Column definitions ─────────────────────────────────────────
	const columns: ColumnDef<S3Object>[] = [
		{
			id: 'select',
			header: ({ table: t }) =>
				renderComponent(DataTableCheckbox, {
					checked: t.getIsAllPageRowsSelected(),
					indeterminate: t.getIsSomePageRowsSelected() && !t.getIsAllPageRowsSelected(),
					onCheckedChange: (value: boolean) => t.toggleAllPageRowsSelected(!!value),
					'aria-label': 'Select all',
				}),
			cell: ({ row }) => {
				if (row.original.isFolder) {
					const empty = createRawSnippet(() => ({ render: () => '' }));
					return renderSnippet(empty);
				}
				return renderComponent(DataTableCheckbox, {
					checked: row.getIsSelected(),
					onCheckedChange: (value: boolean) => row.toggleSelected(!!value),
					'aria-label': 'Select row',
				});
			},
			enableSorting: false,
			enableHiding: false,
		},
		{
			accessorKey: 'key',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Name',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ displayName: string; isFolder: boolean; fullKey: string }]>(
					(getProps) => {
						const { displayName, isFolder, fullKey } = getProps();
						const icon = isFolder
							? '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-amber-500 inline-block mr-2 align-text-bottom"><path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.9a2 2 0 0 1-1.69-.9L9.6 3.9A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/></svg>'
							: '<svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="text-muted-foreground inline-block mr-2 align-text-bottom"><path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/></svg>';
						return {
							render: () =>
								`<span class="flex items-center gap-1" title="${fullKey}">${icon}<span class="font-medium">${displayName}</span></span>`,
						};
					}
				);
				return renderSnippet(s, {
					displayName: getDisplayName(row.original.key),
					isFolder: row.original.isFolder,
					fullKey: row.original.key,
				});
			},
			filterFn: (row, _columnId, filterValue) => {
				const q = (filterValue as string).toLowerCase();
				return (
					getDisplayName(row.original.key).toLowerCase().includes(q) ||
					row.original.key.toLowerCase().includes(q)
				);
			},
		},
		{
			accessorKey: 'owner',
			header: 'Owner',
			accessorFn: (row) => getOwnerName(row),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ owner: string }]>((getOwner) => {
					const { owner } = getOwner();
					return {
						render: () =>
							`<span class="text-muted-foreground">${row.original.isFolder ? '-' : owner || '-'}</span>`,
					};
				});
				return renderSnippet(s, { owner: getOwnerName(row.original) });
			},
			filterFn: 'equalsString',
		},
		{
			accessorKey: 'size',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Size',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ size: string }]>((getSize) => {
					const { size } = getSize();
					return {
						render: () => `<span class="text-muted-foreground">${size}</span>`,
					};
				});
				return renderSnippet(s, {
					size: row.original.isFolder ? '-' : formatBytes(row.original.size),
				});
			},
		},
		{
			accessorKey: 'last_modified',
			header: ({ column }) =>
				renderComponent(DataTableHeaderButton, {
					label: 'Last Modified',
					onclick: column.getToggleSortingHandler(),
				}),
			cell: ({ row }) => {
				const s = createRawSnippet<[{ date: string }]>((getDate) => {
					const { date } = getDate();
					return {
						render: () => `<span class="text-muted-foreground">${date}</span>`,
					};
				});
				return renderSnippet(s, {
					date: row.original.last_modified ? formatDate(row.original.last_modified) : '-',
				});
			},
			sortingFn: (a, b) => {
				const da = new Date(a.original.last_modified || 0).getTime();
				const db = new Date(b.original.last_modified || 0).getTime();
				return da - db;
			},
		},
		{
			id: 'actions',
			enableHiding: false,
			cell: ({ row }) => {
				if (row.original.isFolder) {
					const empty = createRawSnippet(() => ({ render: () => '' }));
					return renderSnippet(empty);
				}
				return renderComponent(DataTableActions, {
					objectKey: row.original.key,
					downloadUrl: downloadUrlFor(row.original.key),
					ondelete: () => {
						deleteTarget = row.original.key;
						deleteDialogOpen = true;
					},
					onshare: () => openShare(row.original.key),
					onview: () => openViewer(row.original),
				});
			},
		},
	];

	// ── Table state ────────────────────────────────────────────────
	let pagination = $state<PaginationState>({ pageIndex: 0, pageSize: 50 });
	let sorting = $state<SortingState>([]);
	let columnFilters = $state<ColumnFiltersState>([]);
	let rowSelection = $state<RowSelectionState>({});
	let columnVisibility = $state<VisibilityState>({});

	const table = createSvelteTable({
		get data() {
			return data;
		},
		columns,
		enableRowSelection: (row) => !row.original.isFolder,
		state: {
			get pagination() {
				return pagination;
			},
			get sorting() {
				return sorting;
			},
			get columnFilters() {
				return columnFilters;
			},
			get columnVisibility() {
				return columnVisibility;
			},
			get rowSelection() {
				return rowSelection;
			},
		},
		getCoreRowModel: getCoreRowModel(),
		getPaginationRowModel: getPaginationRowModel(),
		getSortedRowModel: getSortedRowModel(),
		getFilteredRowModel: getFilteredRowModel(),
		onPaginationChange: (updater) => {
			pagination = typeof updater === 'function' ? updater(pagination) : updater;
		},
		onSortingChange: (updater) => {
			sorting = typeof updater === 'function' ? updater(sorting) : updater;
		},
		onColumnFiltersChange: (updater) => {
			columnFilters = typeof updater === 'function' ? updater(columnFilters) : updater;
		},
		onColumnVisibilityChange: (updater) => {
			columnVisibility = typeof updater === 'function' ? updater(columnVisibility) : updater;
		},
		onRowSelectionChange: (updater) => {
			rowSelection = typeof updater === 'function' ? updater(rowSelection) : updater;
		},
	});

	let selectedCount = $derived(table.getFilteredSelectedRowModel().rows.length);

	// ── File Viewer ────────────────────────────────────────────────
	let viewerOpen = $state(false);
	let viewerIndex = $state(-1);

	let selectableRows = $derived(
		table.getFilteredRowModel().rows.filter((r) => !r.original.isFolder)
	);
	let viewerObject = $derived(viewerIndex >= 0 ? selectableRows[viewerIndex]?.original : undefined);
	let viewerUrl = $derived(viewerObject ? downloadUrlFor(viewerObject.key) : '');
	let viewerFilename = $derived(viewerObject ? getDisplayName(viewerObject.key) : '');
	let viewerSize = $derived(viewerObject?.size ?? 0);
	let viewerHasPrev = $derived(viewerIndex > 0);
	let viewerHasNext = $derived(viewerIndex < selectableRows.length - 1);

	function openViewer(obj: S3Object) {
		viewerIndex = selectableRows.findIndex((r) => r.original.key === obj.key);
		viewerOpen = true;
	}
	function viewerPrev() {
		if (viewerHasPrev) viewerIndex--;
	}
	function viewerNext() {
		if (viewerHasNext) viewerIndex++;
	}

	// ── Upload ─────────────────────────────────────────────────────
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
				selectedFiles[index] = {
					...selectedFiles[index],
					status: 'error',
					error: 'Network error',
				};
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
			if (selectedFiles[i].status === 'pending') await uploadFile(i);
		}
		uploading = false;
		const doneCount = selectedFiles.filter((f) => f.status === 'done').length;
		const errCount = selectedFiles.filter((f) => f.status === 'error').length;
		if (doneCount > 0) toast.success(`Uploaded ${doneCount} file${doneCount !== 1 ? 's' : ''}`);
		if (errCount > 0) toast.error(`${errCount} file${errCount !== 1 ? 's' : ''} failed`);
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

	// ── Presigned URL ──────────────────────────────────────────────
	const EXPIRY_PRESETS = [
		{ label: '5 min', value: 300 },
		{ label: '1 hr', value: 3600 },
		{ label: '6 hr', value: 21600 },
		{ label: '24 hr', value: 86400 },
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

	// ── Bulk download ──────────────────────────────────────────────
	let downloading = $state(false);
	async function bulkDownload() {
		const keys = table
			.getFilteredSelectedRowModel()
			.rows.map((r) => r.original.key)
			.filter((k) => !k.endsWith('/'));
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
				await new Promise((r) => setTimeout(r, 150));
			}
			toast.success(
				`Started downloading ${result.urls.length} file${result.urls.length !== 1 ? 's' : ''}`
			);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to download');
		} finally {
			downloading = false;
		}
	}

	// ── Delete ─────────────────────────────────────────────────────
	let deleteTarget = $state('');
	let deleteDialogOpen = $state(false);
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
			deleteDialogOpen = false;
			deleteTarget = '';
		}
	}
	async function confirmBulkDelete() {
		deleting = true;
		const keys = table.getFilteredSelectedRowModel().rows.map((r) => r.original.key);
		try {
			await bulk_delete_objects({ bucket, keys }).updates(objectData);
			toast.success(`Deleted ${keys.length} object${keys.length !== 1 ? 's' : ''}`);
		} catch (err) {
			toast.error(err instanceof Error ? err.message : 'Failed to delete objects');
		}
		rowSelection = {};
		deleting = false;
		bulkDeleteOpen = false;
	}
</script>

<svelte:head><title>{bucket} - HCP Admin Console</title></svelte:head>

<div class="space-y-4">
	<!-- Header -->
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
				{#if prefix}
					<p class="mt-1 text-sm text-muted-foreground">
						<code class="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{prefix}</code>
					</p>
				{/if}
			</div>
			{#await objectData then _od}
				<Badge variant="secondary">{keyCount} objects</Badge>
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
			{#if prefix}
				<p class="text-sm text-muted-foreground">
					Prefix: <code class="rounded bg-muted px-1.5 py-0.5 font-mono text-xs">{prefix}</code>
				</p>
			{/if}
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
					{#each selectedFiles as item, i}
						<div class="flex items-center gap-3 rounded-lg border p-2">
							{#if item.preview}
								<img
									src={item.preview}
									alt={item.file.name}
									class="h-12 w-12 rounded object-cover"
								/>
							{:else}
								{@const Icon = getFileIcon(item.file.name)}
								<div class="flex h-12 w-12 items-center justify-center rounded bg-muted">
									<Icon class="h-6 w-6 text-muted-foreground" />
								</div>
							{/if}
							<div class="min-w-0 flex-1">
								<p class="truncate text-sm font-medium">{item.file.name}</p>
								{#if item.status === 'pending'}
									<input
										type="text"
										value={item.key}
										oninput={(e) => {
											selectedFiles[i] = { ...selectedFiles[i], key: e.currentTarget.value };
										}}
										class="mt-1 w-full rounded border bg-background px-2 py-0.5 font-mono text-xs text-muted-foreground"
										placeholder="Object key"
									/>
								{:else}
									<p class="mt-0.5 truncate font-mono text-xs text-muted-foreground">
										{item.key}
									</p>
								{/if}
								<p class="text-xs text-muted-foreground">{formatBytes(item.file.size)}</p>
								{#if item.status === 'uploading'}
									<Progress value={item.progress} max={100} class="mt-1 h-1.5" />
								{/if}
							</div>
							{#if item.status === 'uploading'}
								<span class="text-xs font-medium text-primary">{item.progress}%</span>
							{:else if item.status === 'done'}
								<CheckCircle class="h-5 w-5 text-emerald-500" />
							{:else if item.status === 'error'}
								<Tooltip.Root>
									<Tooltip.Trigger>
										{#snippet child({ props })}
											<span {...props}><AlertCircle class="h-5 w-5 text-destructive" /></span>
										{/snippet}
									</Tooltip.Trigger>
									<Tooltip.Content
										class="max-w-xs border-destructive/20 bg-destructive/10 text-destructive"
									>
										{item.error}
									</Tooltip.Content>
								</Tooltip.Root>
							{:else}
								<button
									onclick={() => removeFile(i)}
									class="rounded p-1 text-muted-foreground hover:text-destructive"
									title="Remove"><X class="h-4 w-4" /></button
								>
							{/if}
						</div>
					{/each}
				</div>
			{/if}
			<Dialog.Footer>
				<Button variant="ghost" onclick={closeUpload} disabled={uploading}>
					{allDone ? 'Close' : 'Cancel'}
				</Button>
				{#if !allDone}
					<Button
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
					</Button>
				{/if}
			</Dialog.Footer>
		</Dialog.Content>
	</Dialog.Root>

	{#if prefix}
		<button
			onclick={() => navigatePrefix(parentPrefix)}
			class="flex items-center gap-2 text-sm text-primary hover:underline"
		>
			<Folder class="h-4 w-4" />.. (parent directory)
		</button>
	{/if}

	{#await objectData}
		<TableSkeleton rows={5} columns={7} />
	{:then _}
		<!-- Toolbar -->
		<div class="flex items-center gap-2">
			<Input
				placeholder="Filter objects..."
				value={(table.getColumn('key')?.getFilterValue() as string) ?? ''}
				oninput={(e) => table.getColumn('key')?.setFilterValue(e.currentTarget.value)}
				class="max-w-sm"
			/>
			<DropdownMenu.Root>
				<DropdownMenu.Trigger>
					{#snippet child({ props })}
						<Button {...props} variant="outline" class="ml-auto">
							Columns <ChevronDown class="ml-2 size-4" />
						</Button>
					{/snippet}
				</DropdownMenu.Trigger>
				<DropdownMenu.Content align="end">
					{#each table.getAllColumns().filter((col) => col.getCanHide()) as column (column.id)}
						<DropdownMenu.CheckboxItem
							class="capitalize"
							checked={column.getIsVisible()}
							onCheckedChange={(v) => column.toggleVisibility(!!v)}
						>
							{column.id === 'key'
								? 'name'
								: column.id === 'last_modified'
									? 'last modified'
									: column.id}
						</DropdownMenu.CheckboxItem>
					{/each}
				</DropdownMenu.Content>
			</DropdownMenu.Root>
		</div>

		{#if selectedCount > 0}
			<div class="flex items-center gap-3 rounded-lg border bg-muted/50 px-4 py-2">
				<span class="text-sm font-medium">{selectedCount} selected</span>
				<Button size="sm" onclick={bulkDownload} disabled={downloading}>
					{#if downloading}<Loader2 class="h-3.5 w-3.5 animate-spin" />{:else}<Download
							class="h-3.5 w-3.5"
						/>{/if}
					Download
				</Button>
				<Button variant="destructive" size="sm" onclick={() => (bulkDeleteOpen = true)}>
					<Trash2 class="h-3.5 w-3.5" />Delete
				</Button>
				<Button variant="ghost" size="sm" onclick={() => (rowSelection = {})}>Deselect All</Button>
			</div>
		{/if}

		<!-- Table -->
		<div class="rounded-md border">
			<Table.Root>
				<Table.Header>
					{#each table.getHeaderGroups() as headerGroup (headerGroup.id)}
						<Table.Row>
							{#each headerGroup.headers as header (header.id)}
								<Table.Head class="[&:has([role=checkbox])]:ps-3">
									{#if !header.isPlaceholder}
										<FlexRender
											content={header.column.columnDef.header}
											context={header.getContext()}
										/>
									{/if}
								</Table.Head>
							{/each}
						</Table.Row>
					{/each}
				</Table.Header>
				<Table.Body>
					{#each table.getRowModel().rows as row (row.id)}
						<Table.Row
							data-state={row.getIsSelected() && 'selected'}
							class="cursor-pointer"
							onclick={() => {
								if (row.original.isFolder) {
									navigatePrefix(row.original.key);
								} else {
									openViewer(row.original);
								}
							}}
						>
							{#each row.getVisibleCells() as cell (cell.id)}
								<Table.Cell
									class="[&:has([role=checkbox])]:ps-3"
									onclick={(e) => {
										const target = e.target as HTMLElement;
										if (
											target.closest('[role=checkbox]') ||
											target.closest('[role=menuitem]') ||
											target.closest('button') ||
											target.closest('a')
										) {
											e.stopPropagation();
										}
									}}
								>
									<FlexRender content={cell.column.columnDef.cell} context={cell.getContext()} />
								</Table.Cell>
							{/each}
						</Table.Row>
					{:else}
						<Table.Row>
							<Table.Cell colspan={columns.length} class="h-24 text-center">
								No objects in this bucket.
							</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
		</div>

		<!-- Pagination -->
		<div class="flex items-center justify-end space-x-2">
			<div class="flex-1 text-sm text-muted-foreground">
				{table.getFilteredSelectedRowModel().rows.length} of
				{table.getFilteredRowModel().rows.length} row(s) selected.
			</div>
			<div class="space-x-2">
				<Button
					variant="outline"
					size="sm"
					onclick={() => table.previousPage()}
					disabled={!table.getCanPreviousPage()}
				>
					Previous
				</Button>
				<Button
					variant="outline"
					size="sm"
					onclick={() => table.nextPage()}
					disabled={!table.getCanNextPage()}
				>
					Next
				</Button>
			</div>
		</div>
	{/await}

	{#if viewerOpen}
		<FileViewer
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
			totalCount={selectableRows.length}
			onclose={() => (viewerOpen = false)}
		/>
	{/if}
</div>

<DeleteConfirmDialog
	bind:open={deleteDialogOpen}
	name={deleteTarget ? getDisplayName(deleteTarget) : ''}
	itemType="object"
	loading={deleting}
	onconfirm={confirmDelete}
/>

<!-- Share dialog -->
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
						onclick={() => (shareMethod = 'get_object')}>Download</Button
					>
					<Button
						variant={shareMethod === 'put_object' ? 'default' : 'outline'}
						size="sm"
						onclick={() => (shareMethod = 'put_object')}>Upload</Button
					>
				</div>
			</div>
			<div class="space-y-2">
				<Label>Expiry</Label>
				<div class="flex flex-wrap gap-2">
					{#each EXPIRY_PRESETS as preset (preset.value)}
						<Button
							variant={shareExpiry === preset.value ? 'default' : 'outline'}
							size="sm"
							onclick={() => (shareExpiry = preset.value)}>{preset.label}</Button
						>
					{/each}
				</div>
			</div>
			{#if !shareUrl}
				<Button onclick={handleGenerateUrl} disabled={shareGenerating} class="w-full">
					{#if shareGenerating}
						<Loader2 class="h-4 w-4 animate-spin" />Generating...
					{:else}Generate URL{/if}
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
										{#if shareCopied}<Check class="h-4 w-4 text-emerald-500" />{:else}<Copy
												class="h-4 w-4"
											/>{/if}
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

<!-- Bulk delete dialog -->
<Dialog.Root bind:open={bulkDeleteOpen}>
	<Dialog.Content class="sm:max-w-md">
		<Dialog.Header>
			<Dialog.Title>Delete {selectedCount} objects?</Dialog.Title>
			<Dialog.Description>This action cannot be undone.</Dialog.Description>
		</Dialog.Header>
		<Dialog.Footer>
			<Button variant="ghost" onclick={() => (bulkDeleteOpen = false)}>Cancel</Button>
			<Button variant="destructive" onclick={confirmBulkDelete} disabled={deleting}>
				{deleting ? 'Deleting...' : 'Delete All'}
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
