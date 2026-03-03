import type { PageServerLoad } from "./$types.js";
import process from "node:process";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8000";

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
