import { drizzle, type NodePgDatabase } from "drizzle-orm/node-postgres";
import { Pool } from "pg";

export type DomainDatabase = { pool: Pool; db: NodePgDatabase };

export function createDomainDatabase(
  connectionString: string,
  maxConnections = 5,
): DomainDatabase {
  const pool = new Pool({
    connectionString,
    max: maxConnections,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
    application_name: "jyotisha-web",
  });
  return { pool, db: drizzle(pool) };
}
