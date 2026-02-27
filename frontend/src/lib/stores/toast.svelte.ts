export interface Toast {
	id: string;
	type: 'success' | 'error' | 'info';
	message: string;
}

let toasts = $state<Toast[]>([]);
let counter = 0;

export function addToast(type: Toast['type'], message: string, duration = 4000) {
	const id = `toast-${++counter}`;
	toasts = [...toasts, { id, type, message }];
	setTimeout(() => removeToast(id), duration);
}

export function removeToast(id: string) {
	toasts = toasts.filter((t) => t.id !== id);
}

export function getToasts(): Toast[] {
	return toasts;
}

export const toast = {
	success: (msg: string) => addToast('success', msg),
	error: (msg: string) => addToast('error', msg),
	info: (msg: string) => addToast('info', msg)
};
