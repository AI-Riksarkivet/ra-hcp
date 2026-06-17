// App-global bulk delete for items without a server-side batch endpoint
// (buckets, namespaces — each is its own MAPI/S3 admin call).
//
// Runs the per-item deletes from module scope with bounded concurrency, so the
// progress tray + completion toast survive navigation and the items delete in
// parallel instead of one slow serial loop. Mirrors delete-progress.svelte.ts
// (which covers the server-side object-delete task).
import { toast } from 'svelte-sonner';

import { getErrorMessage } from '$lib/utils/get-error-message.js';

// Bounded so we don't open hundreds of admin requests at once; force-deletes
// can be heavy server-side.
const CONCURRENCY = 6;

let running = $state(false);
let entity = $state('item');
let total = $state(0);
let done = $state(0);
let failed = $state(0);
let canceled = false;

/** Reactive view of the running bulk delete (read in the global tray). */
export const bulkDeleteProgress = {
	get running() {
		return running;
	},
	get entity() {
		return entity;
	},
	get total() {
		return total;
	},
	get done() {
		return done;
	},
	get failed() {
		return failed;
	},
	get percent() {
		return total > 0 ? Math.round((100 * done) / total) : 0;
	}
};

/** Request cancellation — in-flight deletes finish, queued ones are skipped. */
export function cancelBulkDelete() {
	canceled = true;
}

function plural(name: string, n: number): string {
	return `${name}${n !== 1 ? 's' : ''}`;
}

/**
 * Delete every name in `names` by calling `deleteOne`, with bounded concurrency.
 * Refreshes the relevant list once via `onDone` (callers must NOT refresh per
 * item). Returns when all workers drain.
 */
export async function startBulkDelete(
	entityName: string,
	names: string[],
	deleteOne: (name: string) => Promise<unknown>,
	onDone?: () => void
): Promise<void> {
	if (running) {
		toast.error('A bulk delete is already running — wait for it to finish or cancel it');
		return;
	}
	if (names.length === 0) return;

	running = true;
	entity = entityName;
	total = names.length;
	done = 0;
	failed = 0;
	canceled = false;
	const errors: string[] = [];

	let next = 0;
	async function worker(): Promise<void> {
		// `next++` is synchronous between awaits, so workers never claim the same
		// index (JS is single-threaded).
		while (!canceled) {
			const i = next++;
			if (i >= names.length) return;
			try {
				await deleteOne(names[i]);
			} catch (err) {
				failed++;
				if (errors.length < 5) errors.push(`${names[i]}: ${getErrorMessage(err, 'failed')}`);
			} finally {
				done++;
			}
		}
	}

	await Promise.all(Array.from({ length: Math.min(CONCURRENCY, names.length) }, worker));

	running = false;
	onDone?.();

	const succeeded = done - failed;
	if (canceled) {
		toast.info(`Canceled — deleted ${succeeded} ${plural(entity, succeeded)}`);
	} else if (failed > 0) {
		toast.error(
			`Deleted ${succeeded} ${plural(entity, succeeded)}, ${failed} failed\n${errors.join('\n')}`
		);
	} else {
		toast.success(`Deleted ${succeeded} ${plural(entity, succeeded)}`);
	}
}
