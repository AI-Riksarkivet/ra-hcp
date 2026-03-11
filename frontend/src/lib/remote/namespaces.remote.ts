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
  tags?: { tag: string[] };
  owner?: string;
  ownerType?: string;
  creationTime?: string;
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
    tags: z.array(z.string()).optional(),
    owner: z.string().optional(),
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
    if (body.tags) payload.tags = { tag: body.tags };
    if (body.owner) {
      payload.owner = body.owner;
      payload.ownerType = "LOCAL";
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

export const update_namespace = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, name, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${encodeURIComponent(name)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update namespace",
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

export const update_versioning = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    enabled: z.boolean(),
  }),
  async ({ tenant, name, enabled }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/versioningSettings`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ enabled }),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update versioning",
      }));
      throw new Error(err.detail);
    }
  },
);

// ── Versioning Settings (MAPI) ──────────────────────────────────────

export interface VersioningSettings {
  enabled?: boolean;
  prune?: boolean;
  pruneDays?: number;
  useDeleteMarkers?: boolean;
  keepDeletionRecords?: boolean;
}

export const get_ns_versioning = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/versioningSettings`,
      );
      if (res.ok) return (await res.json()) as VersioningSettings;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return {} as VersioningSettings;
  },
);

export const update_ns_versioning = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, name, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/versioningSettings`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update versioning settings",
      }));
      throw new Error(err.detail);
    }
  },
);

// ── Namespace Statistics ──────────────────────────────────────────────

export interface NsStatistics {
  objectCount?: number;
  storageCapacityUsed?: number;
  ingestedVolume?: number;
  customMetadataCount?: number;
  customMetadataSize?: number;
  shredCount?: number;
  shredSize?: number;
}

export const get_ns_statistics = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/statistics`,
      );
      if (res.ok) return (await res.json()) as NsStatistics;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return null;
  },
);

// ── Compliance Settings ──────────────────────────────────────────────

export interface ComplianceSettings {
  retentionDefault?: string;
  minimumRetentionAfterInitialUnspecified?: string;
  shreddingDefault?: boolean;
  customMetadataChanges?: string;
  dispositionEnabled?: boolean;
}

export const get_ns_compliance = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/complianceSettings`,
      );
      if (res.ok) return (await res.json()) as ComplianceSettings;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return {} as ComplianceSettings;
  },
);

export const update_ns_compliance = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, name, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/complianceSettings`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update compliance settings",
      }));
      throw new Error(err.detail);
    }
  },
);

// ── Retention Classes ────────────────────────────────────────────────

export interface RetentionClass {
  name?: string;
  value?: string;
  description?: string;
  allowDisposition?: boolean;
}

export const get_retention_classes = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const listRes = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/retentionClasses`,
      );
      if (!listRes.ok) return [] as RetentionClass[];
      const list = await listRes.json();
      const names: string[] = list.name ?? [];
      if (names.length === 0) return [] as RetentionClass[];

      const details = await Promise.all(
        names.map(async (rcName) => {
          try {
            const r = await apiFetch(
              `/api/v1/mapi/tenants/${tenant}/namespaces/${
                encodeURIComponent(name)
              }/retentionClasses/${encodeURIComponent(rcName)}`,
            );
            if (r.ok) return (await r.json()) as RetentionClass;
          } catch {
            // ignore individual failures
          }
          return { name: rcName } as RetentionClass;
        }),
      );
      return details;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return [] as RetentionClass[];
  },
);

export const create_retention_class = command(
  z.object({
    tenant: z.string(),
    namespace: z.string(),
    body: z.object({
      name: z.string(),
      value: z.string(),
      description: z.string().optional(),
      allowDisposition: z.boolean().optional(),
    }),
  }),
  async ({ tenant, namespace: ns, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(ns)
      }/retentionClasses`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to create retention class",
      }));
      throw new Error(err.detail);
    }
  },
);

export const update_retention_class = command(
  z.object({
    tenant: z.string(),
    namespace: z.string(),
    className: z.string(),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, namespace: ns, className, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(ns)
      }/retentionClasses/${encodeURIComponent(className)}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update retention class",
      }));
      throw new Error(err.detail);
    }
  },
);

