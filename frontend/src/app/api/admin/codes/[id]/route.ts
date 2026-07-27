import { NextResponse } from "next/server";
import { z } from "zod";

import { requireAdminSession } from "@/lib/admin/auth";
import { runCodeRpc } from "@/lib/admin/codes";
import {
  adminErrorResponse,
  invalidQueryResponse,
  requestId,
} from "@/lib/admin/http";

export const runtime = "nodejs";

const paramsSchema = z.object({ id: z.string().uuid() });
const updateCodeSchema = z.object({
  note: z.string().trim().max(500).nullable().optional(),
  expiresAt: z.string().datetime({ offset: true }).nullable().optional(),
}).refine((value) => "note" in value || "expiresAt" in value, {
  message: "至少提供一个可修改字段",
});

export async function PATCH(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const session = await requireAdminSession("write");
    const parsedParams = paramsSchema.safeParse(await context.params);
    const parsedBody = updateCodeSchema.safeParse(await request.json().catch(() => null));
    if (!parsedParams.success || !parsedBody.success) {
      return invalidQueryResponse();
    }
    const body = parsedBody.data;
    const rows = await runCodeRpc(
      "admin_update_redemption_code",
      session,
      requestId(request),
      {
        p_code_id: parsedParams.data.id,
        p_set_note: "note" in body,
        p_note: body.note ?? null,
        p_set_expires_at: "expiresAt" in body,
        p_expires_at: body.expiresAt ?? null,
      },
    );
    return NextResponse.json({ data: rows[0] });
  } catch (error) {
    return adminErrorResponse(error);
  }
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ id: string }> },
) {
  try {
    const session = await requireAdminSession("write");
    const parsed = paramsSchema.safeParse(await context.params);
    if (!parsed.success) return invalidQueryResponse();
    const rows = await runCodeRpc(
      "admin_revoke_redemption_code",
      session,
      requestId(request),
      { p_code_id: parsed.data.id },
    );
    return NextResponse.json({ data: rows[0] });
  } catch (error) {
    return adminErrorResponse(error);
  }
}
