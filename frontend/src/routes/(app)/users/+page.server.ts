import type { PageServerLoad } from "./$types.js";
import { BACKEND_URL } from "$lib/server/env.js";

async function fetchUsers(token: string) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/mapi/userAccounts`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : data.userAccounts ?? [];
    }
  } catch {
    // ignore
  }
  return [];
}

async function fetchGroups(token: string) {
  try {
    const res = await fetch(`${BACKEND_URL}/api/v1/mapi/groupAccounts`, {
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      const data = await res.json();
      return Array.isArray(data) ? data : data.groupAccounts ?? [];
    }
  } catch {
    // ignore
  }
  return [];
}

export const load: PageServerLoad = ({ locals }) => {
  return {
    users: fetchUsers(locals.token!),
    groups: fetchGroups(locals.token!),
  };
};
