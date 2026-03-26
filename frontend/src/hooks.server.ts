import type { Handle, HandleServerError } from "@sveltejs/kit";
import { enumerateSessions } from "$lib/server/sessions.js";
import { BACKEND_URL } from "$lib/server/env.js";

console.info(`[frontend] started — BACKEND_URL=${BACKEND_URL}`);

export const handle: Handle = ({ event, resolve }) => {
  // Fix URL protocol for TLS-terminating proxies (nginx ingress).
  // Deno sees http:// but browser sends Origin: https://.
  // Override event.url so SvelteKit's CSRF check sees the correct origin.
  const proto = event.request.headers.get("x-forwarded-proto");
  if (proto === "https" && event.url.protocol === "http:") {
    const fixed = new URL(event.url.href);
    fixed.protocol = "https:";
    Object.defineProperty(event, "url", { value: fixed, configurable: true });
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
