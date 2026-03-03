import type { PageServerLoad } from "./$types.js";
import { BACKEND_URL } from "$lib/server/env.js";

async function fetchHealth() {
  try {
    const res = await fetch(`${BACKEND_URL}/health`);
    if (res.ok) return await res.json();
  } catch {
    // ignore
  }
  return { status: "unknown" };
}

async function fetchBuckets(token: string) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/buckets`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      return { buckets: data.buckets ?? [], owner: data.owner ?? "" };
    }
  } catch {
    // ignore
  }
  return { buckets: [], owner: "" };
}

export const load: PageServerLoad = ({ locals }) => {
  return {
    health: fetchHealth(),
    buckets: fetchBuckets(locals.token),
  };
};
