import { query } from "$app/server";
import { BACKEND_URL } from "$lib/server/env.js";

export const get_health = query(async () => {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    if (res.ok) return await res.json();
  } catch {
    // ignore
  }
  return { status: "unknown" };
});
