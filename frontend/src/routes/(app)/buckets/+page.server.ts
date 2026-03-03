import { fail } from "@sveltejs/kit";
import { createBucketSchema } from "$lib/api/schemas.js";
import type { Actions, PageServerLoad } from "./$types.js";
import { BACKEND_URL } from "$lib/server/env.js";

async function fetchBuckets(token: string) {
  const response = await fetch(`${BACKEND_URL}/api/v1/buckets`, {
    headers: { Authorization: `Bearer ${token}` },
  });

  if (!response.ok) {
    return { buckets: [], owner: "" };
  }

  const data = await response.json();
  // Backend may return PascalCase (Name, CreationDate) — normalize
  const buckets = (data.buckets ?? []).map((b: Record<string, unknown>) => ({
    name: b.name ?? b.Name ?? "",
    creation_date: b.creation_date ?? b.CreationDate ?? "",
  }));
  return { buckets, owner: data.owner ?? "" };
}

export const load: PageServerLoad = ({ locals }) => {
  return {
    bucketData: fetchBuckets(locals.token!),
  };
};

export const actions = {
  create: async ({ request, locals }) => {
    const formData = await request.formData();
    const data = { bucket: formData.get("bucket") as string };

    const result = createBucketSchema.safeParse(data);
    if (!result.success) {
      return fail(400, { error: result.error.issues[0].message });
    }

    const response = await fetch(`${BACKEND_URL}/api/v1/buckets`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${locals.token}`,
      },
      body: JSON.stringify({ bucket: result.data.bucket }),
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: "Failed to create bucket",
      }));
      return fail(response.status, { error: error.detail });
    }

    return { success: true };
  },

  delete: async ({ request, locals }) => {
    const formData = await request.formData();
    const bucket = formData.get("bucket") as string;

    if (!bucket) {
      return fail(400, { error: "Bucket name is required" });
    }

    const response = await fetch(
      `${BACKEND_URL}/api/v1/buckets/${encodeURIComponent(bucket)}`,
      {
        method: "DELETE",
        headers: { Authorization: `Bearer ${locals.token}` },
      },
    );

    if (!response.ok) {
      const error = await response.json().catch(() => ({
        detail: "Failed to delete bucket",
      }));
      return fail(response.status, { error: error.detail });
    }

    return { success: true };
  },
} satisfies Actions;
