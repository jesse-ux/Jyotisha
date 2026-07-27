import { NextResponse } from "next/server";
import { z } from "zod";
import { hashRedeemCode, normalizeRedeemCode } from "@/lib/supabase/codes";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

const requestSchema = z.object({ code: z.string().max(100) });

const redeemErrors: Record<string, { status: number; message: string }> = {
  unauthorized: { status: 401, message: "请先登录" },
  invalid_code: { status: 404, message: "兑换码不存在" },
  expired_code: { status: 410, message: "兑换码已过期" },
  revoked_code: { status: 410, message: "兑换码已撤销" },
  already_redeemed: { status: 409, message: "兑换码已被使用" },
  profile_missing: { status: 500, message: "账户资料不存在，请稍后重试" },
};

export async function POST(request: Request) {
  try {
    const parsed = requestSchema.safeParse(await request.json().catch(() => null));
    if (!parsed.success) {
      return NextResponse.json({ error: "请输入有效兑换码" }, { status: 400 });
    }

    const code = normalizeRedeemCode(parsed.data.code);
    if (!/^JYOTISH-[A-Z0-9]{4}-[A-Z0-9]{4}$/.test(code)) {
      return NextResponse.json({ error: "兑换码格式不正确" }, { status: 400 });
    }

    const supabase = await createServerSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: "请先登录" }, { status: 401 });
    }

    const { data, error } = await supabase.rpc("redeem_code", {
      p_code_hash: hashRedeemCode(code),
    });

    if (error) {
      return NextResponse.json({ error: "兑换失败，请稍后重试" }, { status: 500 });
    }

    const result = Array.isArray(data) ? data[0] : data;
    if (!result?.success) {
      const mapped = redeemErrors[result?.error_code] ?? {
        status: 500,
        message: "兑换失败，请稍后重试",
      };
      return NextResponse.json({ error: mapped.message }, { status: mapped.status });
    }

    return NextResponse.json({ credits: result.credits });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置", code: "SUPABASE_NOT_CONFIGURED" }, { status: 503 });
    }
    return NextResponse.json({ error: "兑换服务暂时不可用" }, { status: 500 });
  }
}
