import type { PageServerLoad } from './$types.js';

export const load: PageServerLoad = async ({ locals }) => {
	return { hasToken: !!locals.token };
};
