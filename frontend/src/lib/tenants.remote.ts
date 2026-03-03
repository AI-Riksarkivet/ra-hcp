import { query } from "$app/server";
import { z } from "zod";
import { apiFetch } from "$lib/server/api.js";

export const get_tenants = query(async () => {
  try {
    const res = await apiFetch("/api/v1/mapi/tenants");
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : data.tenants ?? [];
    }
  } catch {
    // ignore
  }
  return [];
});

export const get_tenant = query(
  z.object({ name: z.string() }),
  async ({ name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${encodeURIComponent(name)}`,
      );
      if (res.ok) return await res.json();
    } catch {
      // ignore
    }
    return { name };
  },
);

export const get_namespaces = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${encodeURIComponent(tenant)}/namespaces`,
      );
      if (res.ok) {
        const data = await res.json();
        return Array.isArray(data) ? data : data.namespaces ?? [];
      }
    } catch {
      // ignore
    }
    return [];
  },
);
