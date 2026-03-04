import type { PageServerLoad } from './$types.js';

export const load: PageServerLoad = ({ locals }) => {
	return { hasToken: !!locals.token };
};
