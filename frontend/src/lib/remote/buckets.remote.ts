import { command, query } from "$app/server";
import { z } from "zod";
import { apiFetch } from "$lib/server/api.js";

export const get_buckets = query(async () => {
  try {
    const res = await apiFetch("/api/v1/buckets");
    if (res.ok) {
      const data = await res.json();
      const buckets = (data.buckets ?? []).map((
        b: Record<string, unknown>,
      ) => ({
        name: b.name ?? b.Name ?? "",
        creation_date: b.creation_date ?? b.CreationDate ?? "",
      }));
      return { buckets, owner: data.owner ?? "" };
    }
  } catch (err) {
    console.error("[buckets.remote]", err);
  }
  return {
    buckets: [] as { name: string; creation_date: string }[],
    owner: "",
  };
});

export const get_objects = query(
  z.object({
    bucket: z.string(),
    prefix: z.string(),
    continuation_token: z.string().optional(),
    flat: z.boolean().optional(),
  }),
  async ({ bucket, prefix, continuation_token, flat }) => {
    try {
      const params = new URLSearchParams({
        max_keys: flat ? "1000" : "200",
      });
      if (!flat) params.set("delimiter", "/");
      if (prefix) params.set("prefix", prefix);
      if (continuation_token) {
        params.set("continuation_token", continuation_token);
      }
      const res = await apiFetch(
        `/api/v1/buckets/${encodeURIComponent(bucket)}/objects?${params}`,
      );
      if (res.ok) {
        const data = await res.json();
        const objects = (data.objects ?? []).map((
          o: Record<string, unknown>,
        ) => ({
          key: o.key ?? o.Key ?? "",
          size: o.size ?? o.Size ?? 0,
          last_modified: o.last_modified ?? o.LastModified ?? "",
          etag: o.etag ?? o.ETag ?? "",
          storage_class: o.storage_class ?? o.StorageClass ?? "",
          owner: (o.owner ?? o.Owner ?? null) as {
            display_name?: string;
            id?: string;
            DisplayName?: string;
            ID?: string;
          } | null,
        }));
        const commonPrefixes = (data.common_prefixes ?? []) as string[];
        return {
          objects,
          commonPrefixes,
          isTruncated: data.is_truncated ?? false,
          nextToken: data.next_continuation_token ?? null,
          keyCount: data.key_count ?? 0,
        };
      }
      if (res.status === 403) {
        return {
          objects: [],
          commonPrefixes: [] as string[],
          isTruncated: false,
          keyCount: 0,
          nextToken: null,
          error:
            "Access Denied — you don't have permission to list objects in this namespace." as
              | string
              | null,
        };
      }
    } catch (err) {
      console.error("[buckets.remote]", err);
    }
    return {
      objects: [],
      commonPrefixes: [] as string[],
      isTruncated: false,
      keyCount: 0,
      nextToken: null,
      error: null as string | null,
    };
  },
);

export const create_bucket = command(
  z.object({ bucket: z.string() }),
  async ({ bucket }) => {
    const res = await apiFetch("/api/v1/buckets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bucket }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: `Failed to create bucket "${bucket}"`,
      }));
      const raw = typeof err.detail === "string"
        ? err.detail
        : JSON.stringify(err.detail);
      // Extract a user-friendly message from backend errors
      let message = raw;
      if (/invalid namespace name/i.test(raw)) {
        message =
          `Invalid bucket name "${bucket}". Bucket names must use only lowercase letters, numbers, hyphens, and dots (no underscores or spaces). Must be 3–63 characters long.`;
      }
      return { error: message };
    }
    return { error: null as string | null };
  },
);

export const delete_bucket = command(
  z.object({ bucket: z.string() }),
  async ({ bucket }) => {
    const res = await apiFetch(
      `/api/v1/buckets/${encodeURIComponent(bucket)}`,
      { method: "DELETE" },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to delete bucket",
      }));
      throw new Error(err.detail);
    }
  },
);

export const delete_object = command(
  z.object({ bucket: z.string(), key: z.string() }),
  async ({ bucket, key }) => {
    const res = await apiFetch(
      `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${
        encodeURIComponent(key)
      }`,
      { method: "DELETE" },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to delete object",
      }));
      throw new Error(err.detail);
    }
  },
);

export const bulk_delete_objects = command(
  z.object({ bucket: z.string(), keys: z.array(z.string()) }),
  async ({ bucket, keys }) => {
    const res = await apiFetch(
      `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/delete`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keys }),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to delete objects",
      }));
      throw new Error(err.detail);
    }
    const data = await res.json();
    if (data.errors && data.errors.length > 0) {
      throw new Error(
        `Failed to delete ${data.errors.length} of ${keys.length} objects`,
      );
    }
  },
);

