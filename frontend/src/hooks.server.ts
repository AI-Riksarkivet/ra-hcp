import type { Handle, HandleServerError } from "@sveltejs/kit";
import { enumerateSessions } from "$lib/server/sessions.js";
import { BACKEND_URL } from "$lib/server/env.js";

console.info(`[frontend] started — BACKEND_URL=${BACKEND_URL}`);

export const handle: Handle = ({ event, resolve }) => {
  // Fix URL protocol for TLS-terminating proxies (nginx ingress).
  // Deno sees http:// but browser sends Origin: https://.
  // SvelteKit's CSRF check compares request Origin header against event.url.origin.
  // We must make them match.
  const proto = event.request.headers.get("x-forwarded-proto");
  const origin = event.request.headers.get("origin");
  if (proto === "https" && event.url.protocol === "http:") {
    // Try multiple approaches since Deno may restrict some
    try {
      const fixed = new URL(event.url.href);
      fixed.protocol = "https:";
      Object.defineProperty(event, "url", { value: fixed, configurable: true, writable: true });
    } catch {
      // Object.defineProperty failed — frozen object
    }

    // If url is still http, the CSRF check will fail on POST.
    // Log it so we can see what's happening.
    if (event.url.protocol === "http:" && event.request.method === "POST") {
      console.warn(
        `[CSRF] Origin mismatch: request=${origin} url=${event.url.origin} proto=${proto} method=${event.request.method} path=${event.url.pathname}`,
      );
    }
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
