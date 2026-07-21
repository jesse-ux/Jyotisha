import type { SelfHostedIdentityConfig } from "./config.ts";
import type { IdentitySurface } from "./contracts.ts";

export type IdentityRequestHandler = (
  request: Request,
) => Response | Promise<Response>;

export interface IdentityAuthHandlers {
  GET: IdentityRequestHandler;
  POST: IdentityRequestHandler;
}

function normalizeHost(value: string | null): string | null {
  if (!value || value !== value.trim() || /[\s,@/\\]/.test(value)) return null;

  try {
    const url = new URL(`https://${value}`);
    if (
      url.username ||
      url.password ||
      url.pathname !== "/" ||
      url.search ||
      url.hash
    ) {
      return null;
    }
    return url.host.toLowerCase();
  } catch {
    return null;
  }
}

export function resolveIdentitySurface(
  hostHeader: string | null,
  config: SelfHostedIdentityConfig,
): IdentitySurface | null {
  const host = normalizeHost(hostHeader);
  if (!host) return null;

  const userHost = new URL(config.userOrigin).host.toLowerCase();
  const adminHost = new URL(config.adminOrigin).host.toLowerCase();
  if (host === userHost) return "user";
  if (host === adminHost) return "admin";
  return null;
}

function isAdminEndpoint(request: Request): boolean {
  try {
    const path = decodeURIComponent(new URL(request.url).pathname);
    return /^\/api\/auth\/+admin(?:\/|$)/i.test(path);
  } catch {
    return true;
  }
}

export function createHostIsolatedAuthHandlers(
  config: SelfHostedIdentityConfig,
  handlers: Record<IdentitySurface, IdentityAuthHandlers>,
): IdentityAuthHandlers {
  const dispatch =
    (method: keyof IdentityAuthHandlers): IdentityRequestHandler =>
    async (request) => {
      const surface = resolveIdentitySurface(request.headers.get("host"), config);
      if (!surface) {
        return new Response("Unrecognized identity host", { status: 421 });
      }
      if (surface === "user" && isAdminEndpoint(request)) {
        return new Response("Not found", { status: 404 });
      }
      return handlers[surface][method](request);
    };

  return { GET: dispatch("GET"), POST: dispatch("POST") };
}
