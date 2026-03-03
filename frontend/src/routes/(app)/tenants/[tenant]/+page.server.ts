import type { PageServerLoad } from "./$types.js";
import { BACKEND_URL } from "$lib/server/env.js";

async function fetchTenant(name: string, token: string) {
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/mapi/tenants/${encodeURIComponent(name)}`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    if (res.ok) return await res.json();
  } catch {
    // ignore
  }
  return { name };
}

async function fetchNamespaces(tenant: string, token: string) {
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/mapi/tenants/${
        encodeURIComponent(tenant)
      }/namespaces`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : data.namespaces ?? [];
    }
  } catch {
    // ignore
  }
  return [];
}

export const load: PageServerLoad = ({ params, locals }) => {
  return {
    tenant: fetchTenant(params.tenant, locals.token),
    namespaces: fetchNamespaces(params.tenant, locals.token),
  };
};
