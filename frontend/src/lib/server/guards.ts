import { redirect } from "@sveltejs/kit";
import type { AccessLevel } from "$lib/constants.js";

export function requireAdmin(accessLevel: AccessLevel) {
  if (accessLevel === "namespace-user") {
    redirect(302, "/buckets");
  }
}
