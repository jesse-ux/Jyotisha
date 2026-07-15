export class SupabaseConfigurationError extends Error {
  readonly code = "SUPABASE_NOT_CONFIGURED";

  constructor(missing: string[]) {
    super(`Supabase 配置缺失：${missing.join(", ")}`);
    this.name = "SupabaseConfigurationError";
  }
}

export function getSupabaseUrl() {
  const url = process.env.NEXT_PUBLIC_SUPABASE_URL;
  if (!url) throw new SupabaseConfigurationError(["NEXT_PUBLIC_SUPABASE_URL"]);
  return url;
}

export function getSupabasePublicConfig() {
  const url = getSupabaseUrl();
  const anonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY;
  if (!anonKey) {
    throw new SupabaseConfigurationError(["NEXT_PUBLIC_SUPABASE_ANON_KEY"]);
  }
  return { url, anonKey };
}

export function isSupabaseConfigurationError(error: unknown) {
  return error instanceof SupabaseConfigurationError;
}
