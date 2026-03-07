<script lang="ts">
	import * as Tooltip from '$lib/components/ui/tooltip/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { get_group_permissions, type DataAccessPermissions } from '$lib/users.remote.js';
	import { PERMISSION_DESCRIPTIONS } from '$lib/constants.js';
	import {
		DataTable,
		createSvelteTable,
		getCoreRowModel,
		renderSnippet,
	} from '$lib/components/ui/data-table/index.js';
	import type { ColumnDef } from '@tanstack/table-core';

	let {
		tenant,
		groupname,
	}: {
		tenant: string;
		groupname: string;
	} = $props();

	let permsData = $derived(get_group_permissions({ tenant, groupname }));
	let nsPermissions = $derived(
		((permsData?.current as DataAccessPermissions)?.namespacePermission ?? []).filter(
			(entry) => entry.permissions?.permission && entry.permissions.permission.length > 0
		)
	);

	type NsPermEntry = { namespaceName: string; permissions?: { permission?: string[] } };

	const nsPermColumns: ColumnDef<NsPermEntry>[] = [
		{
			accessorKey: 'namespaceName',
			header: 'Namespace',
			cell: ({ row }) => renderSnippet(nsNameCell, row.original),
			meta: { cellClass: 'px-4 py-3 font-medium' },
		},
		{
			id: 'permissions',
			header: 'Permissions',
			cell: ({ row }) => renderSnippet(nsPermsCell, row.original),
		},
	];

	let nsPermTable = $derived(
		createSvelteTable({
			get data() {
				return nsPermissions;
			},
			columns: nsPermColumns,
			getCoreRowModel: getCoreRowModel(),
		})
	);
</script>

{#snippet nsNameCell(entry: NsPermEntry)}
	<a
		href="/namespaces/{entry.namespaceName}"
		class="text-primary underline-offset-4 hover:underline"
	>
		{entry.namespaceName}
	</a>
{/snippet}

{#snippet nsPermsCell(entry: NsPermEntry)}
	<div class="flex flex-wrap gap-1">
		{#each entry.permissions?.permission ?? [] as perm (perm)}
			<Tooltip.Root>
				<Tooltip.Trigger>
					{#snippet child({ props })}
						<span {...props}><Badge variant="secondary">{perm}</Badge></span>
					{/snippet}
				</Tooltip.Trigger>
				<Tooltip.Content>{PERMISSION_DESCRIPTIONS[perm] ?? perm}</Tooltip.Content>
			</Tooltip.Root>
		{/each}
	</div>
{/snippet}

<section class="space-y-3">
	<h3 class="text-sm font-semibold uppercase tracking-wide text-muted-foreground">
		Namespace Access
	</h3>
	{#await permsData}
		<div class="rounded-lg border p-5">
			<div class="space-y-2">
				{#each Array(3) as _, i (i)}
					<div class="h-5 w-full animate-pulse rounded bg-muted"></div>
				{/each}
			</div>
		</div>
	{:then}
		<DataTable table={nsPermTable} noResultsMessage="This group has no namespace access." />
	{/await}
</section>
