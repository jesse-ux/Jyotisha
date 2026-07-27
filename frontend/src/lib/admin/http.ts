import { NextResponse } from "next/server";
import { z } from "zod";

import { AdminAuthorizationError } from "./auth";

export const listQuerySchema = z.object({
  page: z.coerce.number().int().min(1).default(1),
  pageSize: z.coerce.number().int().min(1).max(100).default(20),
  sort: z.string().trim().max(64).optional(),
  order: z.enum(["asc", "desc"]).default("desc"),
  q: z.string().trim().max(200).optional(),
  status: z.string().trim().max(50).optional(),
});

export type ListQuery = z.infer<typeof listQuerySchema>;

export function parseListQuery(request: Request) {
  return listQuerySchema.safeParse(
    Object.fromEntries(new URL(request.url).searchParams.entries()),
  );
}

export function requestId(request: Request): string {
  const supplied = request.headers.get("x-request-id")?.trim();
  return supplied && supplied.length <= 200 ? supplied : crypto.randomUUID();
}

export function adminErrorResponse(error: unknown) {
  if (error instanceof AdminAuthorizationError) {
    return NextResponse.json({ error: error.message }, { status: error.status });
  }
  return NextResponse.json(
    { error: "后台服务暂时不可用" },
    { status: 500 },
  );
}

export function invalidQueryResponse(details?: unknown) {
  return NextResponse.json(
    { error: "查询参数不正确", ...(details ? { details } : {}) },
    { status: 400 },
  );
}

export async function readonlyAdminMutation() {
  try {
    const { requireAdminSession } = await import("./auth");
    await requireAdminSession();
    return NextResponse.json({ error: "此资源只读" }, { status: 405 });
  } catch (error) {
    return adminErrorResponse(error);
  }
}
