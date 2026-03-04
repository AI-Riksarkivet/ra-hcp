import { fail } from "@sveltejs/kit";
import { loginSchema } from "$lib/api/schemas.js";
import type { Actions, PageServerLoad } from "./$types.js";
import { BACKEND_URL, COOKIE_SECURE } from "$lib/server/env.js";

export const load: PageServerLoad = ({ locals }) => {
  return { hasToken: !!locals.token };
};

export const actions = {
  default: async ({ request, cookies }) => {
    const formData = await request.formData();
    const data = {
      tenant: (formData.get("tenant") as string) || undefined,
      username: formData.get("username") as string,
      password: formData.get("password") as string,
    };

    const result = loginSchema.safeParse(data);
    if (!result.success) {
      const firstError = result.error.issues[0];
      return fail(400, { error: firstError.message });
    }

    try {
      const body = new URLSearchParams({
        grant_type: "password",
        username: result.data.username,
        password: result.data.password,
      });
      if (result.data.tenant) {
        body.set("tenant", result.data.tenant);
      }

      const response = await fetch(`${BACKEND_URL}/api/v1/auth/token`, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body,
      });

      if (!response.ok) {
        const error = await response.json().catch(() => ({
          detail: "Authentication failed",
        }));
        return fail(401, {
          error: error.detail ?? "Invalid username or password",
        });
      }

      const tokenData = await response.json();

      cookies.set("hcp_token", tokenData.access_token, {
        path: "/",
        httpOnly: true,
        sameSite: "lax",
        secure: COOKIE_SECURE,
        maxAge: 60 * 60 * 8, // 8 hours
      });
    } catch (err) {
      console.error("Login fetch failed:", err);
      return fail(500, {
        error: `Unable to connect to backend service (${BACKEND_URL})`,
      });
    }

    return { success: true };
  },
} satisfies Actions;
