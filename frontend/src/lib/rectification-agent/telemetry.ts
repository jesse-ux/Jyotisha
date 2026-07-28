import { z } from "zod";

const telemetryEventSchema = z.object({
  caseId: z.string().uuid().nullable(),
  phase: z.enum(["reasoner", "renderer", "tool", "fallback"]),
  outcome: z.enum(["started", "succeeded", "failed", "rejected"]),
  modelId: z.string().trim().min(1).max(120).nullable(),
  toolName: z.string().trim().min(1).max(120).nullable(),
  decisionAction: z.string().trim().min(1).max(80).nullable(),
  durationMs: z.number().int().min(0).max(300_000).nullable(),
  errorCode: z.string().trim().min(1).max(120).nullable(),
  deploymentSha: z.string().trim().min(1).max(80).nullable(),
}).strict();

export type RectificationAgentTelemetryEvent = z.infer<typeof telemetryEventSchema>;

export function recordRectificationAgentTelemetry(
  event: RectificationAgentTelemetryEvent,
): void {
  const parsed = telemetryEventSchema.safeParse(event);
  if (!parsed.success) return;
  const line = JSON.stringify({
    ...parsed.data,
    component: "rectification-agent",
    at: new Date().toISOString(),
  });
  if (parsed.data.outcome === "failed" || parsed.data.outcome === "rejected") {
    console.warn(`[rectification-agent] ${line}`);
  } else {
    console.info(`[rectification-agent] ${line}`);
  }
}
