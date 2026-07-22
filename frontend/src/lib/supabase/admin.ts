import "server-only";

import { createClient, type SupabaseClient } from "@supabase/supabase-js";
import { createLocalPostgresDataClient } from "@/lib/db/local-postgres-client";
import { readDatabaseUrl } from "@/lib/db/config";
import {
  getSupabaseUrl,
  SupabaseConfigurationError,
} from "./config";

export function createAdminSupabaseClient() {
  if (process.env.AUTH_PROVIDER?.trim() === "self-hosted") {
    return createLocalPostgresDataClient(
      readDatabaseUrl(process.env, "ADMIN_DATABASE_URL"),
      null,
      "service_role",
    ) as unknown as SupabaseClient;
  }
  const url = getSupabaseUrl();
  const serviceRoleKey = process.env.SUPABASE_SERVICE_ROLE_KEY;
  if (!serviceRoleKey) {
    throw new SupabaseConfigurationError(["SUPABASE_SERVICE_ROLE_KEY"]);
  }

  return createClient(url, serviceRoleKey, {
    auth: { autoRefreshToken: false, persistSession: false },
  });
}

export function isAdminEmail(email: string | null | undefined) {
  const configured = process.env.ADMIN_EMAILS;
  if (!configured?.trim() || !email) return false;

  const normalized = email.trim().toLowerCase();
  return configured
    .split(",")
    .some((candidate) => candidate.trim().toLowerCase() === normalized);
}
