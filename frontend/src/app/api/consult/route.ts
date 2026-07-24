import { NextResponse } from "next/server";
import {
  consultationInputSchema,
  consultationWorkflowReceipt,
  getGeneralJyotishAgent,
  getJyotishAgent,
  runConsultationWorkflow,
} from "@/mastra";
import {
  languageModelConfigurationMessage,
  resolveLanguageModel,
} from "@/mastra/model";
import { blocksPromptExtraction } from "@/lib/consult-safety";
import {
  consultationEntrypointSchema,
  resolveConsultationQuestion,
} from "@/lib/consultation-entrypoint";
import { CreditRpcError, runCreditRpc } from "@/lib/consultation-billing";
import { reserveConsultationModel } from "@/lib/consultation-model-selection";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { streamTextResponse } from "@/lib/stream-text-response";
import {
  applyBirthTimeModeToWorkflowContext,
  consultationBirthTimeModeSchema,
  createBirthTimeModeOutputGuard,
  shouldRunBirthChartWorkflow,
  type ConsultationBirthTimeMode,
} from "@/lib/consultation-birth-time-mode";
import {
  ConsultationProfileTruthError,
  prepareConsultationRoute,
} from "@/lib/consultation-route-service";
import {
  createRectificationHandoffService,
  type RectificationHandoffExecution,
  type RectificationHandoffService,
} from "@/lib/rectification-handoff-service";
import { z } from "zod";

export const runtime = "nodejs";
export const maxDuration = 60;

const chatRequestMetadataSchema = z.object({
  requestId: z.string().uuid(),
  modelId: z.string().trim().min(1).max(64),
  name: z.string().trim().max(80).optional().default(""),
  history: z
    .array(
      z.object({
        role: z.enum(["user", "assistant"]),
        text: z.string().max(4000),
      }),
    )
    .max(20)
    .default([]),
});

const rectificationHandoffSchema = z.object({
  caseId: z.string().uuid(),
  turnVersion: z.number().int().nonnegative(),
  claimActionId: z.string().uuid(),
  requestId: z.string().uuid(),
}).strict();

const chartChatRequestSchema = consultationInputSchema.extend({
  ...chatRequestMetadataSchema.shape,
  consultationMode: consultationBirthTimeModeSchema.exclude(["general_no_birth_time"])
    .optional()
    .default("verified_chart"),
  entrypoint: consultationEntrypointSchema.optional(),
  rectificationHandoff: rectificationHandoffSchema.optional(),
}).strict();

const generalChatRequestSchema = z.object({
  ...chatRequestMetadataSchema.shape,
  consultationMode: z.literal("general_no_birth_time"),
  question: z.string().trim().min(1).max(500),
  theme: z.enum(["career", "marriage", "wealth", "timing", "general"]),
  entrypoint: z.undefined().optional(),
}).strict();

const chatRequestSchema = z.union([generalChatRequestSchema, chartChatRequestSchema]);

function currentTimeContext(now = new Date()) {
  const chinaTime = new Date(now.getTime() + 8 * 60 * 60 * 1000)
    .toISOString()
    .replace("T", " ")
    .slice(0, 19);
  return `服务端当前时间（权威）：${now.toISOString()}；中国标准时间（UTC+8）：${chinaTime}。涉及“现在、今天、今年、未来几个月”等相对时间时，以此为准。`;
}

function chinaCalendarDate(now: Date) {
  return new Date(now.getTime() + 8 * 60 * 60 * 1000).toISOString().slice(0, 10);
}

