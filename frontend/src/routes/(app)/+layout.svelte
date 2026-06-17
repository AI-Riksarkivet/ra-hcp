<script lang="ts">
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import AppSidebar from '$lib/components/layout/AppSidebar.svelte';
	import AppHeader from '$lib/components/layout/AppHeader.svelte';
	import NavigationProgress from '$lib/components/layout/NavigationProgress.svelte';
	import { Progress } from '$lib/components/ui/progress';
	import { Button } from '$lib/components/ui/button';
	import { deleteProgress, cancelDelete } from '$lib/utils/delete-progress.svelte.js';
	import {
		bulkDeleteProgress,
		cancelBulkDelete
	} from '$lib/utils/bulk-delete-progress.svelte.js';

	let { data, children } = $props();
</script>

<NavigationProgress />
<Sidebar.Provider>
	<AppSidebar accessLevel={data.accessLevel} mapiEnabled={data.mapiEnabled} />
	<Sidebar.Inset>
		<AppHeader
			username={data.username}
			tenant={data.tenant}
			userGUID={data.userGUID}
			sessions={data.sessions}
		/>
		<div class="flex-1 overflow-y-auto p-6">
			{@render children()}
		</div>
	</Sidebar.Inset>
</Sidebar.Provider>

{#if deleteProgress.running || bulkDeleteProgress.running}
	<div class="fixed right-4 bottom-4 z-50 flex w-80 flex-col gap-2">
		{#if deleteProgress.running}
			<div class="bg-background rounded-lg border p-4 shadow-lg">
				<div class="mb-1 flex items-center justify-between text-sm">
					<span class="font-medium">Deleting objects…</span>
					<span class="text-muted-foreground">
						{deleteProgress.deleted.toLocaleString()}{deleteProgress.total
							? ` / ${deleteProgress.total.toLocaleString()}`
							: ''} objects
					</span>
				</div>
				<Progress value={deleteProgress.deleted} max={deleteProgress.total || 1} />
				<div class="mt-2 flex items-center justify-between">
					<span class="text-muted-foreground text-xs">
						{deleteProgress.total
							? `${deleteProgress.percent}%`
							: 'Counting objects…'}{deleteProgress.failed
							? ` · ${deleteProgress.failed.toLocaleString()} failed`
							: ''}
					</span>
					<Button
						size="sm"
						variant="outline"
						disabled={deleteProgress.canceling}
						onclick={cancelDelete}
					>
						{deleteProgress.canceling ? 'Canceling…' : 'Cancel'}
					</Button>
				</div>
			</div>
		{/if}
		{#if bulkDeleteProgress.running}
			<div class="bg-background rounded-lg border p-4 shadow-lg">
				<div class="mb-1 flex items-center justify-between text-sm">
					<span class="font-medium">Deleting {bulkDeleteProgress.entity}s…</span>
					<span class="text-muted-foreground">
						{bulkDeleteProgress.done.toLocaleString()} / {bulkDeleteProgress.total.toLocaleString()}
					</span>
				</div>
				<Progress value={bulkDeleteProgress.done} max={bulkDeleteProgress.total || 1} />
				<div class="mt-2 flex items-center justify-between">
					<span class="text-muted-foreground text-xs">
						{bulkDeleteProgress.percent}%{bulkDeleteProgress.failed
							? ` · ${bulkDeleteProgress.failed.toLocaleString()} failed`
							: ''}
					</span>
					<Button size="sm" variant="outline" onclick={cancelBulkDelete}>Cancel</Button>
				</div>
			</div>
		{/if}
	</div>
{/if}
