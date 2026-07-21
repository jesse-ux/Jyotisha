export type DatabaseUrlKey =
  | "IDENTITY_DATABASE_URL"
  | "APP_DATABASE_URL"
  | "ADMIN_DATABASE_URL";

export function readDatabaseUrl(
  env: NodeJS.ProcessEnv,
  key: DatabaseUrlKey,
): string {
  const value = env[key]?.trim();
  if (!value) throw new Error(`${key} is required`);
  if (!value.startsWith("postgresql://")) {
    throw new Error(`${key} must be a PostgreSQL URL`);
  }
  return value;
}
