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
  z.object({ bucket: z.string(), prefix: z.string() }),
  async ({ bucket, prefix }) => {
    try {
      const params = new URLSearchParams({
        max_keys: "100",
        delimiter: "/",
      });
      if (prefix) params.set("prefix", prefix);
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
    } catch (err) {
      console.error("[buckets.remote]", err);
    }
    return {
      objects: [] as {
        key: string;
        size: number;
        last_modified: string;
        etag: string;
        storage_class: string;
        owner: {
          display_name?: string;
          id?: string;
          DisplayName?: string;
          ID?: string;
        } | null;
      }[],
      commonPrefixes: [] as string[],
      isTruncated: false,
      keyCount: 0,
      nextToken: null,
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
        detail: "Failed to create bucket",
      }));
      throw new Error(err.detail);
    }
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
