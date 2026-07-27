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

type UserRow = {
  id: string;
  email: string;
  name: string | null;
  role: string;
  email_verified: boolean;
  banned: boolean;
  created_at: Date;
  credits: number;
  birth_date: string | null;
  birth_time_status: string | null;
  birth_place_label: string | null;
  total_count: string;
};

const sortColumns = new Map([
  ["createdAt", "u.created_at"],
  ["email", "u.email"],
  ["credits", "p.credits"],
  ["name", "u.name"],
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
    const { page, pageSize, sort, order, q } = parsed.data;
    const values: unknown[] = [];
    const conditions: string[] = [];
    if (q) {
      values.push(`%${q}%`);
      conditions.push(`(u.email ilike $${values.length} or u.name ilike $${values.length})`);
    }
    values.push(pageSize, pageOffset(page, pageSize));
    const sortColumn = sortColumns.get(sort ?? "createdAt") ?? "u.created_at";
    const rows = await queryAdminRows<UserRow>(`
      select
        u.id, u.email, u.name, u.role, u.email_verified, u.banned,
        u.created_at, p.credits, p.birth_date, p.birth_time_status,
        p.birth_place_label, count(*) over()::text as total_count
      from identity.users u
      join public.profiles p on p.id = u.id
      ${conditions.length ? `where ${conditions.join(" and ")}` : ""}
      order by ${sortColumn} ${order === "asc" ? "asc" : "desc"}, u.id asc
      limit $${values.length - 1} offset $${values.length}
    `, values);
    return NextResponse.json({
      data: rows.map((row) => ({
        id: row.id,
        email: row.email,
        name: row.name,
        role: row.role,
        emailVerified: row.email_verified,
        banned: row.banned,
        createdAt: row.created_at.toISOString(),
        credits: row.credits,
        birthDate: row.birth_date,
        birthTimeStatus: row.birth_time_status,
        birthPlace: row.birth_place_label,
      })),
      total: Number(rows[0]?.total_count ?? 0),
    });
  } catch (error) {
    return adminErrorResponse(error);
  }
}
