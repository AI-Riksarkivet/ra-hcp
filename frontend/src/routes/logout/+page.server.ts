import { redirect } from '@sveltejs/kit';
import type { PageServerLoad } from './$types.js';

export const load: PageServerLoad = ({ cookies }) => {
	cookies.delete('hcp_token', { path: '/' });
	redirect(302, '/login');
};
