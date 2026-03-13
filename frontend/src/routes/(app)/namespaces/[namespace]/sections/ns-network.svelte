<script lang="ts">
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Tabs from '$lib/components/ui/tabs/index.js';
	import { Switch } from '$lib/components/ui/switch/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import CardSkeleton from '$lib/components/ui/skeleton/card-skeleton.svelte';
	import SaveButton from '$lib/components/custom/save-button/save-button.svelte';
	import IpListEditor from '$lib/components/custom/ip-list-editor/ip-list-editor.svelte';
	import { useSave } from '$lib/utils/use-save.svelte.js';
	import {
		get_ns_protocol_detail,
		update_ns_protocol,
		type IpSettings,
	} from '$lib/remote/namespaces.remote.js';

	const PROTOCOLS = ['http', 'nfs', 'cifs', 'smtp'] as const;
	type Protocol = (typeof PROTOCOLS)[number];

	const PROTOCOL_LABELS: Record<Protocol, string> = {
		http: 'HTTP / S3',
		nfs: 'NFS',
		cifs: 'CIFS',
		smtp: 'SMTP',
	};

	const PROTOCOL_DESCRIPTIONS: Record<Protocol, string> = {
		http: 'Controls which IP addresses can access this namespace via HTTP, REST, S3, and WebDAV.',
		nfs: 'Controls which IP addresses can mount this namespace via NFS. NFS uses IP-based access control only — no username/password.',
		cifs: 'Controls which IP addresses can access this namespace via CIFS/SMB file sharing.',
		smtp: 'Controls which IP addresses can send email to this namespace via SMTP.',
	};

	let {
		tenant,
		namespaceName,
	}: {
		tenant: string;
		namespaceName: string;
	} = $props();

	let activeProtocol = $state<Protocol>('http');

	// Fetch all protocol details
	let httpData = $derived(
		get_ns_protocol_detail({ tenant, name: namespaceName, protocol: 'http' })
	);
	let nfsData = $derived(get_ns_protocol_detail({ tenant, name: namespaceName, protocol: 'nfs' }));
	let cifsData = $derived(
		get_ns_protocol_detail({ tenant, name: namespaceName, protocol: 'cifs' })
	);
	let smtpData = $derived(
		get_ns_protocol_detail({ tenant, name: namespaceName, protocol: 'smtp' })
	);

	function getQueryData(proto: Protocol) {
		switch (proto) {
			case 'http':
				return httpData;
			case 'nfs':
				return nfsData;
			case 'cifs':
				return cifsData;
			case 'smtp':
				return smtpData;
		}
	}

	function getIpSettings(proto: Protocol): IpSettings {
		return (getQueryData(proto)?.current?.ipSettings ?? {}) as IpSettings;
	}

	// Per-protocol savers
	const httpSaver = useSave({
		successMsg: 'HTTP network restrictions updated',
		errorMsg: 'Failed to update HTTP network restrictions',
	});
	const nfsSaver = useSave({
		successMsg: 'NFS network restrictions updated',
		errorMsg: 'Failed to update NFS network restrictions',
	});
	const cifsSaver = useSave({
		successMsg: 'CIFS network restrictions updated',
		errorMsg: 'Failed to update CIFS network restrictions',
	});
	const smtpSaver = useSave({
		successMsg: 'SMTP network restrictions updated',
		errorMsg: 'Failed to update SMTP network restrictions',
	});

	function getSaver(proto: Protocol) {
		switch (proto) {
			case 'http':
				return httpSaver;
			case 'nfs':
				return nfsSaver;
			case 'cifs':
				return cifsSaver;
			case 'smtp':
				return smtpSaver;
		}
	}

	// Per-protocol local state
	let httpAllow = $state<string[]>([]);
	let httpDeny = $state<string[]>([]);
	let httpBoth = $state(false);

	let nfsAllow = $state<string[]>([]);
	let nfsDeny = $state<string[]>([]);
	let nfsBoth = $state(false);

	let cifsAllow = $state<string[]>([]);
	let cifsDeny = $state<string[]>([]);
	let cifsBoth = $state(false);

	let smtpAllow = $state<string[]>([]);
	let smtpDeny = $state<string[]>([]);
	let smtpBoth = $state(false);

	// Sync effects for each protocol
	$effect(() => {
		const s = getIpSettings('http');
		void httpSaver.syncVersion;
		httpAllow = [...(s.allowAddresses ?? [])];
		httpDeny = [...(s.denyAddresses ?? [])];
		httpBoth = s.allowIfInBothLists ?? false;
	});

	$effect(() => {
		const s = getIpSettings('nfs');
		void nfsSaver.syncVersion;
		nfsAllow = [...(s.allowAddresses ?? [])];
		nfsDeny = [...(s.denyAddresses ?? [])];
		nfsBoth = s.allowIfInBothLists ?? false;
	});

	$effect(() => {
		const s = getIpSettings('cifs');
		void cifsSaver.syncVersion;
		cifsAllow = [...(s.allowAddresses ?? [])];
		cifsDeny = [...(s.denyAddresses ?? [])];
		cifsBoth = s.allowIfInBothLists ?? false;
	});

	$effect(() => {
		const s = getIpSettings('smtp');
		void smtpSaver.syncVersion;
		smtpAllow = [...(s.allowAddresses ?? [])];
		smtpDeny = [...(s.denyAddresses ?? [])];
		smtpBoth = s.allowIfInBothLists ?? false;
	});

	function getLocalState(proto: Protocol) {
		switch (proto) {
			case 'http':
				return { allow: httpAllow, deny: httpDeny, both: httpBoth };
			case 'nfs':
				return { allow: nfsAllow, deny: nfsDeny, both: nfsBoth };
			case 'cifs':
				return { allow: cifsAllow, deny: cifsDeny, both: cifsBoth };
			case 'smtp':
				return { allow: smtpAllow, deny: smtpDeny, both: smtpBoth };
		}
	}

	function arraysEqual(a: string[], b: string[]): boolean {
		if (a.length !== b.length) return false;
		return a.every((v, i) => v === b[i]);
	}

	function isDirty(proto: Protocol): boolean {
		const local = getLocalState(proto);
		const server = getIpSettings(proto);
		return (
			!arraysEqual(local.allow, server.allowAddresses ?? []) ||
			!arraysEqual(local.deny, server.denyAddresses ?? []) ||
			local.both !== (server.allowIfInBothLists ?? false)
		);
	}

	function ruleCount(proto: Protocol): number {
		const s = getIpSettings(proto);
		return (s.allowAddresses?.length ?? 0) + (s.denyAddresses?.length ?? 0);
	}

	let httpDirty = $derived(isDirty('http'));
	let nfsDirty = $derived(isDirty('nfs'));
	let cifsDirty = $derived(isDirty('cifs'));
	let smtpDirty = $derived(isDirty('smtp'));

	function getDirty(proto: Protocol): boolean {
		switch (proto) {
			case 'http':
				return httpDirty;
			case 'nfs':
				return nfsDirty;
			case 'cifs':
				return cifsDirty;
			case 'smtp':
				return smtpDirty;
		}
	}
