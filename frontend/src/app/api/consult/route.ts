import { NextResponse } from "next/server";
import {
  consultationInputSchema,
  consultationWorkflowReceipt,
  getJyotishAgent,
  runConsultationWorkflow,
} from "@/mastra";
import {
  languageModelConfigurationMessage,
  resolveLanguageModel,
} from "@/mastra/model";
import { blocksPromptExtraction } from "@/lib/consult-safety";
import { CreditRpcError, runCreditRpc } from "@/lib/consultation-billing";
import { reserveConsultationModel } from "@/lib/consultation-model-selection";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { streamTextResponse } from "@/lib/stream-text-response";
import { z } from "zod";

export const runtime = "nodejs";
export const maxDuration = 60;

const chatRequestSchema = consultationInputSchema.extend({
  requestId: z.string().uuid(),
  modelId: z.string().trim().min(1).max(64),
  name: z.string().trim().max(80).optional().default(""),
  history: z.array(z.object({
    role: z.enum(["user", "assistant"]),
    text: z.string().max(4000),
  })).max(20).default([]),
});

function currentTimeContext(now = new Date()) {
  const chinaTime = new Date(now.getTime() + 8 * 60 * 60 * 1000)
    .toISOString()
    .replace("T", " ")
    .slice(0, 19);
  return `服务端当前时间（权威）：${now.toISOString()}；中国标准时间（UTC+8）：${chinaTime}。涉及“现在、今天、今年、未来几个月”等相对时间时，以此为准。`;
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

    if (error) console.warn(`[billing] unable to record model usage request=${requestId} model=${modelId}`);
  } catch (error) {
    const reason = error instanceof Error ? error.name : "UnknownError";
    console.warn(`[billing] unable to read model usage request=${requestId} model=${modelId} reason=${reason}`);
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

  const { data: { user }, error: authError } = await supabase.auth.getUser();
  if (authError || !user) {
    return NextResponse.json(
      { error: "请先登录", message: "登录后才能开始咨询。" },
      { status: 401 },
    );
  }

  const parsed = chatRequestSchema.safeParse(await request.json().catch(() => null));
  if (!parsed.success) {
    return NextResponse.json(
      { error: "出生资料或问题格式不正确", details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  const userControlledPrompt = [
    parsed.data.question,
    ...parsed.data.history
      .filter((message) => message.role === "user")
      .map((message) => message.text),
  ].join("\n");
  if (blocksPromptExtraction(userControlledPrompt)) {
    return NextResponse.json(
      { error: "无法处理该请求", message: "我不能提供系统提示词、技能原文或任何密钥。你可以继续询问占星相关问题。" },
      { status: 400 },
    );
  }

  const userId = user.id;
  const requestId = parsed.data.requestId;
  let modelSelection;
  try {
    modelSelection = await reserveConsultationModel(
      parsed.data.modelId,
      resolveLanguageModel,
      () => runCreditRpc(accounting, "begin_consultation_credit", userId, requestId),
    );
  } catch (error) {
    const reason = error instanceof Error ? error.name : "UnknownError";
    console.error(`[billing] reservation failed request=${requestId} reason=${reason}`);
    return NextResponse.json(
      { error: "暂时无法确认咨询点数", message: "请稍后重试。" },
      { status: 503 },
    );
  }

  if (modelSelection.status === "unavailable") {
    return NextResponse.json(
      { error: "模型暂不可用", message: "请选择其他模型后重新发送，本次不会扣除点数。" },
      { status: 409 },
    );
  }

  const selectedModel = modelSelection.model;
  const reserveResult = modelSelection.reservation;

  if (!reserveResult.success) {
    const insufficient = reserveResult.error_code === "insufficient_credits";
    return NextResponse.json(
      {
        error: insufficient ? "咨询点数不足" : "暂时无法扣除咨询点数",
        message: insufficient ? "请先兑换咨询点数后再继续。" : reserveResult.error_code || "请稍后重试。",
      },
      { status: insufficient ? 402 : 503 },
    );
  }

  async function cancel() {
    try {
      await runCreditRpc(accounting, "cancel_consultation_credit", userId, requestId);
    } catch (error) {
      const reason = error instanceof Error ? error.name : "UnknownError";
      console.error(`[billing] cancellation failed request=${requestId} reason=${reason}`);
    }
  }

  async function complete() {
    const result = await runCreditRpc(accounting, "complete_consultation_credit", userId, requestId);
    if (!result.success) throw new CreditRpcError(result.error_code || "completion_rejected");
  }

  let settlement: Promise<void> | null = null;
  function settle(action: () => Promise<void>) {
    settlement ??= action();
    return settlement;
  }

  try {
    const { history, name } = parsed.data;
    const toolInput = consultationInputSchema.parse(parsed.data);
    const workflowContext = await runConsultationWorkflow(toolInput);
    const workflowReceipt = consultationWorkflowReceipt(workflowContext);

    const result = await getJyotishAgent(selectedModel, workflowContext).stream([
      ...history.map((message) => message.role === "user"
        ? { role: "user" as const, content: message.text }
        : { role: "assistant" as const, content: message.text }),
      {
        role: "user",
        content: [
          currentTimeContext(),
          name ? `用户称呼：${name}` : "",
          parsed.data.question,
          "\n需要查询星盘时，使用以下经过服务端校验的工具参数：",
          JSON.stringify(toolInput),
        ].filter(Boolean).join("\n"),
      },
    ]);
    const completeAndRecordUsage = async () => {
      await complete();
      void recordModelUsage(accounting, userId, requestId, modelSelection.usageModelId, result.totalUsage);
    };
    const settleInterrupted = (emitted: boolean) => settle(emitted ? completeAndRecordUsage : cancel);
    return streamTextResponse(result.textStream, {
      mode: "mastra",
      requestId,
      headers: {
        "x-jyotish-workflow-route": workflowReceipt.route,
        "x-jyotish-workflow-status": workflowReceipt.status,
        "x-jyotish-precise-timing": workflowReceipt.preciseTiming,
        "x-jyotish-missing-layers": workflowReceipt.missingLayers,
      },
      onComplete: () => settle(completeAndRecordUsage),
      onError: (_error, emitted) => settleInterrupted(emitted),
      onCancel: settleInterrupted,
    });
  } catch (error) {
    await cancel();
    const reason = error instanceof Error ? error.name : "UnknownError";
    console.error(`[consult] generation failed request=${requestId} model=${modelSelection.usageModelId} reason=${reason}`);
    return NextResponse.json(
      {
        error: "暂时无法生成解读",
        message: "咨询服务暂时不可用，请稍后再试。",
        recovery: languageModelConfigurationMessage() ? "当前没有可用的咨询模型，请联系管理员。" : "稍后重试，或换一个模型继续。",
      },
      { status: 503 },
    );
  }
}