export const get_s3_credentials = query(async () => {
  try {
    const res = await apiFetch("/api/v1/credentials");
    if (res.ok) {
      const data = await res.json();
      return {
        access_key_id: (data.access_key_id ?? "") as string,
        secret_access_key: (data.secret_access_key ?? "") as string,
        username: (data.username ?? "") as string,
        endpoint_url: (data.endpoint_url ?? "") as string,
      };
    }
  } catch (err) {
    console.error("[buckets.remote]", err);
  }
  return {
    access_key_id: "",
    secret_access_key: "",
    username: "",
    endpoint_url: "",
  };
});

export const bulk_presign = command(
  z.object({
    bucket: z.string(),
    keys: z.array(z.string()).min(1),
    expires_in: z.number().min(1).max(604800).default(3600),
  }),
  async ({ bucket, keys, expires_in }) => {
    const res = await apiFetch(
      `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/presign`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ keys, expires_in }),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to generate presigned URLs",
      }));
      throw new Error(err.detail);
    }
    const data = await res.json();
    return {
      urls: (data.urls ?? []) as { key: string; url: string }[],
      expires_in: (data.expires_in ?? expires_in) as number,
    };
  },
);

export const generate_presigned_url = command(
  z.object({
    bucket: z.string(),
    key: z.string(),
    expires_in: z.number().min(1).max(604800),
    method: z.enum(["get_object", "put_object"]),
  }),
  async ({ bucket, key, expires_in, method }) => {
    const res = await apiFetch("/api/v1/presign", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ bucket, key, expires_in, method }),
    });
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to generate presigned URL",
      }));
      throw new Error(err.detail);
    }
    const data = await res.json();
    return {
      url: data.url as string,
      bucket: data.bucket as string,
      key: data.key as string,
      expires_in: data.expires_in as number,
      method: data.method as string,
    };
  },
);

// ── ZIP Download Task ───────────────────────────────────────────────

export const start_zip_download = command(
  z.object({
    bucket: z.string(),
    prefix: z.string().optional(),
    keys: z.array(z.string()).optional(),
  }),
  async ({ bucket, prefix, keys }) => {
    const body: Record<string, unknown> = {};
    if (prefix != null) body.prefix = prefix;
    if (keys && keys.length > 0) body.keys = keys;
    const res = await apiFetch(
      `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/download`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to start ZIP download",
      }));
      throw new Error(
        typeof err.detail === "string" ? err.detail : JSON.stringify(
          err.detail,
        ),
      );
    }
    return (await res.json()) as {
      task_id: string;
      status: string;
      total: number;
    };
  },
);

export const poll_zip_download = query(
  z.object({ bucket: z.string(), task_id: z.string() }),
  async ({ bucket, task_id }) => {
    try {
      const res = await apiFetch(
        `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/download/${
          encodeURIComponent(task_id)
        }`,
      );
      if (res.ok) {
        const contentType = res.headers.get("content-type") ?? "";
        if (contentType.includes("application/json")) {
          return (await res.json()) as {
            task_id: string;
            status: string;
            total: number;
            completed: number;
            failed: number;
            failed_keys: string[];
          };
        }
        // If it's a ZIP file, the task is ready
        return {
          task_id,
          status: "ready" as string,
          total: 0,
          completed: 0,
          failed: 0,
          failed_keys: [] as string[],
        };
      }
    } catch (err) {
      console.error("[buckets.remote] poll_zip_download", err);
    }
    return null;
  },
);

// ── Head Object ─────────────────────────────────────────────────────

export const head_object = query(
  z.object({ bucket: z.string(), key: z.string() }),
  async ({ bucket, key }) => {
    try {
      const res = await apiFetch(
        `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${
          encodeURIComponent(key)
        }`,
        { method: "HEAD" },
      );
      if (res.ok) {
        return {
          content_length: Number(res.headers.get("content-length") ?? 0),
          content_type: res.headers.get("content-type") ?? "",
          etag: res.headers.get("etag") ?? "",
          last_modified: res.headers.get("last-modified") ?? "",
        };
      }
    } catch (err) {
      console.error("[buckets.remote] head_object", err);
    }
    return null;
  },
);

// ── Copy Object ─────────────────────────────────────────────────────

export const copy_object = command(
  z.object({
    bucket: z.string(),
    key: z.string(),
    source_bucket: z.string(),
    source_key: z.string(),
  }),
  async ({ bucket, key, source_bucket, source_key }) => {
    const res = await apiFetch(
      `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${
        encodeURIComponent(key)
      }/copy`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ source_bucket, source_key }),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to copy object",
      }));
      throw new Error(err.detail);
    }
    return await res.json();
  },
);

