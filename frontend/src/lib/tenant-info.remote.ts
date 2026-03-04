import { z } from "zod";
import { command, query } from "$app/server";
import { apiFetch } from "$lib/server/api.js";

export interface TenantInfo {
  name: string;
  systemVisibleDescription?: string;
  tenantVisibleDescription?: string;
  hardQuota?: string;
  softQuota?: string;
  namespaceQuota?: number;
  authenticationTypes?: { authenticationType: string[] };
  complianceConfigurationEnabled?: boolean;
  versioningConfigurationEnabled?: boolean;
  searchConfigurationEnabled?: boolean;
  replicationConfigurationEnabled?: boolean;
  servicePlan?: string;
}

export interface TenantStatistics {
  objectCount: number;
  bytesUsed: string;
  customMetadataObjectCount?: number;
  shredObjectCount?: number;
  namespacesUsed?: number;
}

export interface TenantSettings {
  consoleSecurity: Record<string, unknown>;
  contactInfo: Record<string, unknown>;
  permissions: Record<string, unknown>;
  namespaceDefaults: Record<string, unknown>;
}

export interface ChargebackEntry {
  namespaceName?: string;
  objectCount?: number;
  ingestedVolume?: number;
  storageCapacityUsed?: number;
  bytesIn?: number;
  bytesOut?: number;
  reads?: number;
  writes?: number;
  deletes?: number;
  valid?: boolean;
}

export interface ChargebackReport {
  chargebackData?: ChargebackEntry[];
}

export const get_tenant = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    try {
      const res = await apiFetch(`/api/v1/mapi/tenants/${tenant}?verbose=true`);
      if (res.ok) return (await res.json()) as TenantInfo;
    } catch {
      // ignore
    }
    return { name: tenant } as TenantInfo;
  },
);

export const get_tenant_statistics = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    try {
      const res = await apiFetch(`/api/v1/mapi/tenants/${tenant}/statistics`);
      if (res.ok) return (await res.json()) as TenantStatistics;
    } catch {
      // ignore
    }
    return {
      objectCount: 0,
      bytesUsed: "0",
    } as TenantStatistics;
  },
);

export const get_tenant_chargeback = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/chargebackReport`,
      );
      if (res.ok) return (await res.json()) as ChargebackReport;
    } catch {
      // ignore
    }
    return { chargebackData: [] } as ChargebackReport;
  },
);

export const get_tenant_settings = query(
  z.object({ tenant: z.string() }),
  async ({ tenant }) => {
    const base = `/api/v1/mapi/tenants/${tenant}`;
    const keys = [
      "consoleSecurity",
      "contactInfo",
      "permissions",
      "namespaceDefaults",
    ] as const;

    const results = await Promise.all(
      keys.map(async (key) => {
        try {
          const res = await apiFetch(`${base}/${key}`);
          if (res.ok) return [key, await res.json()] as const;
        } catch {
          // ignore
        }
        return [key, {}] as const;
      }),
    );

    return Object.fromEntries(results) as TenantSettings;
  },
);

export const update_contact_info = command(
  z.object({ tenant: z.string(), body: z.record(z.string(), z.unknown()) }),
  async ({ tenant, body }) => {
    const res = await apiFetch(`/api/v1/mapi/tenants/${tenant}/contactInfo`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update contact info",
      }));
      throw new Error(err.detail);
    }
  },
);

export const update_namespace_defaults = command(
  z.object({ tenant: z.string(), body: z.record(z.string(), z.unknown()) }),
  async ({ tenant, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaceDefaults`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update namespace defaults",
      }));
      throw new Error(err.detail);
    }
  },
);

export const update_permissions = command(
  z.object({ tenant: z.string(), body: z.record(z.string(), z.unknown()) }),
  async ({ tenant, body }) => {
    const res = await apiFetch(`/api/v1/mapi/tenants/${tenant}/permissions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update permissions",
      }));
      throw new Error(err.detail);
    }
  },
);
