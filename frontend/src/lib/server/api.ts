import { getRequestEvent } from "$app/server";
import { BACKEND_URL } from "$lib/server/env.js";

export function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const event = getRequestEvent();
  const token = event.locals.token;
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return fetch(`${BACKEND_URL}${path}`, { ...init, headers });
}

export async function throwIfNotOk(
  res: Response,
  fallback: string,
): Promise<void> {
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: fallback }));
    const detail = typeof err.detail === "string"
      ? err.detail
      : JSON.stringify(err.detail);
    throw new Error(detail);
  }
}