</script>

{#await Promise.all([httpData, nfsData, cifsData, smtpData])}
	<CardSkeleton />
{:then}
	<Card.Root>
		<Card.Header>
			<Card.Title>Network Restrictions</Card.Title>
			<Card.Description>
				IP address allow and deny lists per protocol. Each protocol has its own independent
				restrictions.
			</Card.Description>
		</Card.Header>
		<Card.Content>
			<Tabs.Root bind:value={activeProtocol}>
				<Tabs.List>
					{#each PROTOCOLS as proto (proto)}
						{@const count = ruleCount(proto)}
						<Tabs.Trigger value={proto}>
							{PROTOCOL_LABELS[proto]}
							{#if count > 0}
								<Badge variant="secondary" class="ml-1.5 h-5 px-1.5 text-xs">
									{count}
								</Badge>
							{/if}
						</Tabs.Trigger>
					{/each}
				</Tabs.List>

				{#each PROTOCOLS as proto (proto)}
					<Tabs.Content value={proto} class="space-y-6 pt-4">
						<p class="text-sm text-muted-foreground">
							{PROTOCOL_DESCRIPTIONS[proto]}
						</p>

						{#if proto === 'http'}
							<IpListEditor
								bind:addresses={httpAllow}
								label="Allow List"
								emptyText="No allow list configured. All addresses are allowed by default."
							/>
							<IpListEditor
								bind:addresses={httpDeny}
								label="Deny List"
								placeholder="IP address or CIDR (e.g. 192.168.1.0/24)"
								variant="destructive"
								emptyText="No deny list configured."
							/>
							<div class="flex items-center gap-2">
								<Switch id="http-allow-if-both" bind:checked={httpBoth} />
								<Label for="http-allow-if-both" class="text-sm">Allow if in both lists</Label>
							</div>
						{:else if proto === 'nfs'}
							<IpListEditor
								bind:addresses={nfsAllow}
								label="Allow List"
								emptyText="No allow list configured. All addresses are allowed by default."
							/>
							<IpListEditor
								bind:addresses={nfsDeny}
								label="Deny List"
								placeholder="IP address or CIDR (e.g. 192.168.1.0/24)"
								variant="destructive"
								emptyText="No deny list configured."
							/>
							<div class="flex items-center gap-2">
								<Switch id="nfs-allow-if-both" bind:checked={nfsBoth} />
								<Label for="nfs-allow-if-both" class="text-sm">Allow if in both lists</Label>
							</div>
						{:else if proto === 'cifs'}
							<IpListEditor
								bind:addresses={cifsAllow}
								label="Allow List"
								emptyText="No allow list configured. All addresses are allowed by default."
							/>
							<IpListEditor
								bind:addresses={cifsDeny}
								label="Deny List"
								placeholder="IP address or CIDR (e.g. 192.168.1.0/24)"
								variant="destructive"
								emptyText="No deny list configured."
							/>
							<div class="flex items-center gap-2">
								<Switch id="cifs-allow-if-both" bind:checked={cifsBoth} />
								<Label for="cifs-allow-if-both" class="text-sm">Allow if in both lists</Label>
							</div>
						{:else if proto === 'smtp'}
							<IpListEditor
								bind:addresses={smtpAllow}
								label="Allow List"
								emptyText="No allow list configured. All addresses are allowed by default."
							/>
							<IpListEditor
								bind:addresses={smtpDeny}
								label="Deny List"
								placeholder="IP address or CIDR (e.g. 192.168.1.0/24)"
								variant="destructive"
								emptyText="No deny list configured."
							/>
							<div class="flex items-center gap-2">
								<Switch id="smtp-allow-if-both" bind:checked={smtpBoth} />
								<Label for="smtp-allow-if-both" class="text-sm">Allow if in both lists</Label>
							</div>
						{/if}

						<p class="text-xs text-muted-foreground">
							When "Allow if in both lists" is enabled, addresses that appear in both allow and deny
							lists will be allowed.
						</p>
					</Tabs.Content>
				{/each}
			</Tabs.Root>
		</Card.Content>
		<Card.Footer>
			<SaveButton
				dirty={getDirty(activeProtocol)}
				saving={getSaver(activeProtocol).saving}
				onclick={() => {
					const proto = activeProtocol;
					const saver = getSaver(proto);
					const local = getLocalState(proto);
					const qd = getQueryData(proto);
					saver.run(async () => {
						if (!qd) return;
						await update_ns_protocol({
							tenant,
							name: namespaceName,
							protocol: proto,
							body: {
								ipSettings: {
									allowAddresses: local.allow.filter(Boolean),
									denyAddresses: local.deny.filter(Boolean),
									allowIfInBothLists: local.both,
								},
							},
						}).updates(qd);
					});
				}}
			/>
		</Card.Footer>
	</Card.Root>
{/await}
