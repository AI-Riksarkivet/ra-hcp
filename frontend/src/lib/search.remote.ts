import { z } from "zod";
import { command, query } from "$app/server";
import { apiFetch } from "$lib/server/api.js";

export interface QueryStatus {
  totalResults: number;
  results: number;
  code: string;
  message?: string;
}

export interface QueryResultObject {
  urlName: string;
  operation: string;
  changeTimeMilliseconds?: string;
  changeTimeString?: string;
  version?: string;
  namespace?: string;
  utf8Name?: string;
  size?: number;
  contentType?: string;
  hold?: boolean;
  retention?: string;
  retentionString?: string;
  retentionClass?: string;
  hash?: string;
  customMetadata?: boolean;
  replicated?: boolean;
  index?: boolean;
  ingestTimeMilliseconds?: string;
  owner?: string;
  type?: string;
}

export interface ObjectQueryResponse {
  status: QueryStatus;
  resultSet: QueryResultObject[];
}

export interface OperationQueryResponse {
  status: QueryStatus;
  resultSet: QueryResultObject[];
}

export const search_objects = command(
  z.object({
    tenant: z.string(),
    query: z.string().default("*:*"),
    count: z.number().optional(),
    offset: z.number().optional(),
    verbose: z.boolean().optional(),
    sort: z.string().optional(),
  }),
  async ({ tenant, ...params }) => {
    const body: Record<string, unknown> = { query: params.query };
    if (params.count != null) body.count = params.count;
    if (params.offset != null) body.offset = params.offset;
    if (params.verbose != null) body.verbose = params.verbose;
    if (params.sort) body.sort = params.sort;

    const res = await apiFetch(
      `/api/v1/query/tenants/${encodeURIComponent(tenant)}/objects`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Object query failed",
      }));
      throw new Error(err.detail);
    }
    return (await res.json()) as ObjectQueryResponse;
  },
);

export const search_operations = command(
  z.object({
    tenant: z.string(),
    count: z.number().optional(),
    verbose: z.boolean().optional(),
    transactions: z.array(z.string()).optional(),
    namespaces: z.array(z.string()).optional(),
    changeTimeFrom: z.string().optional(),
    changeTimeTo: z.string().optional(),
  }),
  async ({ tenant, ...params }) => {
    const body: Record<string, unknown> = {};
    if (params.count != null) body.count = params.count;
    if (params.verbose != null) body.verbose = params.verbose;

    const systemMetadata: Record<string, unknown> = {};
    if (params.changeTimeFrom) {
      systemMetadata.changeTimeFrom = params.changeTimeFrom;
    }
    if (params.changeTimeTo) {
      systemMetadata.changeTimeTo = params.changeTimeTo;
    }
    if (params.namespaces?.length) {
      systemMetadata.namespaces = params.namespaces;
    }
    if (params.transactions?.length) {
      systemMetadata.transactions = { transaction: params.transactions };
    }
    if (Object.keys(systemMetadata).length > 0) {
      body.systemMetadata = systemMetadata;
    }

    const res = await apiFetch(
      `/api/v1/query/tenants/${encodeURIComponent(tenant)}/operations`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      },
    );
    if (!res.ok) {
      const err = await res.json().catch(() => ({
        detail: "Operation query failed",
      }));
      throw new Error(err.detail);
    }
    return (await res.json()) as OperationQueryResponse;
  },
);

export const get_recent_operations = query(
  z.object({ tenant: z.string(), count: z.number().default(10) }),
  async ({ tenant, count }) => {
    const res = await apiFetch(
      `/api/v1/query/tenants/${encodeURIComponent(tenant)}/operations`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ count, verbose: true }),
      },
    );
    if (!res.ok) {
      return {
        status: { totalResults: 0, results: 0, code: "ERROR" },
        resultSet: [],
      } as OperationQueryResponse;
    }
    return (await res.json()) as OperationQueryResponse;
  },
);
