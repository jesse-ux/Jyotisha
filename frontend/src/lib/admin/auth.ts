import "server-only";

import { headers } from "next/headers";

import { getIdentityAuthServices } from "@/modules/identity/auth";
import {
  IdentityAuthorizationError,
  requireIdentityUser,
} from "@/modules/identity/session";
import type { IdentityUser } from "@/modules/identity/contracts";
import { authorizeAdminAccess, type AdminRole } from "./auth-policy";

export type { AdminRole } from "./auth-policy";

export class AdminAuthorizationError extends Error {
  constructor(
    message: string,
    readonly status: 401 | 403,
  ) {
    super(message);
    this.name = "AdminAuthorizationError";
  }
}

export async function requireAdminSession(
  access: "read" | "write" = "read",
): Promise<{ user: IdentityUser; role: AdminRole }> {
  if (
    process.env.AUTH_PROVIDER?.trim() !== "self-hosted"
    || process.env.APP_ENV?.trim() === "production"
  ) {
    throw new AdminAuthorizationError("后台身份服务未启用", 403);
  }

  try {
    const user = await requireIdentityUser(
      getIdentityAuthServices().admin.api,
      new Headers(await headers()),
    );
    const authorization = authorizeAdminAccess(user, access);
    if (!authorization.allowed) {
      throw new AdminAuthorizationError("无权执行此操作", authorization.status);
    }
    return { user, role: authorization.role };
  } catch (error) {
    if (error instanceof AdminAuthorizationError) throw error;
    if (error instanceof IdentityAuthorizationError) {
      throw new AdminAuthorizationError(
        error.status === 401 ? "请先登录" : "无权访问后台",
        error.status,
      );
    }
    throw error;
  }
}
