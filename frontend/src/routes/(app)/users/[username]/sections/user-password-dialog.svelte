<script lang="ts">
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Loader2 } from 'lucide-svelte';
	import { toast } from 'svelte-sonner';
	import { change_password } from '$lib/users.remote.js';

	let {
		tenant,
		username,
		open = $bindable(false),
	}: {
		tenant: string;
		username: string;
		open: boolean;
	} = $props();

	let newPassword = $state('');
	let confirmPassword = $state('');
	let changingPassword = $state(false);

	let passwordValid = $derived(newPassword.length > 0 && newPassword === confirmPassword);

	async function handleChangePassword() {
		if (!passwordValid) return;
		changingPassword = true;
		try {
			await change_password({ tenant, username, password: newPassword });
			toast.success('Password changed successfully');
			newPassword = '';
			confirmPassword = '';
			open = false;
		} catch {
			toast.error('Failed to change password');
		} finally {
			changingPassword = false;
		}
	}
</script>

<Dialog.Root bind:open>
	<Dialog.Content class="sm:max-w-md">
		<Dialog.Header>
			<Dialog.Title>Change Password</Dialog.Title>
			<Dialog.Description>Set a new password for "{username}".</Dialog.Description>
		</Dialog.Header>
		<div class="space-y-4">
			<div class="space-y-2">
				<Label for="new-password">New Password</Label>
				<Input
					id="new-password"
					type="password"
					bind:value={newPassword}
					placeholder="Enter new password"
				/>
			</div>
			<div class="space-y-2">
				<Label for="confirm-password">Confirm Password</Label>
				<Input
					id="confirm-password"
					type="password"
					bind:value={confirmPassword}
					placeholder="Confirm new password"
				/>
			</div>
			{#if newPassword.length > 0 && confirmPassword.length > 0 && newPassword !== confirmPassword}
				<p class="text-sm text-destructive">Passwords do not match.</p>
			{/if}
			<Dialog.Footer>
				<Button
					variant="ghost"
					type="button"
					onclick={() => {
						open = false;
						newPassword = '';
						confirmPassword = '';
					}}>Cancel</Button
				>
				<Button disabled={!passwordValid || changingPassword} onclick={handleChangePassword}>
					{#if changingPassword}
						<Loader2 class="h-4 w-4 animate-spin" />
						Changing...
					{:else}
						Change Password
					{/if}
				</Button>
			</Dialog.Footer>
		</div>
	</Dialog.Content>
</Dialog.Root>
