import type { RequestHandler } from './$types.js';

const BACKEND_URL = process.env.BACKEND_URL ?? 'http://localhost:8000';

const handler: RequestHandler = async ({ params, request, locals }) => {
	const url = new URL(request.url);
	const target = `${BACKEND_URL}/api/${params.path}${url.search}`;

	const headers = new Headers();
	const contentType = request.headers.get('content-type');
	if (contentType) {
		headers.set('content-type', contentType);
	}
	if (locals.token) {
		headers.set('authorization', `Bearer ${locals.token}`);
	}

	const response = await fetch(target, {
		method: request.method,
		headers,
		body: request.method !== 'GET' && request.method !== 'HEAD' ? request.body : undefined,
		// @ts-expect-error duplex is needed for streaming request bodies
		duplex: 'half'
	});

	return new Response(response.body, {
		status: response.status,
		statusText: response.statusText,
		headers: {
			'content-type': response.headers.get('content-type') ?? 'application/json'
		}
	});
};

export const GET = handler;
export const POST = handler;
export const PUT = handler;
export const DELETE = handler;
export const HEAD = handler;
export const PATCH = handler;
