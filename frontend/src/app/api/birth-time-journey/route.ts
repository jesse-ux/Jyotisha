import { NextResponse } from "next/server";
import { z } from "zod";
import { parseBirthTimeProfile } from "@/lib/birth-time-journey-adapters";
import {
  createJyotishBirthTimeJourneyEngine,
  BirthTimeJourneyEngineError,
} from "@/lib/birth-time-journey-engine";
import {
  createBirthTimeJourneyService,
  RectificationCaseNotFoundError,
} from "@/lib/birth-time-journey-service";
import {
  createSupabaseBirthTimeJourneyStore,
  BirthTimeJourneyStoreError,
} from "@/lib/birth-time-journey-store";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";

export const runtime = "nodejs";
export const maxDuration = 60;

const eventSchema = z.discriminatedUnion("type", [
  z.object({ type: z.literal("assess") }).strict(),
  z.object({
    type: z.literal("answer_question"),
    caseId: z.string().uuid(),
    questionId: z.string().trim().min(1).max(120),
    answer: z.enum(["A", "B", "C", "D"]),
  }).strict(),
]);

async function requestPayload(request: Request): Promise<unknown> {
  try {
    return await request.json();
  } catch (error) {
    if (error instanceof SyntaxError) return null;
    throw error;
  }
}

export async function POST(request: Request) {
  let supabase: Awaited<ReturnType<typeof createServerSupabaseClient>>;
  try {
    supabase = await createServerSupabaseClient();
  } catch (error) {
    if (isSupabaseConfigurationError(error)) {
      return NextResponse.json(
        { error: "服务尚未配置", message: "请先配置 Supabase 环境变量。" },
        { status: 503 },
      );
    }
    throw error;
  }

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: "请先登录", message: "登录后才能继续出生时间评估。" },
      { status: 401 },
    );
  }

  const parsed = eventSchema.safeParse(await requestPayload(request));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "生时评估请求格式不正确", details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  const service = createBirthTimeJourneyService({
    store: createSupabaseBirthTimeJourneyStore(supabase),
    engine: createJyotishBirthTimeJourneyEngine(),
  });

  try {
    switch (parsed.data.type) {
      case "assess": {
        const { data: profile, error } = await supabase
          .from("profiles")
          .select("birth_date,reported_birth_time,birth_time_source,birth_time_period,birth_time_clue,uncertainty_before_minutes,uncertainty_after_minutes,latitude,longitude,timezone_offset")
          .eq("id", user.id)
          .maybeSingle();
        if (error) throw new BirthTimeJourneyStoreError("load_case");
        if (!profile) {
          return NextResponse.json(
            { error: "出生资料尚未完成", message: "请先填写出生日期、时间情况和地点。" },
            { status: 409 },
          );
        }
        const assessment = parseBirthTimeProfile(profile);
        return NextResponse.json(await service.assess(user.id, assessment));
      }
      case "answer_question":
        return NextResponse.json(await service.answerQuestion(
          user.id,
          parsed.data.caseId,
          parsed.data.questionId,
          parsed.data.answer,
        ));
      default: {
        const exhaustive: never = parsed.data;
        return exhaustive;
      }
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "出生资料尚未完成", message: "请检查出生时间情况和地点后重试。" },
        { status: 409 },
      );
    }
    if (error instanceof RectificationCaseNotFoundError) {
      return NextResponse.json(
        { error: "校正记录不存在", message: "请重新开始出生时间评估。" },
        { status: 404 },
      );
    }
    if (error instanceof BirthTimeJourneyStoreError || error instanceof BirthTimeJourneyEngineError) {
      return NextResponse.json(
        { error: "生时评估暂时不可用", message: "已保留当前资料，请稍后重试。" },
        { status: 503 },
      );
    }
    throw error;
  }
}
