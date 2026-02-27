import type { PageServerLoad } from './$types.js';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

export const load: PageServerLoad = async ({ params, locals }) => {
	const headers = { Authorization: `Bearer ${locals.token}` };

	const [tenantRes, namespacesRes] = await Promise.allSettled([
		fetch(`${BACKEND_URL}/api/v1/mapi/tenants/${encodeURIComponent(params.tenant)}`, { headers }),
		fetch(
			`${BACKEND_URL}/api/v1/mapi/tenants/${encodeURIComponent(params.tenant)}/namespaces`,
			{ headers }
		)
	]);

	const tenant =
		tenantRes.status === 'fulfilled' && tenantRes.value.ok
			? await tenantRes.value.json()
			: { name: params.tenant };

	const namespacesData =
		namespacesRes.status === 'fulfilled' && namespacesRes.value.ok
			? await namespacesRes.value.json()
			: [];

	const namespaces = Array.isArray(namespacesData)
		? namespacesData
		: namespacesData.namespaces ?? [];

	return { tenant, namespaces };
};
