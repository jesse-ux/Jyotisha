import { NextResponse } from "next/server";
import { z } from "zod";

import { requireAdminSession } from "@/lib/admin/auth";
import { mapCode, runCodeRpc, type RedemptionCodeRecord } from "@/lib/admin/codes";
import { pageOffset, queryAdminRows } from "@/lib/admin/database";
import {
  adminErrorResponse,
  invalidQueryResponse,
  parseListQuery,
  requestId,
} from "@/lib/admin/http";
import {
  generateRedeemCode,
  hashRedeemCode,
  maskRedeemCode,
} from "@/lib/supabase/codes";

export const runtime = "nodejs";

const createCodesSchema = z.object({
  credits: z.number().int().positive().max(1_000_000),
  count: z.number().int().min(1).max(100),
  expiresAt: z.string().datetime({ offset: true }).nullable().optional(),
  note: z.string().trim().max(500).nullable().optional(),
});

type CodeRow = {
  id: string;
  code_mask: string;
  credits: number;
  expires_at: Date | null;
  note: string | null;
  created_at: Date;
  redeemed_by: string | null;
  redeemed_email: string | null;
  redeemed_at: Date | null;
  revoked_by: string | null;
  revoked_at: Date | null;
  total_count: string;
};

const sortColumns = new Map([
  ["createdAt", "c.created_at"],
  ["expiresAt", "c.expires_at"],
  ["credits", "c.credits"],
  ["status", "status"],
]);

function serializedCodeRow(row: CodeRow) {
  return mapCode({
    ...row,
    expires_at: row.expires_at?.toISOString() ?? null,
    created_at: row.created_at.toISOString(),
    redeemed_at: row.redeemed_at?.toISOString() ?? null,
    revoked_at: row.revoked_at?.toISOString() ?? null,
  });
}

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
      conditions.push(`(c.code_mask ilike $${values.length} or c.note ilike $${values.length})`);
    }
    if (status && ["available", "expired", "redeemed", "revoked"].includes(status)) {
      const clauses = {
        available: "c.redeemed_at is null and c.revoked_at is null and (c.expires_at is null or c.expires_at > now())",
        expired: "c.redeemed_at is null and c.revoked_at is null and c.expires_at <= now()",
        redeemed: "c.redeemed_at is not null",
        revoked: "c.revoked_at is not null",
      };
      conditions.push(clauses[status as keyof typeof clauses]);
    }
    values.push(pageSize, pageOffset(page, pageSize));
    const sortColumn = sortColumns.get(sort ?? "createdAt") ?? "c.created_at";
    const rows = await queryAdminRows<CodeRow>(`
      select c.id, c.code_mask, c.credits, c.expires_at, c.note,
        c.created_at, c.redeemed_by, c.redeemed_email, c.redeemed_at,
        c.revoked_by, c.revoked_at,
        case
          when c.redeemed_at is not null then 'redeemed'
          when c.revoked_at is not null then 'revoked'
          when c.expires_at is not null and c.expires_at <= now() then 'expired'
          else 'available'
        end as status,
        count(*) over()::text as total_count
      from public.redemption_codes c
      ${conditions.length ? `where ${conditions.join(" and ")}` : ""}
      order by ${sortColumn} ${order === "asc" ? "asc" : "desc"}, c.id asc
      limit $${values.length - 1} offset $${values.length}
    `, values);
    return NextResponse.json({
      data: rows.map(serializedCodeRow),
      total: Number(rows[0]?.total_count ?? 0),
    });
  } catch (error) {
    return adminErrorResponse(error);
  }
}

export async function POST(request: Request) {
  try {
    const session = await requireAdminSession("write");
    const parsed = createCodesSchema.safeParse(await request.json().catch(() => null));
    if (!parsed.success) return invalidQueryResponse(parsed.error.flatten());
    const plainCodes = Array.from({ length: parsed.data.count }, generateRedeemCode);
    const records = plainCodes.map((code) => ({
      codeHash: hashRedeemCode(code),
      codeMask: maskRedeemCode(code),
      credits: parsed.data.credits,
      expiresAt: parsed.data.expiresAt ?? null,
      note: parsed.data.note || null,
    }));
    const operationRequestId = requestId(request);
    const stored = await runCodeRpc(
      "admin_create_redemption_codes",
      session,
      operationRequestId,
      { p_codes: records },
    );
    const byMask = new Map<string, RedemptionCodeRecord>(
      stored.map((record) => [record.mask, record]),
    );
    return NextResponse.json({
      data: {
        id: operationRequestId,
        generated: plainCodes.map((code) => ({
          ...(byMask.get(maskRedeemCode(code)) ?? {}),
          code,
        })),
      },
    }, { status: 201 });
  } catch (error) {
    return adminErrorResponse(error);
  }
}
