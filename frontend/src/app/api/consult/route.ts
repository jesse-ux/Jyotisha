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
import { createAdminSupabaseClient } from "@/lib/supabase/admin";
import { createServerSupabaseClient } from "@/lib/supabase/server";
import { z } from "zod";

export const runtime = "nodejs";
export const maxDuration = 60;

const chatRequestSchema = consultationInputSchema.extend({
  name: z.string().trim().max(80).optional().default(""),
  history: z.array(z.object({
    role: z.enum(["user", "assistant"]),
    text: z.string().max(4000),
  })).max(20).default([]),
});

type StreamHooks = {
  onComplete?: () => Promise<void>;
  onError?: (error: unknown) => Promise<void>;
};

type CreditRpcResult = {
  success?: boolean;
  credits?: number;
  error_code?: string;
};

function currentTimeContext(now = new Date()) {
  const chinaTime = new Date(now.getTime() + 8 * 60 * 60 * 1000)
    .toISOString()
    .replace("T", " ")
    .slice(0, 19);
  return `服务端当前时间（权威）：${now.toISOString()}；中国标准时间（UTC+8）：${chinaTime}。涉及“现在、今天、今年、未来几个月”等相对时间时，以此为准。`;
}

function streamTextResponse(
  stream: AsyncIterable<string>,
  mode: "engine" | "mastra",
  hooks: StreamHooks = {},
) {
  const iterator = stream[Symbol.asyncIterator]();
  const encoder = new TextEncoder();
  let settled = false;
  let emitted = false;

  const body = new ReadableStream<Uint8Array>({
    async pull(controller) {
      try {
        const { done, value } = await iterator.next();
        if (done) {
          settled = true;
          if (!emitted) {
            const error = new Error("empty_stream");
            await hooks.onError?.(error);
            controller.error(error);
            return;
          }
          await hooks.onComplete?.();
          controller.close();
          return;
        }
        if (/\S/.test(value)) emitted = true;
        controller.enqueue(encoder.encode(value));
      } catch (error) {
        if (!settled) {
          settled = true;
          await hooks.onError?.(error);
        }
        controller.error(error);
      }
    },
    async cancel() {
      const refundBeforeOutput = !settled && !emitted;
      settled = true;
      try {
        await iterator.return?.();
      } finally {
        if (refundBeforeOutput) {
          await hooks.onError?.(new Error("stream_cancelled_before_output"));
        }
      }
    },
  });

  return new Response(body, {
    headers: {
      "cache-control": "no-cache, no-transform",
      "content-type": "text/plain; charset=utf-8",
      "x-accel-buffering": "no",
      "x-ayanam-mode": mode,
    },
  });
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
  const requestId = crypto.randomUUID();
  let refunded = false;
  let refundInFlight: Promise<void> | null = null;

  async function performRefund() {
    if (refunded) return;
    if (refundInFlight) return refundInFlight;

    refundInFlight = (async () => {
      let lastError = "unknown_refund_error";
      for (let attempt = 1; attempt <= 3; attempt += 1) {
        try {
          const { data, error } = await accounting.rpc("refund_credit", {
            p_user_id: userId,
            p_request_id: requestId,
          });
          const result = Array.isArray(data) ? data[0] : data;
          if (!error && result?.success) {
            refunded = true;
            return;
          }
          lastError = error?.message || result?.error_code || "refund_rejected";
        } catch (error) {
          lastError = error instanceof Error ? error.message : "refund_request_failed";
        }

        if (attempt < 3) {
          await new Promise((resolve) => setTimeout(resolve, attempt * 150));
        }
      }
      console.error(`[billing] refund failed for ${requestId}: ${lastError}`);
    })();

    try {
      await refundInFlight;
    } finally {
      refundInFlight = null;
    }
  }

  async function refund() {
    await performRefund();
  }

  let reserveResult: CreditRpcResult | null = null;
  let reserveErrorMessage = "";
  for (let attempt = 1; attempt <= 3; attempt += 1) {
    try {
      const { data, error } = await accounting.rpc("reserve_credit", {
        p_user_id: userId,
        p_request_id: requestId,
      });
      const result = (Array.isArray(data) ? data[0] : data) as CreditRpcResult | null;
      if (!error && result) {
        reserveResult = result;
        break;
      }
      reserveErrorMessage = error?.message || "empty_reservation_response";
    } catch (error) {
      reserveErrorMessage = error instanceof Error ? error.message : "reservation_request_failed";
    }

    if (attempt < 3) {
      await new Promise((resolve) => setTimeout(resolve, attempt * 150));
    }
  }

  if (!reserveResult) {
    await performRefund();
    return NextResponse.json(
      { error: "暂时无法确认咨询点数", message: reserveErrorMessage || "请稍后重试。" },
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

  try {
    const { history, name, ...toolInput } = parsed.data;

    if (!languageModelSettings.configured) {
      const evidence = await runConsultationWorkflow(toolInput);
      return streamTextResponse(staticTextStream(engineSummary(evidence)), "engine", {
        onError: refund,
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
    return streamTextResponse(result.textStream, "mastra", {
      onComplete: () => recordModelUsage(accounting, userId, requestId, result.totalUsage),
      onError: refund,
    });
  } catch (error) {
    await refund();
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
