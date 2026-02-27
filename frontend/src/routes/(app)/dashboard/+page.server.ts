import type { PageServerLoad } from './$types.js';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = { Authorization: `Bearer ${locals.token}` };

	const [healthRes, bucketsRes] = await Promise.allSettled([
		fetch(`${BACKEND_URL}/health`),
		fetch(`${BACKEND_URL}/api/v1/buckets`, { headers })
	]);

	const health =
		healthRes.status === 'fulfilled' && healthRes.value.ok
			? await healthRes.value.json()
			: { status: 'unknown' };

	const buckets =
		bucketsRes.status === 'fulfilled' && bucketsRes.value.ok
			? await bucketsRes.value.json()
			: { buckets: [], owner: '' };

	return { health, buckets };
};
