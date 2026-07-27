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

type TransactionRow = {
  id: string;
  user_id: string;
  email: string | null;
  transaction_type: string;
  amount: number;
  balance_after: number;
  request_id: string;
  model: string | null;
  input_tokens: number | null;
  output_tokens: number | null;
  created_at: Date;
  total_count: string;
};

const sortColumns = new Map([
  ["createdAt", "t.created_at"],
  ["amount", "t.amount"],
  ["balanceAfter", "t.balance_after"],
  ["type", "t.transaction_type"],
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
      conditions.push(`(p.email ilike $${values.length} or t.request_id ilike $${values.length})`);
    }
    if (status && ["redeem", "reserve", "refund"].includes(status)) {
      values.push(status);
      conditions.push(`t.transaction_type = $${values.length}`);
    }
    values.push(pageSize, pageOffset(page, pageSize));
    const sortColumn = sortColumns.get(sort ?? "createdAt") ?? "t.created_at";
    const rows = await queryAdminRows<TransactionRow>(`
      select t.id, t.user_id, p.email, t.transaction_type, t.amount,
        t.balance_after, t.request_id, t.model, t.input_tokens,
        t.output_tokens, t.created_at, count(*) over()::text as total_count
      from public.credit_transactions t
      left join public.profiles p on p.id = t.user_id
      ${conditions.length ? `where ${conditions.join(" and ")}` : ""}
      order by ${sortColumn} ${order === "asc" ? "asc" : "desc"}, t.id asc
      limit $${values.length - 1} offset $${values.length}
    `, values);
    return NextResponse.json({
      data: rows.map((row) => ({
        id: row.id,
        userId: row.user_id,
        email: row.email,
        type: row.transaction_type,
        amount: row.amount,
        balanceAfter: row.balance_after,
        requestId: row.request_id,
        model: row.model,
        inputTokens: row.input_tokens,
        outputTokens: row.output_tokens,
        createdAt: row.created_at.toISOString(),
      })),
      total: Number(rows[0]?.total_count ?? 0),
    });
  } catch (error) {
    return adminErrorResponse(error);
  }
}
