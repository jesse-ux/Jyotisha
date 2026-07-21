import type { IdentitySession, IdentityUser } from "./contracts.ts";

interface RawIdentitySession {
  session: { expiresAt: Date | string };
  user: {
    id: string;
    email: string;
    emailVerified: boolean;
    name: string;
    image?: string | null;
    role?: string | null;
  };
}

export interface IdentitySessionReader {
  getSession(input: { headers: Headers }): Promise<RawIdentitySession | null>;
}

export class IdentityAuthorizationError extends Error {
  constructor(
    message: string,
    readonly status: 401 | 403,
  ) {
    super(message);
    this.name = "IdentityAuthorizationError";
  }
}

function parseRoles(role: string | null | undefined): string[] {
  const roles = (role ?? "user")
    .split(",")
    .map((value) => value.trim())
    .filter(Boolean);
  return [...new Set(roles.length ? roles : ["user"])];
}

export async function readIdentitySession(
  reader: IdentitySessionReader,
  requestHeaders: Headers,
): Promise<IdentitySession | null> {
  const value = await reader.getSession({ headers: requestHeaders });
  if (!value) return null;

  const expiresAt = new Date(value.session.expiresAt);
  if (!Number.isFinite(expiresAt.getTime())) {
    throw new Error("identity session has an invalid expiry");
  }

  return {
    expiresAt,
    user: {
      id: value.user.id,
      email: value.user.email.trim().toLowerCase(),
      emailVerified: value.user.emailVerified,
      name: value.user.name,
      image: value.user.image ?? null,
      role: parseRoles(value.user.role),
    },
  };
}

export async function requireIdentityUser(
  reader: IdentitySessionReader,
  requestHeaders: Headers,
): Promise<IdentityUser> {
  const session = await readIdentitySession(reader, requestHeaders);
  if (!session) throw new IdentityAuthorizationError("Authentication required", 401);
  return session.user;
}

export async function requireIdentityAdmin(
  reader: IdentitySessionReader,
  requestHeaders: Headers,
): Promise<IdentityUser> {
  const user = await requireIdentityUser(reader, requestHeaders);
  if (!user.role.includes("admin")) {
    throw new IdentityAuthorizationError("Administrator access required", 403);
  }
  return user;
}
