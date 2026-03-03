import { command, query } from "$app/server";
import { z } from "zod";
import { apiFetch } from "$lib/server/api.js";

export const get_buckets = query(async () => {
  try {
    const res = await apiFetch("/api/v1/buckets");
    if (res.ok) {
      const data = await res.json();
      const buckets = (data.buckets ?? []).map(
        (b: Record<string, unknown>) => ({
          name: b.name ?? b.Name ?? "",
          creation_date: b.creation_date ?? b.CreationDate ?? "",
        }),
      );
      return { buckets, owner: data.owner ?? "" };
    }
  } catch {
    // ignore
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
      const params = new URLSearchParams({ max_keys: "100" });
      if (prefix) params.set("prefix", prefix);
      const res = await apiFetch(
        `/api/v1/buckets/${encodeURIComponent(bucket)}/objects?${params}`,
      );
      if (res.ok) {
        const data = await res.json();
        const objects = (data.objects ?? []).map(
          (o: Record<string, unknown>) => ({
            key: o.key ?? o.Key ?? "",
            size: o.size ?? o.Size ?? 0,
            last_modified: o.last_modified ?? o.LastModified ?? "",
            etag: o.etag ?? o.ETag ?? "",
            storage_class: o.storage_class ?? o.StorageClass ?? "",
          }),
        );
        return {
          objects,
          isTruncated: data.is_truncated ?? false,
          nextToken: data.next_continuation_token ?? null,
          keyCount: data.key_count ?? 0,
        };
      }
    } catch {
      // ignore
    }
    return {
      objects: [] as {
        key: string;
        size: number;
        last_modified: string;
        etag: string;
        storage_class: string;
      }[],
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
    let failCount = 0;
    for (const key of keys) {
      const res = await apiFetch(
        `/api/v1/buckets/${encodeURIComponent(bucket)}/objects/${
          encodeURIComponent(key)
        }`,
        { method: "DELETE" },
      );
      if (!res.ok) failCount++;
    }
    if (failCount > 0) {
      throw new Error(
        `Failed to delete ${failCount} of ${keys.length} objects`,
      );
    }
  },
);
