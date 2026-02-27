import type { PageServerLoad } from './$types.js';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

export const load: PageServerLoad = async ({ locals }) => {
	const headers = { Authorization: `Bearer ${locals.token}` };

	const [usersRes, groupsRes] = await Promise.allSettled([
		fetch(`${BACKEND_URL}/api/v1/mapi/userAccounts`, { headers }),
		fetch(`${BACKEND_URL}/api/v1/mapi/groupAccounts`, { headers })
	]);

	const usersData =
		usersRes.status === 'fulfilled' && usersRes.value.ok
			? await usersRes.value.json()
			: [];

	const groupsData =
		groupsRes.status === 'fulfilled' && groupsRes.value.ok
			? await groupsRes.value.json()
			: [];

	const users = Array.isArray(usersData) ? usersData : usersData.userAccounts ?? [];
	const groups = Array.isArray(groupsData) ? groupsData : groupsData.groupAccounts ?? [];

	return { users, groups };
};
