import { getRequestEvent } from "$app/server";
import { error } from "@sveltejs/kit";
import { BACKEND_URL } from "$lib/server/env.js";

export async function apiFetch(
  path: string,
  init?: RequestInit,
): Promise<Response> {
  const event = getRequestEvent();
  const token = event.locals.token;
  const headers = new Headers(init?.headers);
  if (token) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  const url = `${BACKEND_URL}${path}`;
  try {
    const res = await fetch(url, { ...init, headers });
    if (!res.ok) {
      console.warn(
        `[apiFetch] ${init?.method ?? "GET"} ${url} → ${res.status}`,
      );
    }
    return res;
  } catch (err) {
    const msg = err instanceof Error ? err.message : "unknown error";
    console.error(`[apiFetch] ${init?.method ?? "GET"} ${url} failed: ${msg}`);
    throw err;
  }
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
    error(res.status, detail);
  }
}