// ── Bucket Versioning ───────────────────────────────────────────────

export type BucketVersioning = {
  status: string | null;
  mfa_delete: string | null;
  error?: string | null;
};

export const get_bucket_versioning = query(
  z.object({ bucket: z.string() }),
  async ({ bucket }) => {
    try {
      const res = await apiFetch(
        `/api/v1/buckets/${encodeURIComponent(bucket)}/versioning`,
      );
      if (res.ok) {
        const data = await res.json();
        return {
          status: (data.status ?? null) as string | null,
          mfa_delete: (data.mfa_delete ?? null) as string | null,
          error: null,
        };
      }
      if (res.status === 403) {
        return {
          status: null,
          mfa_delete: null,
          error: "Access Denied — insufficient permissions.",
        };
      }
    } catch (err) {
      console.error("[buckets.remote] get_bucket_versioning", err);
    }
    return { status: null, mfa_delete: null, error: null } as BucketVersioning;
  },
);

export const set_bucket_versioning = command(
  z.object({
    bucket: z.string(),
    status: z.enum(["Enabled", "Suspended"]),
  }),
  async ({ bucket, status }) => {
    const res = await apiFetch(
      `/api/v1/buckets/${encodeURIComponent(bucket)}/versioning`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ status }),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update versioning",
      }));
      throw new Error(err.detail);
    }
    return await res.json();
  },
);

// ── Bucket ACL ──────────────────────────────────────────────────────

export type AclOwner = {
  ID?: string;
  DisplayName?: string;
};

export type AclGrant = {
  Grantee?: Record<string, unknown>;
  Permission?: string;
};

export type AclData = {
  owner: AclOwner | null;
  grants: AclGrant[];
  error?: string | null;
};

export const get_bucket_acl = query(
  z.object({ bucket: z.string() }),
  async ({ bucket }) => {
    try {
      const res = await apiFetch(
        `/api/v1/buckets/${encodeURIComponent(bucket)}/acl`,
      );
      if (res.ok) {
        const data = await res.json();
        return {
          owner: (data.owner ?? null) as AclOwner | null,
          grants: (data.grants ?? []) as AclGrant[],
          error: null,
        };
      }
      if (res.status === 403) {
        return {
          owner: null,
          grants: [] as AclGrant[],
          error:
            "Access Denied — you don't have READ_ACL permission on this namespace.",
        };
      }
      return {
        owner: null,
        grants: [] as AclGrant[],
        error: `Failed to load ACL (HTTP ${res.status})`,
      };
    } catch (err) {
      console.error("[buckets.remote] get_bucket_acl", err);
    }
    return {
      owner: null,
      grants: [] as AclGrant[],
      error: "Failed to load ACL",
    };
  },
);

export const put_bucket_acl = command(
  z.object({
    bucket: z.string(),
    owner: z.record(z.string(), z.unknown()).optional(),
    grants: z.array(z.record(z.string(), z.unknown())),
  }),
  async ({ bucket, owner, grants }) => {
    const res = await apiFetch(
      `/api/v1/buckets/${encodeURIComponent(bucket)}/acl`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ Owner: owner, Grants: grants }),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update bucket ACL",
      }));
      throw new Error(err.detail);
    }
    return await res.json();
  },
);

// ── Object ACL ──────────────────────────────────────────────────────

export const get_object_acl = query(
  z.object({ bucket: z.string(), key: z.string() }),
  async ({ bucket, key }) => {
    try {
      const res = await apiFetch(
        `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${
          encodeURIComponent(key)
        }/acl`,
      );
      if (res.ok) {
        const data = await res.json();
        return {
          owner: (data.owner ?? null) as AclOwner | null,
          grants: (data.grants ?? []) as AclGrant[],
        };
      }
    } catch (err) {
      console.error("[buckets.remote] get_object_acl", err);
    }
    return { owner: null, grants: [] } as AclData;
  },
);

export const put_object_acl = command(
  z.object({
    bucket: z.string(),
    key: z.string(),
    owner: z.record(z.string(), z.unknown()).optional(),
    grants: z.array(z.record(z.string(), z.unknown())),
  }),
  async ({ bucket, key, owner, grants }) => {
    const res = await apiFetch(
      `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${
        encodeURIComponent(key)
      }/acl`,
      {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ Owner: owner, Grants: grants }),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Failed to update object ACL",
      }));
      throw new Error(err.detail);
    }
    return await res.json();
  },
);
