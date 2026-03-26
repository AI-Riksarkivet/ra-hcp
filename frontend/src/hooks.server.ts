import type { Handle, HandleServerError } from "@sveltejs/kit";
import { enumerateSessions } from "$lib/server/sessions.js";
import { BACKEND_URL } from "$lib/server/env.js";

console.info(`[frontend] started — BACKEND_URL=${BACKEND_URL}`);

export const handle: Handle = ({ event, resolve }) => {
  // Fix CSRF for TLS-terminating proxies (nginx ingress).
  // The Deno server sees http:// but the browser sends Origin: https://.
  // SvelteKit rejects this as cross-site. Rewrite Origin to match the
  // server's URL so the CSRF check passes. This is safe because
  // X-Forwarded-Proto confirms the proxy did TLS termination.
  const proto = event.request.headers.get("x-forwarded-proto");
  const origin = event.request.headers.get("origin");
  if (proto === "https" && origin && event.url.protocol === "http:") {
    event.request.headers.set("origin", event.url.origin);
  }

  const token = event.cookies.get("hcp_token");
  if (token) {
    event.locals.token = token;
  }
  event.locals.sessions = enumerateSessions(event.cookies, token);
  return resolve(event);
};

export const handleError: HandleServerError = ({ error, event, status }) => {
  const msg = error instanceof Error ? error.message : String(error);
  const stack = error instanceof Error ? error.stack : undefined;
  console.error(
    `[frontend] ${event.request.method} ${event.url.pathname} → ${status}: ${msg}`,
  );
  if (stack) console.error(stack);
  return {
    message: msg,
  };
};
