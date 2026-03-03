import { query } from "$app/server";
import { apiFetch } from "$lib/server/api.js";

export const get_users = query(async () => {
  try {
    const res = await apiFetch("/api/v1/mapi/userAccounts");
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : data.userAccounts ?? [];
    }
  } catch {
    // ignore
  }
  return [];
});

export const get_groups = query(async () => {
  try {
    const res = await apiFetch("/api/v1/mapi/groupAccounts");
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : data.groupAccounts ?? [];
    }
  } catch {
    // ignore
  }
  return [];
});
