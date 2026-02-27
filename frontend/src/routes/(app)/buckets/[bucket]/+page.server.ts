import type { PageServerLoad } from './$types.js';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

export const load: PageServerLoad = async ({ params, locals, url }) => {
	const prefix = url.searchParams.get('prefix') ?? '';
	const queryParams = new URLSearchParams({ max_keys: '100' });
	if (prefix) queryParams.set('prefix', prefix);

	const response = await fetch(
		`${BACKEND_URL}/api/v1/buckets/${encodeURIComponent(params.bucket)}/objects?${queryParams}`,
		{ headers: { Authorization: `Bearer ${locals.token}` } }
	);

	if (!response.ok) {
		return { bucket: params.bucket, objects: [], prefix, error: 'Failed to load objects' };
	}

	const data = await response.json();
	return {
		bucket: params.bucket,
		objects: data.objects ?? [],
		prefix,
		isTruncated: data.is_truncated ?? false,
		nextToken: data.next_continuation_token ?? null,
		keyCount: data.key_count ?? 0
	};
};
