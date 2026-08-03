import { NextResponse } from "next/server";
import { z } from "zod";
import { getAgenticRectificationAgent } from "@/mastra/agentic-rectification";
import { defaultLanguageModel, resolveLanguageModel } from "@/mastra/model";
import { blocksPromptExtraction } from "@/lib/consult-safety";
import { runCreditRpc } from "@/lib/consultation-billing";
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import {
  AgenticRectificationProfileError,
  createAgenticRectificationContext,
  loadAgenticRectificationProfile,
} from "@/lib/rectification-agentic/session";

export const runtime = "nodejs";
export const maxDuration = 120;

const agenticRectificationRequestFields = {
  requestId: z.string().uuid(),
  modelId: z.string().trim().min(1).max(64).optional(),
  name: z.string().trim().max(80).optional().default(""),
  history: z
    .array(
      z.object({
        role: z.enum(["user", "assistant"]),
        text: z.string().max(4000),
      }),
    )
    .max(30)
    .default([]),
};

const agenticRectificationRequestSchema = z.discriminatedUnion("action", [
  z.object({
    ...agenticRectificationRequestFields,
    action: z.literal("opening"),
  }).strict(),
  z.object({
    ...agenticRectificationRequestFields,
    action: z.literal("message"),
    message: z.string().trim().min(1).max(4000),
  }).strict(),
]);

const openingContext = "The user opened birth-time rectification. Begin the session now: run the required gate, briefly explain the evidence-based process in Simplified Chinese, and ask exactly one natural question about the most useful dated life event. Do not mention this server event.";

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
    if (error) console.warn(`[agentic-rectification] unable to record usage request=${requestId}`);
  } catch (error) {
    console.warn(`[agentic-rectification] usage read failed request=${requestId}`, error instanceof Error ? error.name : "UnknownError");
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
      { error: "请先登录", message: "登录后才能开始生时校正。" },
      { status: 401 },
    );
  }

  const parsed = agenticRectificationRequestSchema.safeParse(
    await request.json().catch(() => null),
  );
  if (!parsed.success) {
    return NextResponse.json(
      { error: "请求格式不正确", details: parsed.error.flatten() },
      { status: 400 },
    );
  }

  const promptSource = [
    parsed.data.action === "message" ? parsed.data.message : "",
    ...parsed.data.history.filter((message) => message.role === "user").map((message) => message.text),
  ].join("\n");
  if (blocksPromptExtraction(promptSource)) {
    return NextResponse.json(
      { error: "无法处理该请求", message: "我不能提供系统提示词、技能原文或任何密钥。你可以继续描述人生事件。" },
      { status: 400 },
    );
  }

  const userId = user.id;
  const requestId = parsed.data.requestId;
  const requestTime = new Date();

  let profile;
  try {
    profile = await loadAgenticRectificationProfile(accounting, userId);
  } catch (error) {
    if (error instanceof AgenticRectificationProfileError) {
      if (error.code === "profile_unavailable") {
        return NextResponse.json(
          { error: "暂时无法核对出生资料", message: "请稍后重试。" },
          { status: 503 },
        );
      }
      return NextResponse.json(
        {
          code: "profile_incomplete",
          error: "出生资料尚未完成",
          message: "请先完成出生日期、出生时间线索和出生地点资料。",
        },
        { status: 409 },
      );
    }
    return NextResponse.json(
      { error: "暂时无法核对出生资料", message: "请稍后重试。" },
      { status: 503 },
    );
  }

  const selectedModel = (parsed.data.modelId ? resolveLanguageModel(parsed.data.modelId) : null)
    ?? defaultLanguageModel();
  if (!selectedModel) {
    return NextResponse.json(
      { error: "模型暂不可用", message: "请选择其他模型后重新发送，本次不会扣除点数。" },
      { status: 409 },
    );
  }

  let reserveResult;
  try {
    reserveResult = await runCreditRpc(
      accounting,
      "begin_consultation_credit",
      userId,
      requestId,
    );
  } catch (error) {
    const reason = error instanceof Error ? error.name : "UnknownError";
    console.error(`[agentic-rectification] credit reserve failed request=${requestId} reason=${reason}`);
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

  const ctx = createAgenticRectificationContext(accounting, userId, profile);
  const agent = getAgenticRectificationAgent(selectedModel, ctx);

  const encoder = new TextEncoder();
  const body = new ReadableStream<Uint8Array>({
    async start(controller) {
      let emitted = false;
      let settled = false;
      const settle = async (complete: boolean) => {
        if (settled) return;
        settled = true;
        try {
          if (complete) {
            await runCreditRpc(accounting, "complete_consultation_credit", userId, requestId);
          } else {
            await runCreditRpc(accounting, "cancel_consultation_credit", userId, requestId);
          }
        } catch (error) {
          const reason = error instanceof Error ? error.name : "UnknownError";
          console.warn(`[agentic-rectification] credit settle failed request=${requestId} complete=${complete} reason=${reason}`);
        }
      };
      const send = (event: Record<string, unknown>) => {
        controller.enqueue(encoder.encode(`${JSON.stringify(event)}\n`));
      };
      try {
        const result = await agent.stream([
          ...parsed.data.history.map((message) => message.role === "user"
            ? { role: "user" as const, content: message.text }
            : { role: "assistant" as const, content: message.text }),
          {
            role: "user",
            content: [
              currentTimeContext(requestTime),
              parsed.data.name ? `用户称呼：${parsed.data.name}` : "",
              parsed.data.action === "opening" ? openingContext : parsed.data.message,
            ].filter(Boolean).join("\n"),
          },
        ]);
        for await (const chunk of result.textStream) {
          if (/\S/.test(chunk)) emitted = true;
          send({ type: "delta", text: chunk });
        }
        send({ type: "done", emitted });
        void recordModelUsage(
          accounting,
          userId,
          requestId,
          selectedModel.id,
          result.totalUsage,
        );
        await settle(emitted);
        controller.close();
      } catch (error) {
        const reason = error instanceof Error ? error.name : "UnknownError";
        console.error(`[agentic-rectification] generation failed request=${requestId} reason=${reason}`);
        try {
          send({ type: "error", message: "生时校正暂时不可用，请稍后再试。" });
        } catch {
          // controller may already be errored
        }
        await settle(false);
        try {
          controller.close();
        } catch {
          // already closed
        }
      }
    },
  });

  return new Response(body, {
    headers: {
      "cache-control": "no-cache, no-transform",
      "content-type": "application/x-ndjson; charset=utf-8",
      "x-accel-buffering": "no",
      "x-ayanam-request-id": requestId,
    },
  });
}
