import { NextResponse } from "next/server";
import { z } from "zod";
import { candidateWorkingTime } from "@/lib/birth-time-candidate-completion";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const runtime = "nodejs";

const requestSchema = z.object({
  caseId: z.string().uuid(),
  resultId: z.string().uuid(),
  time: z.string().regex(/^([01]\d|2[0-3]):[0-5]\d$/),
}).strict();

export async function POST(request: Request) {
  try {
    const supabase = await createServerSupabaseClient();
    const { data: { user }, error: authError } = await supabase.auth.getUser();
    if (authError || !user) {
      return NextResponse.json({ error: "请先登录" }, { status: 401 });
    }

    const parsed = requestSchema.safeParse(await request.json().catch(() => null));
    if (!parsed.success) {
      return NextResponse.json({ error: "候选时间格式不正确" }, { status: 400 });
    }

    const admin = createAdminSupabaseClient();
    const { data: stored, error: caseError } = await admin
      .from("birth_time_rectification_cases")
      .select("id,user_id,status,candidate_result_id,candidate_result,turn_state")
      .eq("id", parsed.data.caseId)
      .eq("user_id", user.id)
      .maybeSingle();
    const time = candidateWorkingTime(stored, { ...parsed.data, userId: user.id });
    if (caseError || !time) {
      return NextResponse.json(
        { error: "候选结果已变化", message: "请使用当前评估结果继续。" },
        { status: 409 },
      );
    }

    const { data: profile, error: profileError } = await admin
      .from("profiles")
      .update({
        active_birth_time: time,
        birth_time_status: "candidate",
        updated_at: new Date().toISOString(),
      })
      .eq("id", user.id)
      .eq("rectification_case_id", parsed.data.caseId)
      .select("id")
      .maybeSingle();
    if (profileError || !profile) {
      return NextResponse.json(
        { error: "候选时间暂时无法保存", message: "当前评估结果仍已保留，请稍后重试。" },
        { status: 503 },
      );
    }

    return NextResponse.json({ ok: true, activeTime: time, birthTimeStatus: "candidate" });
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json({ error: "Supabase 尚未配置" }, { status: 503 });
    }
    return NextResponse.json({ error: "候选时间暂时无法保存" }, { status: 500 });
  }
}
