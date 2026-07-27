"use client";

import type {
  AccessControlProvider,
  AuthProvider,
  BaseRecord,
  CrudFilter,
  DataProvider,
  HttpError,
CreateParams,
DeleteOneParams,
GetListParams,
GetOneParams,
UpdateParams,
} from "@refinedev/core";

export type AdminIdentity = {
  id: string;
  email: string;
  name: string;
  role: "admin" | "viewer";
};

const apiBase = "/api/admin";
let identityCache: AdminIdentity | null = null;

function logicalFilters(filters: CrudFilter[] | undefined) {
  return (filters ?? []).filter(
    (filter): filter is Extract<CrudFilter, { field: string }> => "field" in filter,
  );
}

async function requestJson<T>(url: string, init?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    cache: "no-store",
    credentials: "same-origin",
    ...init,
    headers: {
      ...(init?.body ? { "content-type": "application/json" } : {}),
      ...init?.headers,
    },
  });
  const payload = await response.json().catch(() => null);
  if (!response.ok) {
    const message = payload && typeof payload.error === "string"
      ? payload.error
      : "后台请求失败";
    throw { message, statusCode: response.status } satisfies HttpError;
  }
  return payload as T;
}

function listParams(
  pagination: { currentPage?: number; pageSize?: number } | undefined,
  sorters: { field: string; order: "asc" | "desc" }[] | undefined,
  filters: CrudFilter[] | undefined,
) {
  const search = new URLSearchParams({
    page: String(pagination?.currentPage ?? 1),
    pageSize: String(pagination?.pageSize ?? 20),
  });
  const sorter = sorters?.[0];
  if (sorter) {
    search.set("sort", sorter.field);
    search.set("order", sorter.order);
  }
  for (const filter of logicalFilters(filters)) {
    if (filter.value === undefined || filter.value === null || filter.value === "") continue;
    if (filter.field === "q" || filter.field === "status") {
      search.set(filter.field, String(filter.value));
    }
  }
  return search;
}

export const adminDataProvider: DataProvider = {
  async getList<TData extends BaseRecord>({ resource, pagination, sorters, filters }: GetListParams) {
    const search = listParams(pagination, sorters, filters);
    return requestJson<{ data: TData[]; total: number }>(
      `${apiBase}/${resource}?${search}`,
    );
  },
  async getOne<TData extends BaseRecord>({ resource, id }: GetOneParams) {
    return requestJson<{ data: TData }>(`${apiBase}/${resource}/${id}`);
  },
  async create<TData extends BaseRecord, TVariables>({ resource, variables }: CreateParams<TVariables>) {
    return requestJson<{ data: TData }>(`${apiBase}/${resource}`, {
      method: "POST",
      body: JSON.stringify(variables),
    });
  },
  async update<TData extends BaseRecord, TVariables>({ resource, id, variables }: UpdateParams<TVariables>) {
    return requestJson<{ data: TData }>(`${apiBase}/${resource}/${id}`, {
      method: "PATCH",
      body: JSON.stringify(variables),
    });
  },
  async deleteOne<TData extends BaseRecord, TVariables>({ resource, id }: DeleteOneParams<TVariables>) {
    return requestJson<{ data: TData }>(`${apiBase}/${resource}/${id}`, {
      method: "DELETE",
    });
  },
  getApiUrl: () => apiBase,
};

async function loadIdentity(): Promise<AdminIdentity> {
  if (identityCache) return identityCache;
  const payload = await requestJson<{ user: AdminIdentity }>(`${apiBase}/session`);
  identityCache = payload.user;
  return identityCache;
}

export const adminAuthProvider: AuthProvider = {
  async login() {
    return { success: false, redirectTo: "/login" };
  },
  async logout() {
    identityCache = null;
    await fetch("/api/auth/sign-out", {
      method: "POST",
      credentials: "same-origin",
    });
    return { success: true, redirectTo: "/login" };
  },
  async check() {
    try {
      await loadIdentity();
      return { authenticated: true };
    } catch (error) {
      const status = (error as HttpError).statusCode;
      return {
        authenticated: false,
        redirectTo: status === 401 ? "/login" : "/",
        error: error as HttpError,
      };
    }
  },
  async onError(error) {
    const status = (error as HttpError)?.statusCode;
    if (status === 401) return { redirectTo: "/login", logout: true };
    if (status === 403) return { error: error as HttpError };
    return { error: error as HttpError };
  },
  async getPermissions() {
    return (await loadIdentity()).role;
  },
  async getIdentity() {
    return loadIdentity();
  },
};

const readOnlyResources = new Set([
  "users",
  "credit-transactions",
  "consultations",
  "audit-logs",
]);

export const adminAccessControlProvider: AccessControlProvider = {
  async can({ resource, action }) {
    const role = (await loadIdentity()).role;
    if (action === "list" || action === "show") return { can: true };
    if (readOnlyResources.has(resource ?? "")) {
      return { can: false, reason: "此资源只读" };
    }
    return role === "admin"
      ? { can: true }
      : { can: false, reason: "viewer 仅可查看" };
  },
  options: {
    buttons: { enableAccessControl: true, hideIfUnauthorized: true },
  },
};
