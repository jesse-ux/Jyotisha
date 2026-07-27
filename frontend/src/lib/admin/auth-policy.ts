import type { IdentityUser } from "@/modules/identity/contracts";

export type AdminRole = "admin" | "viewer";

export type AdminAccessResult =
  | { allowed: true; role: AdminRole }
  | { allowed: false; status: 401 | 403 };

export function authorizeAdminAccess(
  user: IdentityUser | null,
  access: "read" | "write",
): AdminAccessResult {
  if (!user) return { allowed: false, status: 401 };
  const role: AdminRole | null = user.role.includes("admin")
    ? "admin"
    : user.role.includes("viewer")
      ? "viewer"
      : null;
  if (!role || (access === "write" && role !== "admin")) {
    return { allowed: false, status: 403 };
  }
  return { allowed: true, role };
}
