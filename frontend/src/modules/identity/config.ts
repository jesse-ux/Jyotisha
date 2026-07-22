type IdentityEnvironment = Record<string, string | undefined>;

export interface SupabaseIdentityConfig {
  provider: "supabase";
}

export interface SelfHostedIdentityConfig {
  provider: "self-hosted";
  databaseUrl: string;
  userOrigin: string;
  adminOrigin: string;
  userSecret: string;
  adminSecret: string;
  resendApiKey: string;
  resendFrom: string;
}

export type IdentityConfig =
  | SupabaseIdentityConfig
  | SelfHostedIdentityConfig;

export function isSelfHostedIdentityEnabled(
  env: IdentityEnvironment,
): boolean {
  const value = env.SELF_HOSTED_IDENTITY_ENABLED?.trim() || "false";
  if (value !== "true" && value !== "false") {
    throw new Error("SELF_HOSTED_IDENTITY_ENABLED must be true or false");
  }
  return value === "true";
}

function required(env: IdentityEnvironment, key: string): string {
  const value = env[key]?.trim();
  if (!value) throw new Error(`${key} is required`);
  return value;
}

function readPostgresUrl(env: IdentityEnvironment): string {
  const value = required(env, "IDENTITY_DATABASE_URL");
  if (!value.startsWith("postgresql://")) {
    throw new Error("IDENTITY_DATABASE_URL must be a PostgreSQL URL");
  }

  try {
    const url = new URL(value);
    if (!url.hostname || !url.pathname || url.pathname === "/") {
      throw new Error("invalid PostgreSQL URL");
    }
  } catch {
    throw new Error("IDENTITY_DATABASE_URL must be a PostgreSQL URL");
  }

  return value;
}

function readOrigin(env: IdentityEnvironment, key: string): string {
  const value = required(env, key);
  let url: URL;
  try {
    url = new URL(value);
  } catch {
    throw new Error(`${key} must be a valid origin`);
  }

  const isLocalhost =
    url.hostname === "localhost" || url.hostname.endsWith(".localhost");
  if (url.protocol !== "https:" && !(isLocalhost && url.protocol === "http:")) {
    throw new Error(`${key} must use HTTPS outside localhost`);
  }
  if (url.pathname !== "/" || url.search || url.hash || url.username || url.password) {
    throw new Error(`${key} must be an origin without a path`);
  }

  return url.origin;
}

function readSecret(env: IdentityEnvironment, key: string): string {
  const value = required(env, key);
  if (value.length < 32) {
    throw new Error(`${key} must be at least 32 characters`);
  }
  return value;
}

function readSender(env: IdentityEnvironment): string {
  const value = required(env, "RESEND_FROM_EMAIL");
  const match = value.match(/(?:^|<)([^<>\s]+@[^<>\s]+)(?:>|$)/);
  if (!match) {
    throw new Error("RESEND_FROM_EMAIL must contain a valid email address");
  }
  return value;
}

export function readSelfHostedIdentityConfig(
  env: IdentityEnvironment,
): SelfHostedIdentityConfig {
  const userOrigin = readOrigin(env, "AUTH_USER_ORIGIN");
  const adminOrigin = readOrigin(env, "AUTH_ADMIN_ORIGIN");
  if (userOrigin === adminOrigin) {
    throw new Error("user and admin origins must be different");
  }

  const userSecret = readSecret(env, "BETTER_AUTH_USER_SECRET");
  const adminSecret = readSecret(env, "BETTER_AUTH_ADMIN_SECRET");
  if (userSecret === adminSecret) {
    throw new Error("user and admin secrets must be different");
  }

  return {
    provider: "self-hosted",
    databaseUrl: readPostgresUrl(env),
    userOrigin,
    adminOrigin,
    userSecret,
    adminSecret,
    resendApiKey: required(env, "RESEND_API_KEY"),
    resendFrom: readSender(env),
  };
}

export function readIdentityConfig(
  env: IdentityEnvironment,
): IdentityConfig {
  const provider = env.AUTH_PROVIDER?.trim() || "supabase";
  if (provider === "supabase") return { provider };
  if (provider !== "self-hosted") {
    throw new Error("AUTH_PROVIDER must be supabase or self-hosted");
  }
  if (!isSelfHostedIdentityEnabled(env)) {
    throw new Error(
      "SELF_HOSTED_IDENTITY_ENABLED must be true when AUTH_PROVIDER is self-hosted",
    );
  }
  return readSelfHostedIdentityConfig(env);
}
