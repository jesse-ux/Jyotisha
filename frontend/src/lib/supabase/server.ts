import "server-only";

import { createServerClient } from "@supabase/ssr";
import type { SupabaseClient } from "@supabase/supabase-js";
import { cookies, headers } from "next/headers";
import { createLocalPostgresDataClient } from "@/lib/db/local-postgres-client";
import { readDatabaseUrl } from "@/lib/db/config";
import { getIdentityAuthServices } from "@/modules/identity/auth";
import { readIdentitySession } from "@/modules/identity/session";
import { readSelfHostedIdentityConfig } from "@/modules/identity/config";
import { resolveIdentitySurface } from "@/modules/identity/host";
import { getSupabasePublicConfig } from "./config";

export async function createServerSupabaseClient() {
  if (process.env.AUTH_PROVIDER?.trim() === "self-hosted") {
    const requestHeaders = new Headers(await headers());
    const services = getIdentityAuthServices();
    const surface = resolveIdentitySurface(
      requestHeaders.get("host"),
      readSelfHostedIdentityConfig(process.env),
    );
    const auth = surface === "admin" ? services.admin : services.user;
    const session = await readIdentitySession(auth.api, requestHeaders);
    return createLocalPostgresDataClient(
      readDatabaseUrl(process.env, "APP_DATABASE_URL"),
      session ? { id: session.user.id, email: session.user.email } : null,
    ) as unknown as SupabaseClient;
  }
  const { url, anonKey } = getSupabasePublicConfig();
  const cookieStore = await cookies();

  return createServerClient(url, anonKey, {
    cookies: {
      getAll: () => cookieStore.getAll(),
      setAll: (cookiesToSet) => {
        try {
          cookiesToSet.forEach(({ name, value, options }) => {
            cookieStore.set(name, value, options);
          });
        } catch {
          // Server Components cannot write cookies; Route Handlers can.
        }
      },
    },
  });
}
