import "server-only";

import { Pool, type QueryResultRow } from "pg";

import { readDatabaseUrl } from "@/lib/db/config";

const poolGlobal = globalThis as typeof globalThis & {
  jyotishaAdminReadPool?: Pool;
};

export function adminReadPool(): Pool {
  if (
    process.env.AUTH_PROVIDER?.trim() !== "self-hosted"
    || process.env.APP_ENV?.trim() === "production"
  ) {
    throw new Error("admin reads require the staging self-hosted identity service");
  }
  poolGlobal.jyotishaAdminReadPool ??= new Pool({
    connectionString: readDatabaseUrl(process.env, "ADMIN_DATABASE_URL"),
    max: 10,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
    allowExitOnIdle: true,
    application_name: "jyotisha-admin-read",
  });
  return poolGlobal.jyotishaAdminReadPool;
}

export async function queryAdminRows<T extends QueryResultRow>(
  sql: string,
  values: readonly unknown[] = [],
): Promise<T[]> {
  const result = await adminReadPool().query<T>(sql, [...values]);
  return result.rows;
}

export type PageResult<T> = { data: T[]; total: number };

export function pageOffset(page: number, pageSize: number) {
  return (page - 1) * pageSize;
}
