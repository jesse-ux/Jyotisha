import path from "node:path";
import { Agent } from "@mastra/core/agent";
import { defaultLanguageModel, resolveLanguageModel } from "@/mastra/model";
import type { CandidateSnapshot, LifeEventRevision, PendingEvidence, RectificationV4Case } from "../rectification-v4/contracts.ts";
import { publicMessageSchema, type PublicMessage, type ValidatedDecision } from "./contracts.ts";
import { recordRectificationAgentTelemetry } from "./telemetry.ts";

const skillPath = process.env.RECTIFICATION_SKILL_PATH?.trim() || path.resolve(process.cwd(), "..", "skills", "birth-time-rectification");
const agents = new Map<string, Agent>();
function agentFor(modelId: string | null): { id: string; agent: Agent } | null {
  const selected = (modelId ? resolveLanguageModel(modelId) : null) ?? defaultLanguageModel();
  if (!selected) return null;
  const cached = agents.get(selected.id);
  if (cached) return { id: selected.id, agent: cached };
  const agent = new Agent({
    id: `rectification-v5-renderer-${selected.id}`, name: "Birth Time Rectification Response Renderer", model: selected.model, skills: [skillPath],
    instructions: "Write concise natural Simplified Chinese. Acknowledge the latest experience, state uncertainty honestly, and never expose ids, scores, internal domains, representative minutes, model/tool details, or claim an exact birth minute. Return strict JSON only.",
  });
  agents.set(selected.id, agent);
  return { id: selected.id, agent };
}

function deterministic(input: { latestAnswer: string; acceptedEvents: readonly LifeEventRevision[]; pendingEvidence: readonly PendingEvidence[]; snapshot: CandidateSnapshot | null; validated: ValidatedDecision }): PublicMessage {
  const latest = input.acceptedEvents.at(-1);
  const acknowledgement = latest
    ? `我记下了你提到的“${latest.summary}”，并保留了你给出的时间精度。`
    : input.pendingEvidence.length
      ? "我保留了你刚才的原始描述；其中的日期或事件关系还不能安全进入评分。"
      : input.latestAnswer
        ? "我保留了你刚才的原始描述；目前还没有足够明确的新日期可以直接进入评分。"
        : "我会继续根据已确认的人生事件比较候选范围。";
  const primary = input.snapshot?.clusters[0];
  const candidateUpdate = primary ? `目前较集中的候选仍是 ${primary.startTime}–${primary.endTime}；这只是待验证范围，不代表其中某一分钟已被确认。` : null;
  const limitation = input.validated.decision.action === "stop_low_confidence" ? "现有证据不足以安全缩小范围，我不会把不稳定结果包装成确定时间。" : null;
  return { acknowledgement, candidateUpdate, limitation, question: input.validated.selectedOpportunity?.prompt ?? null };
}

export function enforceServerQuestion(value: unknown, question: string | null): PublicMessage {
  return { ...publicMessageSchema.parse(value), question };
}

export async function renderPublicTurn(input: Readonly<{
  caseValue: RectificationV4Case; latestAnswer: string; acceptedEvents: readonly LifeEventRevision[];
  pendingEvidence: readonly PendingEvidence[]; snapshot: CandidateSnapshot | null; validated: ValidatedDecision; timeoutMs?: number;
}>): Promise<PublicMessage> {
  const started = Date.now();
  const deploymentSha = process.env.DEPLOYMENT_SHA?.trim() || null;
  const fallback = deterministic(input);
  const selected = agentFor(input.caseValue.narrationModelId);
  if (!selected) {
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "fallback", outcome: "succeeded", modelId: input.caseValue.narrationModelId, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: "renderer_model_unavailable", deploymentSha });
    return fallback;
  }
  recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "renderer", outcome: "started", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: null, errorCode: null, deploymentSha });
  try {
    const result = await selected.agent.generate(JSON.stringify({
      task: "Render the public turn. The server-owned question must not be changed.", latestAnswer: input.latestAnswer,
      acceptedEvents: input.acceptedEvents.slice(-3).map((event) => ({ summary: event.summary, date: event.dateRange.label, subject: event.subject })),
      pendingEvidence: input.pendingEvidence.slice(-3).map((event) => ({ rawText: event.rawText, reasonCode: event.reasonCode })),
      candidateRange: input.snapshot?.clusters[0] ? { start: input.snapshot.clusters[0].startTime, end: input.snapshot.clusters[0].endTime } : null,
      action: input.validated.decision.action, exactQuestion: input.validated.selectedOpportunity?.prompt ?? null,
    }), { abortSignal: AbortSignal.timeout(input.timeoutMs ?? 15_000), structuredOutput: { schema: publicMessageSchema, jsonPromptInjection: "inline" } });
    const message = enforceServerQuestion(result.object, input.validated.selectedOpportunity?.prompt ?? null);
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "renderer", outcome: "succeeded", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: null, deploymentSha });
    return message;
  } catch {
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "renderer", outcome: "failed", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: "renderer_failed", deploymentSha });
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "fallback", outcome: "succeeded", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: "renderer_failed", deploymentSha });
    return fallback;
  }
}
