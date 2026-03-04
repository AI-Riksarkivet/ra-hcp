import { z } from "zod";
import { command, query } from "$app/server";
import { apiFetch } from "$lib/server/api.js";

export const get_users = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    try {
      const res = await apiFetch(`/api/v1/mapi/tenants/${tenant}/userAccounts`);
      if (res.ok) {
        const data = await res.json();
        if (Array.isArray(data)) return data;
        if (Array.isArray(data.username)) {
          return data.username.map((u: string) => ({ username: u }));
        }
        return data.userAccounts ?? [];
      }
    } catch {
      // ignore
    }
    return [];
  },
);

export interface DataAccessPermissions {
  namespacePermission?: Array<{
    namespaceName: string;
    permissions?: { permission?: string[] };
  }>;
}

export const get_user_permissions = query(
  z.object({ tenant: z.string(), username: z.string() }),
  async ({ tenant, username }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/userAccounts/${
          encodeURIComponent(username)
        }/dataAccessPermissions`,
      );
      if (res.ok) return (await res.json()) as DataAccessPermissions;
    } catch {
      // ignore
    }
    return {} as DataAccessPermissions;
  },
);

export const set_user_permissions = command(
  z.object({
    tenant: z.string(),
    username: z.string(),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, username, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/userAccounts/${
        encodeURIComponent(username)
      }/dataAccessPermissions`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update user permissions",
      }));
      throw new Error(err.detail);
    }
  },
);

export const create_user = command(
  z.object({
    tenant: z.string(),
    username: z.string(),
    fullName: z.string().optional(),
    description: z.string().optional(),
    enabled: z.boolean().optional(),
    roles: z.array(z.string()).optional(),
  }),
  async ({ tenant, ...body }) => {
    const payload: Record<string, unknown> = { username: body.username };
    if (body.fullName) payload.fullName = body.fullName;
    if (body.description) payload.description = body.description;
    if (body.enabled != null) payload.enabled = body.enabled;
    if (body.roles) payload.roles = { role: body.roles };
    payload.localAuthentication = true;
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/userAccounts`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to create user",
      }));
      throw new Error(err.detail);
    }
  },
);

export const create_group = command(
  z.object({
    tenant: z.string(),
    groupname: z.string(),
    description: z.string().optional(),
    roles: z.array(z.string()).optional(),
  }),
  async ({ tenant, ...body }) => {
    const payload: Record<string, unknown> = { groupname: body.groupname };
    if (body.description) payload.description = body.description;
    if (body.roles) payload.roles = { role: body.roles };
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/groupAccounts`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to create group",
      }));
      throw new Error(err.detail);
    }
  },
);

export const get_user = query(
  z.object({ tenant: z.string(), username: z.string() }),
  async ({ tenant, username }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/userAccounts/${
          encodeURIComponent(username)
        }`,
      );
      if (res.ok) return await res.json();
    } catch {
      // ignore
    }
    return null;
  },
);

export const update_user = command(
  z.object({
    tenant: z.string(),
    username: z.string(),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, username, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/userAccounts/${
        encodeURIComponent(username)
      }`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update user",
      }));
      throw new Error(err.detail);
    }
  },
);

export const delete_user = command(
  z.object({ tenant: z.string(), username: z.string() }),
  async ({ tenant, username }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/userAccounts/${
        encodeURIComponent(username)
      }`,
      { method: "DELETE" },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to delete user",
      }));
      throw new Error(err.detail);
    }
  },
);

export const change_password = command(
  z.object({
    tenant: z.string(),
    username: z.string(),
    password: z.string(),
  }),
  async ({ tenant, username, password }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/userAccounts/${
        encodeURIComponent(username)
      }/changePassword`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ password }),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to change password",
      }));
      throw new Error(err.detail);
    }
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
