import { NextResponse } from "next/server";
import {
  consultationInputSchema,
  jyotishAgent,
  runConsultationWorkflow,
} from "@/mastra";
import {
  languageModelConfigurationMessage,
  languageModelSettings,
} from "@/mastra/model";
import { blocksPromptExtraction } from "@/lib/consult-safety";
import { CreditRpcError, runCreditRpc } from "@/lib/consultation-billing";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { streamTextResponse } from "@/lib/stream-text-response";
import { z } from "zod";

export const runtime = "nodejs";
export const maxDuration = 60;

const chatRequestSchema = consultationInputSchema.extend({
  requestId: z.string().uuid(),
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

async function* staticTextStream(text: string) {
  yield text;
}

function engineSummary(data: Record<string, unknown>) {
  const topics = Array.isArray(data.guided_topics) ? data.guided_topics : [];
  const routing = data.routing && typeof data.routing === "object" ? data.routing : {};
  const route = "primary_route" in routing ? String(routing.primary_route) : "统一咨询工作流";
  const topicText = topics
    .slice(0, 3)
    .map((item) => {
      if (!item || typeof item !== "object") return null;
      const record = item as Record<string, unknown>;
      return String(record.title || record.label || record.theme || "值得继续探索的主题");
    })
    .filter(Boolean);

  return [
    "星盘计算已完成，但当前没有配置 AI 模型，因此先返回引擎摘要。",
    `本次路由：${route}。`,
    topicText.length ? `建议继续查看：${topicText.join("、")}。` : "可继续查看事业、关系与年度时间窗口。",
    "启动 AI 解读需配置模型；原始计算结果已保留。",
  ].join("\n");
}

function configuredModelId() {
  if (languageModelSettings.mode === "compatible") {
    return process.env.LLM_MODEL?.trim() || "third-party";
  }
  return process.env.MASTRA_MODEL?.trim() || "openai/gpt-5-mini";
}

async function recordModelUsage(
  accounting: ReturnType<typeof createAdminSupabaseClient>,
  userId: string,
  requestId: string,
  usage: Promise<{ inputTokens?: number; outputTokens?: number }>,
) {
  try {
    const resolved = await usage;
    const { error } = await accounting
      .from("credit_transactions")
      .update({
        model: configuredModelId(),
        input_tokens: Math.max(0, Math.trunc(resolved.inputTokens ?? 0)),
        output_tokens: Math.max(0, Math.trunc(resolved.outputTokens ?? 0)),
      })
      .eq("user_id", userId)
      .eq("transaction_type", "reserve")
      .eq("request_id", requestId);

    if (error) console.warn("[billing] unable to record model usage", error.message);
  } catch (error) {
    console.warn("[billing] unable to read model usage", error);
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
  let reserveResult;
  try {
    reserveResult = await runCreditRpc(accounting, "begin_consultation_credit", userId, requestId);
  } catch (error) {
    console.error(`[billing] reservation failed for ${requestId}`, error);
    return NextResponse.json(
      { error: "暂时无法确认咨询点数", message: "请稍后重试。" },
      { status: 503 },
    );
  }

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
      console.error(`[billing] cancellation failed for ${requestId}`, error);
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

    if (!languageModelSettings.configured) {
      const evidence = await runConsultationWorkflow(toolInput);
      return streamTextResponse(staticTextStream(engineSummary(evidence)), {
        mode: "engine",
        requestId,
        onComplete: () => settle(complete),
        onError: (_error, emitted) => settle(emitted ? complete : cancel),
        onCancel: (emitted) => settle(emitted ? complete : cancel),
      });
    }

    const result = await jyotishAgent.stream([
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
      void recordModelUsage(accounting, userId, requestId, result.totalUsage);
    };
    const settleInterrupted = (emitted: boolean) => settle(emitted ? completeAndRecordUsage : cancel);
    return streamTextResponse(result.textStream, {
      mode: "mastra",
      requestId,
      onComplete: () => settle(completeAndRecordUsage),
      onError: (_error, emitted) => settleInterrupted(emitted),
      onCancel: settleInterrupted,
    });
  } catch (error) {
    await cancel();
    const message = error instanceof Error ? error.message : "咨询服务暂时不可用";
    return NextResponse.json(
      {
        error: "暂时无法生成解读",
        message,
        recovery: `请确认 Python API 已运行，并检查 JYOTISH_API_BASE 与模型配置。${languageModelConfigurationMessage() ? ` ${languageModelConfigurationMessage()}` : ""}`,
      },
      { status: 503 },
    );
  }
}
