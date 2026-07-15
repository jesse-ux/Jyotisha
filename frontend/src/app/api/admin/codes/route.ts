import { NextResponse } from "next/server";
import { z } from "zod";
import {
  createAdminSupabaseClient,
  isAdminEmail,
} from "@/lib/supabase/admin";
import {
  generateRedeemCode,
  hashRedeemCode,
  maskRedeemCode,
} from "@/lib/supabase/codes";
import {
  isSupabaseConfigurationError,
  SupabaseConfigurationError,
} from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

const createCodesSchema = z.object({
  credits: z.number().int().positive().max(1_000_000),
  count: z.number().int().min(1).max(100),
  expiresAt: z.string().datetime({ offset: true }).optional(),
  note: z.string().trim().max(500).optional(),
});

async function requireAdmin() {
  if (!process.env.ADMIN_EMAILS?.trim()) {
    throw new SupabaseConfigurationError(["ADMIN_EMAILS"]);
  }

  const supabase = await createServerSupabaseClient();
  const { data: { user }, error } = await supabase.auth.getUser();
  if (error || !user) return { response: NextResponse.json({ error: "请先登录" }, { status: 401 }) };
  if (!isAdminEmail(user.email)) {
    return { response: NextResponse.json({ error: "无管理员权限" }, { status: 403 }) };
  }
  return { user };
}

export async function GET() {
  try {
    const auth = await requireAdmin();
    if ("response" in auth) return auth.response;

    const admin = createAdminSupabaseClient();
    const { data, error } = await admin
      .from("redemption_codes")
      .select("id,code_mask,credits,expires_at,note,created_at,redeemed_by,redeemed_email,redeemed_at")
      .order("created_at", { ascending: false })
      .limit(100);

    if (error) {
      return NextResponse.json({ error: "暂时无法读取兑换码列表" }, { status: 500 });
    }

    return NextResponse.json({
      codes: data.map((code) => ({
        id: code.id,
        mask: code.code_mask,
        credits: code.credits,
        expiresAt: code.expires_at,
        note: code.note,
        createdAt: code.created_at,
        redeemedBy: code.redeemed_by,
        redeemedEmail: code.redeemed_email,
        redeemedAt: code.redeemed_at,
      })),
    });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 或管理员白名单尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: "兑换码管理服务暂时不可用" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const auth = await requireAdmin();
    if ("response" in auth) return auth.response;

    const parsed = createCodesSchema.safeParse(await request.json().catch(() => null));
    if (!parsed.success) {
      return NextResponse.json({ error: "兑换码参数不正确" }, { status: 400 });
    }

    const { credits, count, expiresAt, note } = parsed.data;
    const codes = Array.from({ length: count }, generateRedeemCode);
    const admin = createAdminSupabaseClient();
    const { error } = await admin.from("redemption_codes").insert(codes.map((code) => ({
      code_hash: hashRedeemCode(code),
      code_mask: maskRedeemCode(code),
      credits,
      expires_at: expiresAt ?? null,
      note: note || null,
      created_by: auth.user.id,
    })));

    if (error) {
      return NextResponse.json({ error: "生成兑换码失败，请重试" }, { status: 500 });
    }

    return NextResponse.json({
      codes: codes.map((code) => ({ code, credits, expiresAt: expiresAt ?? null, note: note || null })),
    }, { status: 201 });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 或管理员白名单尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: "兑换码管理服务暂时不可用" }, { status: 500 });
  }
}