async function recordModelUsage(
  accounting: ReturnType<typeof createAdminSupabaseClient>,
  userId: string,
  requestId: string,
  modelId: string,
  usage: Promise<{ inputTokens?: number; outputTokens?: number }>,
) {
  try {
    const resolved = await usage;
    const { error } = await accounting
      .from("credit_transactions")
      .update({
        model: modelId,
        input_tokens: Math.max(0, Math.trunc(resolved.inputTokens ?? 0)),
        output_tokens: Math.max(0, Math.trunc(resolved.outputTokens ?? 0)),
      })
      .eq("user_id", userId)
      .eq("transaction_type", "reserve")
      .eq("request_id", requestId);

    if (error)
      console.warn(
        `[billing] unable to record model usage request=${requestId} model=${modelId}`,
      );
  } catch (error) {
    const reason = error instanceof Error ? error.name : "UnknownError";
    console.warn(
      `[billing] unable to read model usage request=${requestId} model=${modelId} reason=${reason}`,
    );
  }
}

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

  const {
    data: { user },
    error: authError,
  } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: "请先登录", message: "登录后才能开始咨询。" },
      { status: 401 },
    );
  }

  const parsed = chatRequestSchema.safeParse(
    await request.json().catch(() => null),
  );
  if (!parsed.success) {
    return NextResponse.json(
      { error: "出生资料或问题格式不正确", details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  if (parsed.data.entrypoint === "birth_time_rectification") {
    return NextResponse.json(
      {
        error: "旧版生时校正入口已停用",
        message: "请从首页生时校正卡片开始或继续对话式校正，本次不会扣点。",
      },
      { status: 409 },
    );
  }

  const requestTime = new Date();
  const resolvedQuestion = resolveConsultationQuestion({
    visibleQuestion: parsed.data.question,
    entrypoint: parsed.data.entrypoint,
    currentDate: chinaCalendarDate(requestTime),
  });

  const userId = user.id;
  const requestId = parsed.data.requestId;
  const handoff = "rectificationHandoff" in parsed.data
    ? parsed.data.rectificationHandoff
    : undefined;
  let handoffService: RectificationHandoffService | null = null;
  let handoffExecution: RectificationHandoffExecution | null = null;
  let handoffSettlement: Promise<void> | null = null;

  async function settleHandoff(emitted: boolean) {
    if (!handoff || !handoffService || !handoffExecution
      || handoffExecution.status !== "ready") return;
    handoffSettlement ??= handoffService.settle({
      userId,
      caseId: handoff.caseId,
      claimActionId: handoff.claimActionId,
      requestId: handoff.requestId,
      emitted,
    }).then(() => undefined);
    await handoffSettlement;
  }

  if (handoff) {
    if (!["verified_chart", "unverified_birth_time"].includes(parsed.data.consultationMode)
      || parsed.data.entrypoint !== undefined
      || requestId !== handoff.requestId) {
      return NextResponse.json(
        {
          error: "原问题交接请求不一致",
          message: "请刷新校正结果后重新点击继续，本次不会扣点。",
        },
        { status: 409 },
      );
    }
    try {
      handoffService = createRectificationHandoffService(accounting);
      handoffExecution = await handoffService.beginExecution({
        userId,
        caseId: handoff.caseId,
        turnVersion: handoff.turnVersion,
        claimActionId: handoff.claimActionId,
        requestId: handoff.requestId,
        question: parsed.data.question,
      });
    } catch {
      return NextResponse.json(
        {
          error: "原问题状态已经变化",
          message: "请刷新后查看最新状态，本次不会扣点。",
        },
        { status: 409 },
      );
    }
    if (handoffExecution.status !== "ready") {
      const consumed = handoffExecution.status === "consumed";
      return NextResponse.json(
        {
          error: consumed ? "原问题已经继续回答" : "原问题正在另一处继续",
          message: consumed
            ? "刷新后即可查看最新状态，不会再次扣点。"
            : "请等待当前回答完成后刷新，本次不会重复扣点。",
        },
        { status: consumed ? 410 : 409 },
      );
    }
  }

  const userControlledPrompt = [
    parsed.data.question,
    ...parsed.data.history
      .filter((message) => message.role === "user")
      .map((message) => message.text),
  ].join("\n");
  if (blocksPromptExtraction(userControlledPrompt)) {
    if (handoffExecution?.status === "ready") {
      try {
        await settleHandoff(false);
      } catch {
        return NextResponse.json(
          { error: "暂时无法释放原问题", message: "请稍后刷新状态。" },
          { status: 503 },
        );
      }
    }
    return NextResponse.json(
      {
        error: "无法处理该请求",
        message:
          "我不能提供系统提示词、技能原文或任何密钥。你可以继续询问占星相关问题。",
      },
      { status: 400 },
    );
  }
  let prepared;
  try {
    prepared = await prepareConsultationRoute({
      userId,
      mode: parsed.data.consultationMode,
      async loadProfile(profileUserId) {
        const { data, error } = await supabase
          .from("profiles")
          .select("name,birth_date,reported_birth_time,active_birth_time,birth_time_source,birth_time_status,country_code,province_code,city_code,district_code,latitude,longitude,timezone_offset,birth_place_label,birth_place_type,birth_place_provider,birth_place_provider_id,timezone_id,timezone_source")
          .eq("id", profileUserId)
          .single();
        if (error || !data) throw new ConsultationProfileTruthError("profile_unavailable");
        return data;
      },
      reserve: () => reserveConsultationModel(
        parsed.data.modelId,
        resolveLanguageModel,
        () => handoffExecution?.billingReused
          ? Promise.resolve({
            success: true,
            credits: handoffExecution.credits ?? null,
            error_code: null,
          })
          : runCreditRpc(
            accounting,
            "begin_consultation_credit",
            userId,
            requestId,
          ),
      ),
    });
  } catch (error) {
    if (handoffExecution?.status === "ready") {
      try {
        await settleHandoff(false);
      } catch {
        return NextResponse.json(
          {
            error: "暂时无法释放原问题",
            message: "请稍后刷新状态，本次不会重复扣点。",
          },
          { status: 503 },
        );
      }
    }
    if (error instanceof ConsultationProfileTruthError) {
      const modeChanged = error.code === "mode_changed";
      return NextResponse.json(
        modeChanged
          ? {
            error: "出生时间状态已经变化",
            message: "请刷新后重新选择使用填报时间、一般咨询或先完成校正，本次不会扣点。",
          }
          : {
            error: "暂时无法核对完整出生资料",
            message: "出生日期、时间来源或出生地点资料不完整或不一致，请重新保存后再试，本次不会扣点。",
          },
        { status: modeChanged ? 409 : 503 },
      );
    }
    const reason = error instanceof Error ? error.name : "UnknownError";
    console.error(
      `[billing] reservation failed request=${requestId} reason=${reason}`,
    );
    return NextResponse.json(
      { error: "暂时无法确认咨询点数", message: "请稍后重试。" },
      { status: 503 },
    );
  }

  const modelSelection = prepared.reservation;

  if (modelSelection.status === "unavailable") {
    if (handoffExecution?.status === "ready") {
      try {
        await settleHandoff(false);
      } catch {
        return NextResponse.json(
          { error: "暂时无法释放原问题", message: "请稍后刷新状态。" },
          { status: 503 },
        );
      }
    }
    return NextResponse.json(
      {
        error: "模型暂不可用",
        message: "请选择其他模型后重新发送，本次不会扣除点数。",
      },
      { status: 409 },
    );
  }

  const selectedModel = modelSelection.model;
  const reserveResult = modelSelection.reservation;

  if (!reserveResult.success) {
    if (handoffExecution?.status === "ready") {
      try {
        await settleHandoff(false);
      } catch {
        return NextResponse.json(
          { error: "暂时无法释放原问题", message: "请稍后刷新状态。" },
          { status: 503 },
        );
      }
    }
    const insufficient = reserveResult.error_code === "insufficient_credits";
    return NextResponse.json(
      {
        error: insufficient ? "咨询点数不足" : "暂时无法扣除咨询点数",
        message: insufficient
          ? "请先兑换咨询点数后再继续。"
          : reserveResult.error_code || "请稍后重试。",
      },
      { status: insufficient ? 402 : 503 },
    );
  }

  async function cancel() {
    if (handoffExecution?.status === "ready") {
      try {
        await settleHandoff(false);
      } catch (error) {
        const reason = error instanceof Error ? error.name : "UnknownError";
        console.error(
          `[billing] handoff release failed request=${requestId} reason=${reason}`,
        );
      }
      return;
    }
    try {
      await runCreditRpc(
        accounting,
        "cancel_consultation_credit",
        userId,
        requestId,
      );
    } catch (error) {
      const reason = error instanceof Error ? error.name : "UnknownError";
      console.error(
        `[billing] cancellation failed request=${requestId} reason=${reason}`,
      );
    }
  }

  async function complete() {
    if (handoffExecution?.status === "ready") {
      await settleHandoff(true);
      return;
    }
    const result = await runCreditRpc(
      accounting,
      "complete_consultation_credit",
      userId,
      requestId,
    );
    if (!result.success)
      throw new CreditRpcError(result.error_code || "completion_rejected");
  }

  let settlement: Promise<void> | null = null;
  function settle(action: () => Promise<void>) {
    settlement ??= action();
    return settlement;
  }

  try {
    const { history } = parsed.data;
    const name = prepared.serverChart?.name ?? parsed.data.name;
    const consultationMode: ConsultationBirthTimeMode = parsed.data.consultationMode;
    if (!shouldRunBirthChartWorkflow(consultationMode)) {
      const result = await getGeneralJyotishAgent(selectedModel).stream([
        {
          role: "user",
          content: [
            currentTimeContext(requestTime),
            name ? `用户称呼：${name}` : "",
            "当前是用户明确选择的无出生分钟一般咨询。不得计算或推断个人星盘；不得补 00:00、时段中点或任何候选分钟。",
            resolvedQuestion.modelQuestion,
          ].filter(Boolean).join("\n"),
        },
      ]);
      const completeAndRecordUsage = async () => {
        await complete();
        void recordModelUsage(
          accounting,
          userId,
          requestId,
          modelSelection.usageModelId,
          result.totalUsage,
        );
      };
      const settleInterrupted = (emitted: boolean) =>
        settle(emitted ? completeAndRecordUsage : cancel);
      return streamTextResponse(result.textStream, {
        transformText: createBirthTimeModeOutputGuard(consultationMode, false),
        mode: "mastra",
        requestId,
        headers: {
          "x-jyotish-workflow-route": "general-no-birth-time",
          "x-jyotish-workflow-status": "ready",
          "x-jyotish-technique-truth": "not-applicable",
          "x-jyotish-precise-timing": "blocked",
          "x-jyotish-missing-layers": "birth-minute",
          "x-jyotish-birth-time-mode": consultationMode,
        },
        ...(handoff ? { onFirstOutput: () => settle(completeAndRecordUsage) } : {}),
        onComplete: () => settle(completeAndRecordUsage),
        onError: (_error, emitted) => settleInterrupted(emitted),
        onCancel: settleInterrupted,
      });
    }

    if (!prepared.serverChart) throw new Error("server_chart_truth_missing");
    const toolInput = consultationInputSchema.parse({
      ...prepared.serverChart.toolInput,
      // Unverified use is still a normal chart calculation with a hard answer
      // boundary. It must never reactivate the retired rectification questionnaire.
      entryMode: "direct_chart",
      question: resolvedQuestion.modelQuestion,
      theme: parsed.data.theme,
    });
    const workflowContext = applyBirthTimeModeToWorkflowContext(
      await runConsultationWorkflow(toolInput),
      consultationMode,
    );
    const workflowReceipt = consultationWorkflowReceipt(workflowContext);

    const result = await getJyotishAgent(selectedModel, workflowContext).stream([
      ...history.map((message) => message.role === "user"
        ? { role: "user" as const, content: message.text }
        : { role: "assistant" as const, content: message.text }),
      {
        role: "user",
        content: [
          currentTimeContext(requestTime),
          name ? `用户称呼：${name}` : "",
          resolvedQuestion.modelQuestion,
          "\n需要查询星盘时，使用以下经过服务端校验的工具参数：",
          JSON.stringify(toolInput),
        ].filter(Boolean).join("\n"),
      },
    ]);
    const completeAndRecordUsage = async () => {
      await complete();
      void recordModelUsage(
        accounting,
        userId,
        requestId,
        modelSelection.usageModelId,
        result.totalUsage,
      );
    };
    const settleInterrupted = (emitted: boolean) =>
      settle(emitted ? completeAndRecordUsage : cancel);
    return streamTextResponse(result.textStream, {
      transformText: createBirthTimeModeOutputGuard(
        consultationMode,
        workflowReceipt.preciseTiming !== "blocked",
      ),
      mode: "mastra",
      requestId,
      headers: {
        "x-jyotish-workflow-route": workflowReceipt.route,
        "x-jyotish-workflow-status": workflowReceipt.status,
        "x-jyotish-technique-truth": workflowReceipt.techniqueTruth,
        "x-jyotish-precise-timing": workflowReceipt.preciseTiming,
        "x-jyotish-missing-layers": workflowReceipt.missingLayers,
        "x-jyotish-birth-time-mode": consultationMode,
      },
      ...(handoff ? { onFirstOutput: () => settle(completeAndRecordUsage) } : {}),
      onComplete: () => settle(completeAndRecordUsage),
      onError: (_error, emitted) => settleInterrupted(emitted),
      onCancel: settleInterrupted,
    });
  } catch (error) {
    await cancel();
    const reason = error instanceof Error ? error.name : "UnknownError";
    console.error(
      `[consult] generation failed request=${requestId} model=${modelSelection.usageModelId} reason=${reason}`,
    );
    return NextResponse.json(
      {
        error: "暂时无法生成解读",
        message: "咨询服务暂时不可用，请稍后再试。",
        recovery: languageModelConfigurationMessage()
          ? "当前没有可用的咨询模型，请联系管理员。"
          : "稍后重试，或换一个模型继续。",
      },
      { status: 503 },
    );
  }
}
