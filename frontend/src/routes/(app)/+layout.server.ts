import { redirect } from "@sveltejs/kit";
import type { LayoutServerLoad } from "./$types.js";
import { Buffer } from "node:buffer";
import { BACKEND_URL } from "$lib/server/env.js";

function parseJwtPayload(token: string): Record<string, unknown> {
  try {
    const payload = token.split(".")[1];
    const decoded = Buffer.from(payload, "base64url").toString("utf-8");
    return JSON.parse(decoded);
  } catch {
    return {};
  }
}

async function fetchUserGUID(
  token: string,
  tenant: string,
  username: string,
): Promise<string | undefined> {
  try {
    const res = await fetch(
      `${BACKEND_URL}/api/v1/mapi/tenants/${tenant}/userAccounts/${
        encodeURIComponent(username)
      }?verbose=true`,
      { headers: { Authorization: `Bearer ${token}` } },
    );
    if (res.ok) {
      const data = await res.json();
      return data.userGUID as string | undefined;
    }
  } catch {
    // Non-critical — header will just hide the ID
  }
  return undefined;
}

export const load: LayoutServerLoad = async ({ locals }) => {
  if (!locals.token) {
    redirect(302, "/login");
  }
  const claims = parseJwtPayload(locals.token);
  const username = (claims.sub as string) ?? "User";
  const tenant = claims.tenant as string | undefined;
  const userGUID = tenant
    ? await fetchUserGUID(locals.token, tenant, username)
    : undefined;
  return {
    authenticated: true,
    username,
    tenant,
    userGUID,
  };
};
