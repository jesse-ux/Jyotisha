import { createHash } from "node:crypto";

export function resolveDynamicRectificationToken(
  configuredToken: string | undefined,
  serviceRoleKey: string | undefined,
): string | null {
  const configured = configuredToken?.trim();
  if (configured) return configured;
  const serviceRole = serviceRoleKey?.trim();
  if (!serviceRole) return null;
  return createHash("sha256")
    .update(`jyotisha-dynamic-rectification-v1:${serviceRole}`)
    .digest("hex");
}
