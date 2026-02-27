import type { PageServerLoad } from './$types.js';

export const load: PageServerLoad = async ({ cookies }) => {
	cookies.delete('hcp_token', { path: '/' });
	return { loggedOut: true };
};
