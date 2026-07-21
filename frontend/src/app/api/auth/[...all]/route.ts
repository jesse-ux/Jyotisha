import { toNextJsHandler } from "better-auth/next-js";

import { getIdentityAuthServices } from "@/modules/identity/auth";
import { readIdentityConfig } from "@/modules/identity/config";
import {
  createHostIsolatedAuthHandlers,
  type IdentityAuthHandlers,
} from "@/modules/identity/host";

export const dynamic = "force-dynamic";

async function dispatch(
  method: keyof IdentityAuthHandlers,
  request: Request,
): Promise<Response> {
  const config = readIdentityConfig(process.env);
  if (config.provider !== "self-hosted") {
    return new Response("Not found", { status: 404 });
  }

  const services = getIdentityAuthServices();
  const handlers = createHostIsolatedAuthHandlers(config, {
    user: toNextJsHandler(services.user),
    admin: toNextJsHandler(services.admin),
  });
  return handlers[method](request);
}

export function GET(request: Request): Promise<Response> {
  return dispatch("GET", request);
}

export function POST(request: Request): Promise<Response> {
  return dispatch("POST", request);
}
