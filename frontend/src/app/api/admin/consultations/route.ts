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

type ConsultationRow = {
  id: string;
  user_id: string;
  email: string | null;
  request_id: string;
  status: string;
  created_at: Date;
  updated_at: Date;
  total_count: string;
};

const sortColumns = new Map([
  ["createdAt", "c.created_at"],
  ["updatedAt", "c.updated_at"],
  ["status", "c.status"],
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
      conditions.push(`(p.email ilike $${values.length} or c.request_id ilike $${values.length})`);
    }
    if (status && ["reserved", "completed", "cancelled"].includes(status)) {
      values.push(status);
      conditions.push(`c.status = $${values.length}`);
    }
    values.push(pageSize, pageOffset(page, pageSize));
    const sortColumn = sortColumns.get(sort ?? "createdAt") ?? "c.created_at";
    const rows = await queryAdminRows<ConsultationRow>(`
      select c.user_id || ':' || c.request_id as id, c.user_id, p.email,
        c.request_id, c.status, c.created_at, c.updated_at,
        count(*) over()::text as total_count
      from public.consultation_requests c
      left join public.profiles p on p.id = c.user_id
      ${conditions.length ? `where ${conditions.join(" and ")}` : ""}
      order by ${sortColumn} ${order === "asc" ? "asc" : "desc"}, c.request_id asc
      limit $${values.length - 1} offset $${values.length}
    `, values);
    return NextResponse.json({
      data: rows.map((row) => ({
        id: row.id,
        userId: row.user_id,
        email: row.email,
        requestId: row.request_id,
        status: row.status,
        createdAt: row.created_at.toISOString(),
        updatedAt: row.updated_at.toISOString(),
      })),
      total: Number(rows[0]?.total_count ?? 0),
    });
  } catch (error) {
    return adminErrorResponse(error);
  }
}
