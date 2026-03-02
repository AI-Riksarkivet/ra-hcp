import { fail } from '@sveltejs/kit';
import type { Actions, PageServerLoad } from './$types.js';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

async function fetchObjects(bucket: string, prefix: string, token: string) {
	const queryParams = new URLSearchParams({ max_keys: '100' });
	if (prefix) queryParams.set('prefix', prefix);

	const response = await fetch(
		`${BACKEND_URL}/api/v1/buckets/${encodeURIComponent(bucket)}/objects?${queryParams}`,
		{ headers: { Authorization: `Bearer ${token}` } }
	);

	if (!response.ok) {
		return { objects: [], isTruncated: false, keyCount: 0, nextToken: null };
	}

	const data = await response.json();
	// Normalize PascalCase (Key, Size, LastModified) to snake_case
	const objects = (data.objects ?? []).map((o: Record<string, unknown>) => ({
		key: o.key ?? o.Key ?? '',
		size: o.size ?? o.Size ?? 0,
		last_modified: o.last_modified ?? o.LastModified ?? '',
		etag: o.etag ?? o.ETag ?? '',
		storage_class: o.storage_class ?? o.StorageClass ?? ''
	}));
	return {
		objects,
		isTruncated: data.is_truncated ?? false,
		nextToken: data.next_continuation_token ?? null,
		keyCount: data.key_count ?? 0
	};
}

export const load: PageServerLoad = async ({ params, locals, url }) => {
	const prefix = url.searchParams.get('prefix') ?? '';

	return {
		bucket: params.bucket,
		prefix,
		objectData: fetchObjects(params.bucket, prefix, locals.token)
	};
};

export const actions = {
	upload: async ({ params, request, locals }) => {
		const formData = await request.formData();
		const file = formData.get('file') as File;

		if (!file || file.size === 0) {
			return fail(400, { error: 'Please select a file' });
		}

		const key = (formData.get('key') as string) || file.name;
		const uploadForm = new FormData();
		uploadForm.append('file', file);

		const response = await fetch(
			`${BACKEND_URL}/api/v1/buckets/${encodeURIComponent(params.bucket)}/objects/${encodeURIComponent(key)}`,
			{
				method: 'POST',
				headers: { Authorization: `Bearer ${locals.token}` },
				body: uploadForm
			}
		);

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: 'Upload failed' }));
			return fail(response.status, { error: error.detail });
		}

		return { success: true };
	},

	delete: async ({ params, request, locals }) => {
		const formData = await request.formData();
		const key = formData.get('key') as string;

		if (!key) {
			return fail(400, { error: 'Object key is required' });
		}

		const response = await fetch(
			`${BACKEND_URL}/api/v1/buckets/${encodeURIComponent(params.bucket)}/objects/${encodeURIComponent(key)}`,
			{
				method: 'DELETE',
				headers: { Authorization: `Bearer ${locals.token}` }
			}
		);

		if (!response.ok) {
			const error = await response.json().catch(() => ({ detail: 'Delete failed' }));
			return fail(response.status, { error: error.detail });
		}

		return { success: true };
	},

	bulkDelete: async ({ params, request, locals }) => {
		const formData = await request.formData();
		const keys = formData.getAll('keys') as string[];

		if (!keys.length) {
			return fail(400, { error: 'At least one object key is required' });
		}

		let failCount = 0;
		for (const key of keys) {
			const response = await fetch(
				`${BACKEND_URL}/api/v1/buckets/${encodeURIComponent(params.bucket)}/objects/${encodeURIComponent(key)}`,
				{
					method: 'DELETE',
					headers: { Authorization: `Bearer ${locals.token}` }
				}
			);
			if (!response.ok) failCount++;
		}

		if (failCount > 0) {
			return fail(500, { error: `Failed to delete ${failCount} of ${keys.length} objects` });
		}

		return { success: true };
	}
} satisfies Actions;
