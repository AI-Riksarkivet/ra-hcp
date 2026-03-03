import { z } from "zod";
import { command, query } from "$app/server";
import { apiFetch } from "$lib/server/api.js";

export interface Namespace {
  name: string;
  description?: string;
  hardQuota?: string;
  softQuota?: string;
  hashScheme?: string;
}

export const get_namespaces = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces`,
      );
      if (res.ok) {
        const data = await res.json();
        const names: string[] = data.name ?? [];

        const details = await Promise.all(
          names.map(async (n) => {
            try {
              const r = await apiFetch(
                `/api/v1/mapi/tenants/${tenant}/namespaces/${
                  encodeURIComponent(n)
                }`,
              );
              if (r.ok) return (await r.json()) as Namespace;
            } catch {
              // ignore
            }
            return { name: n } as Namespace;
          }),
        );
        return details;
      }
    } catch {
      // ignore
    }
    return [] as Namespace[];
  },
);

export const create_namespace = command(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name }),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to create namespace",
      }));
      throw new Error(err.detail);
    }
  },
);

export const delete_namespace = command(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${encodeURIComponent(name)}`,
      { method: "DELETE" },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to delete namespace",
      }));
      throw new Error(err.detail);
    }
  },
);
