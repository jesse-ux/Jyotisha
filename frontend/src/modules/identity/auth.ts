import { betterAuth } from "better-auth";
import { Pool } from "pg";

import { buildAuthOptions, type AdminUserAuthorizer } from "./auth-factory.ts";
import {
  readIdentityConfig,
  type SelfHostedIdentityConfig,
} from "./config.ts";
import type { EmailOtpSender } from "./contracts.ts";
import { ResendEmailOtpSender } from "./email/resend-email-otp-sender.ts";

interface AdminRoleRow {
  role: string;
  banned: boolean;
  ban_expires: Date | null;
}

export function createIdentityPool(databaseUrl: string): Pool {
  return new Pool({
    connectionString: databaseUrl,
    options: "-c search_path=identity,pg_catalog",
    application_name: "jyotisha-identity",
    max: 10,
    idleTimeoutMillis: 30_000,
    connectionTimeoutMillis: 5_000,
  });
}

export function createDatabaseAdminAuthorizer(
  pool: Pool,
): AdminUserAuthorizer {
  return async (userId) => {
    const result = await pool.query<AdminRoleRow>(
      `
        select role, banned, ban_expires
        from identity.users
        where id = $1
        limit 1
      `,
      [userId],
    );
    const user = result.rows[0];
    if (!user) return false;

    if (user.banned) {
      const banExpiry = user.ban_expires?.getTime();
      if (banExpiry === undefined || !Number.isFinite(banExpiry)) return false;
      if (banExpiry > Date.now()) return false;
    }

    return user.role
      .split(",")
      .map((role) => role.trim())
      .includes("admin");
  };
}

export interface IdentityAuthServices {
  pool: Pool;
  user: ReturnType<typeof betterAuth>;
  admin: ReturnType<typeof betterAuth>;
}

interface IdentityAuthDependencies {
  pool?: Pool;
  emailSender?: EmailOtpSender;
  authorizeAdminUser?: AdminUserAuthorizer;
}

export function createIdentityAuthServices(
  config: SelfHostedIdentityConfig,
  dependencies: IdentityAuthDependencies = {},
): IdentityAuthServices {
  const pool = dependencies.pool ?? createIdentityPool(config.databaseUrl);
  const emailSender =
    dependencies.emailSender ??
    new ResendEmailOtpSender({
      apiKey: config.resendApiKey,
      from: config.resendFrom,
    });
  const authorizeAdminUser =
    dependencies.authorizeAdminUser ?? createDatabaseAdminAuthorizer(pool);

  return {
    pool,
    user: betterAuth(
      buildAuthOptions({
        surface: "user",
        config,
        database: pool,
        emailSender,
      }),
    ),
    admin: betterAuth(
      buildAuthOptions({
        surface: "admin",
        config,
        database: pool,
        emailSender,
        authorizeAdminUser,
      }),
    ),
  };
}

const identityGlobal = globalThis as typeof globalThis & {
  jyotishaIdentityAuth?: IdentityAuthServices;
};

export function getIdentityAuthServices(
  env: NodeJS.ProcessEnv = process.env,
): IdentityAuthServices {
  const config = readIdentityConfig(env);
  if (config.provider !== "self-hosted") {
    throw new Error("self-hosted identity is not enabled");
  }

  identityGlobal.jyotishaIdentityAuth ??= createIdentityAuthServices(config);
  return identityGlobal.jyotishaIdentityAuth;
}
