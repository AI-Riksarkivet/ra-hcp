import { error } from '@sveltejs/kit';
import type { LayoutServerLoad } from './$types.js';

function parseJwtPayload(token: string): Record<string, unknown> {
	try {
		const payload = token.split('.')[1];
		const decoded = Buffer.from(payload, 'base64url').toString('utf-8');
		return JSON.parse(decoded);
	} catch {
		return {};
	}
}

export const load: LayoutServerLoad = async ({ locals }) => {
	if (!locals.token) {
		error(401, 'Not authenticated');
	}
	const claims = parseJwtPayload(locals.token);
	const username = (claims.sub as string) ?? 'User';
	return { authenticated: true, username };
};
