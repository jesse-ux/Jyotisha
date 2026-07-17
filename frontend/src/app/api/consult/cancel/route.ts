import { NextResponse } from "next/server";
import { z } from "zod";
import { runCreditRpc } from "@/lib/consultation-billing";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

const cancelRequestSchema = z.object({
  requestId: z.string().uuid(),
});

export async function POST(request: Request) {
  let supabase: Awaited<ReturnType<typeof createServerSupabaseClient>>;
  let accounting: ReturnType<typeof createAdminSupabaseClient>;
  try {
    supabase = await createServerSupabaseClient();
    accounting = createAdminSupabaseClient();
  } catch {
    return NextResponse.json(
      { error: "服务尚未配置", message: "请先配置 Supabase 环境变量。" },
      { status: 503 },
    );
  }

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: "请先登录", message: "登录后才能取消咨询。" },
      { status: 401 },
    );
  }

  const parsed = cancelRequestSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "取消请求格式不正确" },
      { status: 400 },
    );
  }

  try {
    const result = await runCreditRpc(
      accounting,
      "cancel_consultation_credit",
      user.id,
      parsed.data.requestId,
    );
    if (result.success) {
      return NextResponse.json({ cancelled: true, credits: result.credits });
    }
    if (result.error_code === "request_completed") {
      return NextResponse.json(
        { cancelled: false, credits: result.credits, message: "回答已经完成，本次咨询已计费。" },
        { status: 409 },
      );
    }
    if (result.error_code === "rate_limited") {
      return NextResponse.json(
        { cancelled: false, credits: result.credits, message: "取消请求过于频繁，请稍后再试。" },
        { status: 429 },
      );
    }
    return NextResponse.json(
      { cancelled: false, credits: result.credits, message: "暂时无法取消本次咨询。" },
      { status: 503 },
    );
  } catch (error) {
    console.error("[billing] cancellation RPC failed", error);
    return NextResponse.json(
      { cancelled: false, message: "暂时无法取消本次咨询。" },
      { status: 503 },
    );
  }
}
