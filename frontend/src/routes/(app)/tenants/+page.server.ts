import type { PageServerLoad } from "./$types.js";
import { BACKEND_URL } from "$lib/server/env.js";

async function fetchTenants(token: string) {
  const response = await fetch(`${BACKEND_URL}/api/v1/mapi/tenants`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    return [];
  }

  const data = await response.json();
  return Array.isArray(data) ? data : data.tenants ?? [];
}

export const load: PageServerLoad = ({ locals }) => {
  return {
    tenants: fetchTenants(locals.token),
  };
};
