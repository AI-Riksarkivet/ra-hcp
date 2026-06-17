// App-global background-delete progress.
//
// The delete runs server-side as a task; this store starts it and polls it from
// module scope (not a component), so the progress bar + completion toast survive
// navigating between pages. A page registers a refresh callback while mounted so
// its object list refreshes when the delete finishes.
import { toast } from 'svelte-sonner';

import {
	cancel_delete_task,
	get_delete_task,
	start_delete_task
} from '$lib/remote/buckets.remote';

let running = $state(false);
let canceling = $state(false);
let bucket = $state('');
let taskId = $state<string | null>(null);
let total = $state(0);
let deleted = $state(0);
let failed = $state(0);

let timer: ReturnType<typeof setInterval> | undefined;
let refreshCb: (() => void) | null = null;

/** Reactive view of the running delete (read in the global tray). */
export const deleteProgress = {
	get running() {
		return running;
	},
	get canceling() {
		return canceling;
	},
	get total() {
		return total;
	},
	get deleted() {
		return deleted;
	},
	get failed() {
		return failed;
	},
	get percent() {
		return total > 0 ? Math.round((100 * deleted) / total) : 0;
	}
};

/** Register (or clear with null) a callback fired when a delete completes. */
export function onDeleteComplete(cb: (() => void) | null) {
	refreshCb = cb;
}

function stop() {
	if (timer) clearInterval(timer);
	timer = undefined;
}

function poll() {
	stop();
	const tid = taskId;
	const bkt = bucket;
	if (!tid) return;
	timer = setInterval(async () => {
		try {
			const st = await get_delete_task({ bucket: bkt, task_id: tid });
			total = st.total;
			deleted = st.deleted;
			failed = st.failed;
			if (st.status === 'done' || st.status === 'canceled') {
				stop();
				running = false;
				canceling = false;
				taskId = null;
				refreshCb?.();
				// The backend is eventually consistent right after a delete, so the
				// first re-list can still show a just-deleted folder. Re-list once
				// more shortly after — the backend serves listings uncached during
				// its post-delete window, so this picks up the converged state
				// without the user having to refresh.
				setTimeout(() => refreshCb?.(), 2500);
				if (st.status === 'canceled') {
					toast.info(`Delete canceled — ${st.deleted.toLocaleString()} objects removed`);
				} else if (st.failed > 0) {
					toast.warning(
						`Deleted ${st.deleted.toLocaleString()} objects, ${st.failed.toLocaleString()} failed`
					);
				} else {
					toast.success(`Deleted ${st.deleted.toLocaleString()} objects`);
				}
			}
		} catch (err) {
			stop();
			running = false;
			canceling = false;
			taskId = null;
			toast.error(err instanceof Error ? err.message : 'Delete failed');
		}
	}, 1500);
}

/** Start a background delete of whole folders (prefixes) and/or explicit keys. */
export async function startDelete(b: string, prefixes: string[], keys: string[]) {
	if (running) {
		toast.error('A delete is already running — wait for it to finish or cancel it');
		return;
	}
	bucket = b;
	total = 0;
	deleted = 0;
	failed = 0;
	canceling = false;
	running = true;
	try {
		const { task_id } = await start_delete_task({ bucket: b, prefixes, keys });
		taskId = task_id;
		toast.info('Deleting in the background…');
		poll();
	} catch (err) {
		running = false;
		toast.error(err instanceof Error ? err.message : 'Failed to start delete');
	}
}

/** Request cancellation of the running delete (best-effort; server stops it). */
export async function cancelDelete() {
	if (!taskId || canceling) return;
	canceling = true;
	try {
		await cancel_delete_task({ bucket, task_id: taskId });
	} catch (err) {
		canceling = false;
		toast.error(err instanceof Error ? err.message : 'Failed to cancel');
	}
}
