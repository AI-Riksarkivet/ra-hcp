import { z } from "zod";
import { query } from "$app/server";
import { apiFetch } from "$lib/server/api.js";

export const get_users = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    try {
      const res = await apiFetch(`/api/v1/mapi/tenants/${tenant}/userAccounts`);
      if (res.ok) {
        const data = await res.json();
        return Array.isArray(data) ? data : data.userAccounts ?? [];
      }
    } catch {
      // ignore
    }
    return [];
  },
);

export const get_groups = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/groupAccounts`,
      );
      if (res.ok) {
        const data = await res.json();
        return Array.isArray(data) ? data : data.groupAccounts ?? [];
      }
    } catch {
      // ignore
    }
    return [];
  },
);
