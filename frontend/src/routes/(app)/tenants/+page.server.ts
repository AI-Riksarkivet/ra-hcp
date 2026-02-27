import type { PageServerLoad } from './$types.js';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

export const load: PageServerLoad = async ({ locals }) => {
	const response = await fetch(`${BACKEND_URL}/api/v1/mapi/tenants`, {
		headers: { Authorization: `Bearer ${locals.token}` }
	});

	if (!response.ok) {
		return { tenants: [] };
	}

	const data = await response.json();
	return { tenants: Array.isArray(data) ? data : data.tenants ?? [] };
};
