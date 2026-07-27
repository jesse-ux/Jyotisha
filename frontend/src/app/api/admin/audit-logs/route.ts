import { NextResponse } from "next/server";

import { requireAdminSession } from "@/lib/admin/auth";
import { pageOffset, queryAdminRows } from "@/lib/admin/database";
import {
  adminErrorResponse,
  invalidQueryResponse,
  parseListQuery,
  readonlyAdminMutation,
} from "@/lib/admin/http";

export const runtime = "nodejs";

type AuditRow = {
  id: string;
  actor_user_id: string;
  actor_email: string;
  actor_role: string;
  action: string;
  target_type: string;
  target_id: string;
  before_value: Record<string, unknown> | null;
  after_value: Record<string, unknown> | null;
  request_id: string;
  created_at: Date;
  total_count: string;
};

const sortColumns = new Map([
  ["createdAt", "a.created_at"],
  ["action", "a.action"],
  ["actorEmail", "a.actor_email"],
]);

export const POST = readonlyAdminMutation;
export const PUT = readonlyAdminMutation;
export const PATCH = readonlyAdminMutation;
export const DELETE = readonlyAdminMutation;

export async function GET(request: Request) {
  try {
    await requireAdminSession();
    const parsed = parseListQuery(request);
    if (!parsed.success) return invalidQueryResponse(parsed.error.flatten());
    const { page, pageSize, sort, order, q, status } = parsed.data;
    const values: unknown[] = [];
    const conditions: string[] = [];
    if (q) {
      values.push(`%${q}%`);
      conditions.push(`(a.actor_email ilike $${values.length} or a.request_id ilike $${values.length})`);
    }
    if (status) {
      values.push(status);
      conditions.push(`a.action = $${values.length}`);
    }
    values.push(pageSize, pageOffset(page, pageSize));
    const sortColumn = sortColumns.get(sort ?? "createdAt") ?? "a.created_at";
    const rows = await queryAdminRows<AuditRow>(`
      select a.*, count(*) over()::text as total_count
      from audit.admin_audit_logs a
      ${conditions.length ? `where ${conditions.join(" and ")}` : ""}
      order by ${sortColumn} ${order === "asc" ? "asc" : "desc"}, a.id asc
      limit $${values.length - 1} offset $${values.length}
    `, values);
    return NextResponse.json({
      data: rows.map((row) => ({
        id: row.id,
        actorUserId: row.actor_user_id,
        actorEmail: row.actor_email,
        actorRole: row.actor_role,
        action: row.action,
        targetType: row.target_type,
        targetId: row.target_id,
        before: row.before_value,
        after: row.after_value,
        requestId: row.request_id,
        createdAt: row.created_at.toISOString(),
      })),
      total: Number(rows[0]?.total_count ?? 0),
    });
  } catch (error) {
    return adminErrorResponse(error);
  }
}
