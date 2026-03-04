import { z } from "zod";
import { command, query } from "$app/server";
import { apiFetch } from "$lib/server/api.js";

export interface Namespace {
  name: string;
  description?: string;
  hardQuota?: string;
  softQuota?: string;
  hashScheme?: string;
  searchEnabled?: boolean;
  versioningSettings?: { enabled: boolean };
}

export interface NsProtocols {
  httpEnabled?: boolean;
  httpsEnabled?: boolean;
  cifsEnabled?: boolean;
  nfsEnabled?: boolean;
  smtpEnabled?: boolean;
}

export interface NsPermissions {
  readAllowed?: boolean;
  writeAllowed?: boolean;
  deleteAllowed?: boolean;
  purgeAllowed?: boolean;
  searchAllowed?: boolean;
  readAclAllowed?: boolean;
  writeAclAllowed?: boolean;
}

export const get_namespaces = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    try {
      const res = await apiFetch(`/api/v1/mapi/tenants/${tenant}/namespaces`);
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
            } catch (err) {
              console.error("[namespaces.remote]", err);
            }
            return { name: n } as Namespace;
          }),
        );
        return details;
      }
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return [] as Namespace[];
  },
);

export const create_namespace = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    description: z.string().optional(),
    hardQuota: z.string().optional(),
    softQuota: z.number().optional(),
    hashScheme: z.string().optional(),
    searchEnabled: z.boolean().optional(),
    versioningEnabled: z.boolean().optional(),
  }),
  async ({ tenant, ...body }) => {
    const payload: Record<string, unknown> = { name: body.name };
    if (body.description) payload.description = body.description;
    if (body.hardQuota) payload.hardQuota = body.hardQuota;
    if (body.softQuota != null) payload.softQuota = body.softQuota;
    if (body.hashScheme) payload.hashScheme = body.hashScheme;
    if (body.searchEnabled != null) payload.searchEnabled = body.searchEnabled;
    if (body.versioningEnabled != null) {
      payload.versioningSettings = { enabled: body.versioningEnabled };
    }
    const res = await apiFetch(`/api/v1/mapi/tenants/${tenant}/namespaces`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to create namespace",
      }));
      throw new Error(err.detail);
    }
  },
);

export const get_namespace = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${encodeURIComponent(name)}`,
      );
      if (res.ok) return (await res.json()) as Namespace;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return null;
  },
);

export const get_ns_protocols = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/protocols`,
      );
      if (res.ok) return (await res.json()) as NsProtocols;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return {} as NsProtocols;
  },
);

export const update_ns_protocol = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    protocol: z.enum(["http", "cifs", "nfs", "smtp"]),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, name, protocol, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/protocols/${protocol}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: `Failed to update ${protocol} protocol`,
      }));
      throw new Error(err.detail);
    }
  },
);

export const get_ns_permissions = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/permissions`,
      );
      if (res.ok) return (await res.json()) as NsPermissions;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return {} as NsPermissions;
  },
);

export const update_ns_permissions = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, name, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/permissions`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update permissions",
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
