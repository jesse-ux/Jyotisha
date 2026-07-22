import { z } from "zod";

const chatMessageSchema = z.object({
  role: z.enum(["user", "assistant"]),
  text: z.string().max(100_000),
  suggestions: z.array(z.string().max(200)).max(3).optional(),
  techniqueTruth: z.string().max(120).optional(),
  workflowReceipt: z.object({
    route: z.string().max(120),
    status: z.string().max(120),
    preciseTiming: z.string().max(120),
    missingLayers: z.array(z.string().max(120)).max(30),
  }).strict().optional(),
}).strict();

export const chatSessionWriteSchema = z.object({
  title: z.string().trim().min(1).max(160),
  theme: z.enum(["career", "marriage", "wealth", "timing", "general"]),
  model_id: z.string().trim().min(1).max(64),
  messages: z.array(chatMessageSchema).max(500),
  session_type: z.enum(["consultation", "birth_time_rectification"]),
  rectification_case_id: z.string().uuid().nullable(),
  updated_at: z.string().datetime(),
}).strict();

export const chatSessionCreateSchema = chatSessionWriteSchema.extend({
  id: z.string().uuid(),
}).strict();

export type ChatSessionWrite = Readonly<{
  title: string;
  theme: "career" | "marriage" | "wealth" | "timing" | "general";
  model_id: string;
  messages: readonly Readonly<{
    role: "user" | "assistant";
    text: string;
    suggestions?: readonly string[];
    techniqueTruth?: string;
    workflowReceipt?: Readonly<{
      route: string;
      status: string;
      preciseTiming: string;
      missingLayers: readonly string[];
    }>;
  }>[];
  session_type: "consultation" | "birth_time_rectification";
  rectification_case_id: string | null;
  updated_at: string;
}>;

function retryableStatus(status: number) {
  return status === 408 || status === 429 || status >= 500;
}

class TerminalChatSessionWriteError extends Error {}

export async function writeChatSession(
  id: string,
  values: ChatSessionWrite,
  mode: "create" | "update",
  fetcher: typeof fetch = fetch,
): Promise<void> {
  const url = mode === "create" ? "/api/sessions" : `/api/sessions/${encodeURIComponent(id)}`;
  const body = mode === "create" ? { id, ...values } : values;
  let lastError = "云端同步暂时不可用";
  for (let attempt = 0; attempt < 2; attempt += 1) {
    try {
      const response = await fetcher(url, {
        method: mode === "create" ? "POST" : "PATCH",
        headers: { "content-type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify(body),
      });
      const payload = await response.json().catch(() => null) as { error?: string } | null;
      if (response.ok) return;
      lastError = payload?.error || "云端同步暂时不可用";
      if (!retryableStatus(response.status)) throw new TerminalChatSessionWriteError(lastError);
    } catch (error) {
      if (error instanceof TerminalChatSessionWriteError) throw error;
      lastError = error instanceof TypeError
        ? "网络暂时不可用，云端记录尚未更新"
        : error instanceof Error ? error.message : lastError;
    }
    if (attempt === 0) await new Promise((resolve) => setTimeout(resolve, 250));
  }
  throw new Error(lastError);
}
