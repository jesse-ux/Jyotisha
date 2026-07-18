import { NextResponse } from "next/server";
import { z } from "zod";
import { birthTimeGuideRequestSchema } from "@/lib/birth-time-guide-agent";
import {
  BirthTimeGuideActionError,
  createBirthTimeGuideService,
} from "@/lib/birth-time-guide-service";
import { BirthTimeJourneyActionError, createJourneyTurnActions } from "@/lib/birth-time-journey-actions";
import {
  BirthTimeJourneyStoreError,
  createSupabaseBirthTimeJourneyStore,
} from "@/lib/birth-time-journey-store";
import { StaleJourneyTurnError } from "@/lib/birth-time-journey-turn-persistence";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { isSupabaseConfigurationError } from "@/lib/supabase/config";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { getBirthTimeGuideAgent } from "@/mastra";
import { defaultLanguageModel } from "@/mastra/model";
import {
  recordJourneyTransitionMetric,
} from "@/lib/birth-time-journey-telemetry";

export const runtime = "nodejs";
export const maxDuration = 30;

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

  const parsed = birthTimeGuideRequestSchema.safeParse(await requestPayload(request));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "生时引导请求格式不正确", details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  const store = createSupabaseBirthTimeJourneyStore(createAdminSupabaseClient());
  const actions = createJourneyTurnActions({ store });
  const model = defaultLanguageModel();
  const generator = model
    ? {
        async generate(prompt: string) {
          const result = await getBirthTimeGuideAgent(model).generate([
            { role: "user", content: prompt },
          ]);
          return { text: result.text };
        },
      }
    : null;
  const guide = createBirthTimeGuideService({
    generator,
    loadCase: store.loadCase,
    proposeEvidenceDraft: actions.proposeEvidenceDraft,
  });

  try {
    switch (parsed.data.type) {
      case "render_question": {
        const response = await guide.renderQuestion(user.id, parsed.data.caseId);
        return NextResponse.json(response);
      }
      case "draft_evidence": {
        const response = await guide.draftEvidence(user.id, parsed.data);
        recordJourneyTransitionMetric(response.turn, "turn_advanced");
        return NextResponse.json(response);
      }
      default: {
        const exhaustive: never = parsed.data;
        return exhaustive;
      }
    }
  } catch (error) {
    if (error instanceof z.ZodError) {
      return NextResponse.json(
        { error: "生时引导输出无效", message: "请检查当前问题后重试。" },
        { status: 409 },
      );
    }
    if (error instanceof BirthTimeGuideActionError) {
      const status = error.reason === "case_not_found" ? 404 : 409;
      return NextResponse.json(
        { error: "当前步骤不可用", message: "请刷新并使用最新的生时校正步骤。" },
        { status },
      );
    }
    if (error instanceof StaleJourneyTurnError || error instanceof BirthTimeJourneyActionError) {
      return NextResponse.json(
        { error: "校正状态已更新", message: "请使用最新问题或草稿后重试。" },
        { status: 409 },
      );
    }
    if (error instanceof BirthTimeJourneyStoreError) {
      return NextResponse.json(
        { error: "生时引导暂时不可用", message: "当前资料已保留，请稍后重试。" },
        { status: 503 },
      );
    }
    throw error;
  }
}
