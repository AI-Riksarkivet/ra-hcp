<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Skeleton } from '$lib/components/ui/skeleton/index.js';
	import { get_lance_schema } from '$lib/remote/lance.remote.js';
	import type { LanceField } from '$lib/types/lance.js';
	import { FileType, Waypoints } from 'lucide-svelte';

	let { bucket, path, table }: { bucket: string; path: string; table: string } = $props();

	let schemaData = $derived(get_lance_schema({ bucket, path: path || undefined, table }));
	let fields = $derived((schemaData?.current?.fields ?? []) as LanceField[]);
</script>

<Card.Root>
	<Card.Header>
		<div class="flex items-center gap-2">
			<FileType class="h-4 w-4 text-muted-foreground" />
			<Card.Title class="text-sm">Schema — {table}</Card.Title>
			<Badge variant="secondary" class="ml-auto">{fields.length} fields</Badge>
		</div>
	</Card.Header>
	<Card.Content>
		{#if fields.length === 0}
			<div class="space-y-2">
				{#each Array(4) as _, i (i)}
					<Skeleton class="h-6 w-full" />
				{/each}
			</div>
		{:else}
			<div class="grid gap-1 font-mono text-xs">
				{#each fields as field (field.name)}
					<div
						class="flex items-center gap-2 rounded px-2 py-1
							{field.is_vector ? 'bg-blue-50 dark:bg-blue-950/20' : ''}"
					>
						<span class="font-medium">{field.name}</span>
						<span class="text-muted-foreground">{field.type}</span>
						{#if field.is_vector}
							<Badge variant="outline" class="ml-auto gap-1 text-xs">
								<Waypoints class="h-3 w-3" />
								vector{field.vector_dim ? ` [${field.vector_dim}]` : ''}
							</Badge>
						{:else if field.is_binary}
							<Badge variant="outline" class="ml-auto gap-1 text-xs text-amber-600">binary</Badge>
						{/if}
					</div>
				{/each}
			</div>
		{/if}
	</Card.Content>
</Card.Root>