export const delete_retention_class = command(
  z.object({
    tenant: z.string(),
    namespace: z.string(),
    className: z.string(),
  }),
  async ({ tenant, namespace: ns, className }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(ns)
      }/retentionClasses/${encodeURIComponent(className)}`,
      { method: "DELETE" },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to delete retention class",
      }));
      throw new Error(err.detail);
    }
  },
);

// ── Custom Metadata Indexing ─────────────────────────────────────────

export interface IndexingSettings {
  contentClasses?: string[];
  fullIndexingEnabled?: boolean;
  excludedAnnotations?: string;
}

export const get_ns_indexing = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/customMetadataIndexingSettings`,
      );
      if (res.ok) return (await res.json()) as IndexingSettings;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return {} as IndexingSettings;
  },
);

export const update_ns_indexing = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, name, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/customMetadataIndexingSettings`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update indexing settings",
      }));
      throw new Error(err.detail);
    }
  },
);

// ── CORS Configuration ───────────────────────────────────────────────

export interface CorsConfig {
  cors?: string;
}

export const get_ns_cors = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/cors`,
      );
      if (res.ok) return (await res.json()) as CorsConfig;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return {} as CorsConfig;
  },
);

export const set_ns_cors = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    body: z.object({ cors: z.string() }),
  }),
  async ({ tenant, name, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/cors`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to set CORS configuration",
      }));
      throw new Error(err.detail);
    }
  },
);

export const delete_ns_cors = command(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/cors`,
      { method: "DELETE" },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to delete CORS configuration",
      }));
      throw new Error(err.detail);
    }
  },
);

// ── Replication Collision Settings ───────────────────────────────────

export interface ReplicationCollision {
  action?: string;
  deleteDays?: number;
  deleteEnabled?: boolean;
}

export const get_repl_collision = query(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    try {
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/replicationCollisionSettings`,
      );
      if (res.ok) return (await res.json()) as ReplicationCollision;
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return {} as ReplicationCollision;
  },
);

export const update_repl_collision = command(
  z.object({
    tenant: z.string(),
    name: z.string(),
    body: z.record(z.string(), z.unknown()),
  }),
  async ({ tenant, name, body }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/replicationCollisionSettings`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update replication collision settings",
      }));
      throw new Error(err.detail);
    }
  },
);

// ── Namespace Templates (Export) ─────────────────────────────────────

export const export_namespace_config = command(
  z.object({ tenant: z.string(), name: z.string() }),
  async ({ tenant, name }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/${
        encodeURIComponent(name)
      }/export`,
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Export failed",
      }));
      throw new Error(err.detail);
    }
    return await res.json();
  },
);

export const export_namespace_configs = command(
  z.object({ tenant: z.string(), names: z.array(z.string()) }),
  async ({ tenant, names }) => {
    const res = await apiFetch(
      `/api/v1/mapi/tenants/${tenant}/namespaces/export?names=${
        names.map(encodeURIComponent).join(",")
      }`,
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Export failed",
      }));
      throw new Error(err.detail);
    }
    return await res.json();
  },
);

// ── Delete Namespace ─────────────────────────────────────────────────

// ── Namespace Chargeback ──────────────────────────────────────────────

export const get_ns_chargeback = query(
  z.object({
    tenant: z.string(),
    name: z.string(),
    start: z.string().optional(),
    end: z.string().optional(),
    granularity: z.enum(["hour", "day", "total"]).optional(),
  }),
  async ({ tenant, name, start, end, granularity }) => {
    try {
      const params = new URLSearchParams();
      if (start) params.set("start", start);
      if (end) params.set("end", end);
      if (granularity) params.set("granularity", granularity);
      const qs = params.toString();
      const res = await apiFetch(
        `/api/v1/mapi/tenants/${tenant}/namespaces/${
          encodeURIComponent(name)
        }/chargebackReport${qs ? `?${qs}` : ""}`,
      );
      if (res.ok) return await res.json();
    } catch (err) {
      console.error("[namespaces.remote]", err);
    }
    return { chargebackData: [] };
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
        detail: `Failed to delete namespace "${name}"`,
      }));
      const detail = typeof err.detail === "string"
        ? err.detail
        : JSON.stringify(err.detail);
      throw new Error(detail);
    }
  },
);
