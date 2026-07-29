import path from "node:path";
import { Agent } from "@mastra/core/agent";
import { createTool } from "@mastra/core/tools";
import { z } from "zod";
import { defaultLanguageModel, resolveLanguageModel } from "@/mastra/model";
import type { CandidateSnapshot, LifeEventRevision, PendingEvidence, RectificationV4Case, RectificationV4Turn } from "../rectification-v4/contracts.ts";
import { chronologicalEvents } from "../rectification-v4/evidence-ledger.ts";
import type { TargetDisposition } from "../rectification-v4/extraction.ts";
import { deterministicDecision } from "./fallback-policy.ts";
import { recordRectificationAgentTelemetry } from "./telemetry.ts";
import {
  rectificationDecisionSchema,
  rectificationDiagnosticSchema,
  type DiagnosticsSummary,
  type QuestionOpportunity,
  type RectificationDecision,
  type RectificationDiagnostic,
  type ToolCallTrace,
} from "./contracts.ts";

const skillPath = process.env.RECTIFICATION_SKILL_PATH?.trim() || path.resolve(process.cwd(), "..", "skills", "birth-time-rectification");
type Usage = Readonly<{ inputTokens?: number; outputTokens?: number }>;
type GeneratedDecision = Readonly<{
  object: unknown;
  totalUsage?: Usage | Promise<Usage>;
  reasoningSummary?: string | null;
  reasoningSource?: "provider_summary" | null;
}>;
export type RectificationReasonerGenerator = (
  prompt: string,
  phase: "initial" | "after_diagnostic",
) => Promise<GeneratedDecision>;

const unsafeReasoningPattern = /(?:[0-9a-f]{8}-[0-9a-f-]{27,}|(?:[01]\d|2[0-3]):[0-5]\d|(?:凌晨|清晨|上午|中午|下午|傍晚|晚上)?[零〇一二两三四五六七八九十百\d]{1,4}[点时](?:[零〇一二两三四五六七八九十百\d]{1,4}分?)?|opportunity(?:id)?|snapshot(?:id)?|event(?:id)?|tool[ _-]?call|score|diagnostic|rule[ _-]?id|贡献矩阵|内部字段|权重|保留率|比例|百分之|分数|得分|阈值|边际|cluster|D\d{1,2})/iu;

function compactText(value: string): string {
  return value.replace(/\s+/gu, "").toLocaleLowerCase();
}

export function sanitizeReasoningSummary(value: unknown, sensitiveTexts: readonly string[] = []): string | null {
  if (typeof value !== "string") return null;
  const text = value.replace(/\s+/gu, " ").trim();
  if (!text || unsafeReasoningPattern.test(text)) return null;
  const compact = compactText(text);
  for (const sensitiveText of sensitiveTexts) {
    const source = compactText(sensitiveText);
    if (source.length < 2) continue;
    const overlapLength = Math.min(4, source.length);
    for (let index = 0; index <= source.length - overlapLength; index += 1) {
      if (compact.includes(source.slice(index, index + overlapLength))) return null;
    }
  }
  const sentences = text.match(/[^。！？!?]+[。！？!?]?/gu)?.slice(0, 2).join("").trim() ?? text;
  return sentences.slice(0, 240).trim() || null;
}

function diagnosticPayload(diagnostic: RectificationDiagnostic, summary: DiagnosticsSummary) {
  switch (diagnostic) {
    case "leave_one_event_out": return { retentionRate: summary.leaveOneEventOutRetentionRate, unstableEventIds: summary.unstableEventIds };
    case "leave_one_domain_out": return { retentionRate: summary.leaveOneDomainOutRetentionRate };
    case "date_sensitivity": return { retentionRate: summary.dateSensitivityRetentionRate, events: summary.eventDateSensitivity };
    case "neighbor_stability": return { supportMinutes: summary.neighborSupportMinutes, clusterMassRatio: summary.clusterMassRatio };
    case "candidate_split": return { marginPercent: summary.primarySecondaryMarginPercent, splits: summary.candidateSplits };
  }
}

export function buildReasonerState(input: Readonly<{
  snapshot: CandidateSnapshot | null;
  diagnostics: DiagnosticsSummary;
  opportunities: readonly QuestionOpportunity[];
  recentTurns?: readonly RectificationV4Turn[];
  recentEvents?: readonly LifeEventRevision[];
  currentTarget?: LifeEventRevision | null;
  targetDisposition?: TargetDisposition;
  pendingEvidence?: readonly PendingEvidence[];
  candidateRangeChanged?: boolean;
}>) {
  return {
    task: "Choose the next bounded rectification action.",
    currentSnapshotId: input.snapshot?.id ?? null,
    canOfferCandidateRange: input.snapshot?.canAcceptRange ?? false,
    hasCandidateRange: Boolean(input.snapshot?.clusters[0]),
    candidateRangeChanged: input.candidateRangeChanged ?? false,
    latestAnswer: input.recentTurns?.at(-1)?.answer ?? "",
    recentTurns: (input.recentTurns ?? []).slice(-6).map((turn) => ({ question: turn.question, answer: turn.answer })),
    recentEvents: chronologicalEvents(input.recentEvents ?? []).slice(-5).map((event) => ({ summary: event.summary, date: event.dateRange.label, domain: event.domain, subject: event.subject })),
    currentTarget: input.currentTarget ? { summary: input.currentTarget.summary, date: input.currentTarget.dateRange.label, domain: input.currentTarget.domain } : null,
    targetDisposition: input.targetDisposition ?? "not_applicable",
    pendingEvidence: {
      count: input.pendingEvidence?.length ?? 0,
      reasons: [...new Set((input.pendingEvidence ?? []).map((item) => item.reasonCode))],
    },
    compactDiagnostics: {
      primaryClusterRetentionRate: input.diagnostics.primaryClusterRetentionRate,
      mostDiscriminatingLayers: input.diagnostics.mostDiscriminatingLayers,
    },
    opportunities: input.opportunities.map(({ opportunityId, kind, targetEventId, goal, requestedFields, anchors, utility, reason }) => ({
      opportunityId, kind, targetEventId, goal, requestedFields, anchors, utility, reason,
    })),
  };
}

export async function runBoundedReasoner(input: Readonly<{
  caseValue: RectificationV4Case;
  snapshot: CandidateSnapshot | null;
  diagnostics: DiagnosticsSummary;
  opportunities: readonly QuestionOpportunity[];
  recentTurns?: readonly RectificationV4Turn[];
  recentEvents?: readonly LifeEventRevision[];
  currentTarget?: LifeEventRevision | null;
  targetDisposition?: TargetDisposition;
  pendingEvidence?: readonly PendingEvidence[];
  candidateRangeChanged?: boolean;
  maxToolCalls?: number;
  timeoutMs?: number;
  enabled?: boolean;
  generateDecision?: RectificationReasonerGenerator;
}>): Promise<Readonly<{
  decision: RectificationDecision;
  mode: "agent" | "deterministic_fallback";
  fallbackReason: string | null;
  toolCalls: readonly ToolCallTrace[];
  inputTokenCount: number | null;
  outputTokenCount: number | null;
  latencyMs: number;
  reasoningSummary: string | null;
}>> {
  const started = Date.now();
  const deploymentSha = process.env.DEPLOYMENT_SHA?.trim() || null;
  const model = (input.caseValue.orchestrationModelId ? resolveLanguageModel(input.caseValue.orchestrationModelId) : null) ?? defaultLanguageModel();
  const modelId = model?.id ?? input.caseValue.orchestrationModelId;
  const toolCalls: ToolCallTrace[] = [];
  let inputTokenCount = 0;
  let outputTokenCount = 0;
  let usageObserved = false;
  const fallback = (reason: string) => {
    recordRectificationAgentTelemetry({
      caseId: input.caseValue.id, phase: "fallback", outcome: "succeeded", modelId,
      toolName: null, decisionAction: null, durationMs: Date.now() - started,
      errorCode: reason, deploymentSha,
    });
    return {
      decision: deterministicDecision(input), mode: "deterministic_fallback" as const,
      fallbackReason: reason, toolCalls: [...toolCalls],
      inputTokenCount: usageObserved ? inputTokenCount : null,
      outputTokenCount: usageObserved ? outputTokenCount : null,
      latencyMs: Date.now() - started,
      reasoningSummary: null,
    };
  };
  if (input.enabled === false) return fallback("deployment_mode_legacy");
  if (!model && !input.generateDecision) return fallback("reasoner_model_unavailable");

  const maxToolCalls = input.maxToolCalls ?? 1;
  const used = new Set<RectificationDiagnostic>();
  const readDiagnostic = async (diagnostic: RectificationDiagnostic) => {
    const toolStarted = Date.now();
    if (used.size >= maxToolCalls || used.has(diagnostic)) {
      const trace = { tool: "run_rectification_diagnostics", diagnostic, outcome: "rejected" as const, durationMs: Date.now() - toolStarted, errorCode: "diagnostic_budget_exhausted" };
      toolCalls.push(trace);
      recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "tool", outcome: "rejected", modelId, toolName: trace.tool, decisionAction: "run_diagnostic", durationMs: trace.durationMs, errorCode: trace.errorCode, deploymentSha });
      throw new Error("diagnostic_budget_exhausted");
    }
    used.add(diagnostic);
    try {
      const result = diagnosticPayload(diagnostic, input.diagnostics);
      const trace = { tool: "run_rectification_diagnostics", diagnostic, outcome: "succeeded" as const, durationMs: Date.now() - toolStarted, errorCode: null };
      toolCalls.push(trace);
      recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "tool", outcome: "succeeded", modelId, toolName: trace.tool, decisionAction: "run_diagnostic", durationMs: trace.durationMs, errorCode: null, deploymentSha });
      return result;
    } catch (error) {
      const trace = { tool: "run_rectification_diagnostics", diagnostic, outcome: "failed" as const, durationMs: Date.now() - toolStarted, errorCode: "diagnostic_read_failed" };
      toolCalls.push(trace);
      recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "tool", outcome: "failed", modelId, toolName: trace.tool, decisionAction: "run_diagnostic", durationMs: trace.durationMs, errorCode: trace.errorCode, deploymentSha });
      throw error;
    }
  };
  const diagnosticsTool = createTool({
    id: "run_rectification_diagnostics",
    description: "Read one server-owned diagnostic for the current rectification snapshot. Inputs cannot contain case data, dates, candidates, or scores.",
    inputSchema: z.object({ diagnostic: rectificationDiagnosticSchema }).strict(),
    outputSchema: z.object({ diagnostic: rectificationDiagnosticSchema, result: z.unknown() }).strict(),
    execute: async ({ diagnostic }) => ({ diagnostic, result: await readDiagnostic(diagnostic) }),
  });
  const agent = model ? new Agent({
    id: `rectification-v5-reasoner-${model.id}`,
    name: "Bounded Birth Time Rectification Reasoner",
    model: model.model,
    skills: [skillPath],
    tools: { run_rectification_diagnostics: diagnosticsTool },
    instructions: "Choose one server-owned action. Never create an event id, candidate, score, date, question, calculation input, or birth minute. Ask only by opportunityId. Candidate ranges may only use currentSnapshotId. You may request or call one diagnostic, then must return a final non-diagnostic action. Return strict structured output.",
  }) : null;
  const isOpenAiProvider = model?.mode === "openai";
  const generate: RectificationReasonerGenerator = input.generateDecision ?? (async (prompt) => {
    if (!agent) throw new Error("reasoner_model_unavailable");
    let reasoningSummary = "";
    const stream = await agent.stream(prompt, {
      abortSignal: AbortSignal.timeout(input.timeoutMs ?? 20_000),
      maxSteps: maxToolCalls + 2,
      providerOptions: isOpenAiProvider
        ? { openai: { reasoningEffort: "high", reasoningSummary: "auto" } }
        : undefined,
      structuredOutput: { schema: rectificationDecisionSchema, jsonPromptInjection: "inline" },
    });
    for await (const chunk of stream.fullStream) {
      const isOpenAiSummary = isOpenAiProvider && chunk.type === "reasoning-delta";
      if (isOpenAiSummary && reasoningSummary.length < 2_000) {
        reasoningSummary += chunk.payload.text.slice(0, 2_000 - reasoningSummary.length);
      }
    }
    return {
      object: await stream.object,
      totalUsage: stream.totalUsage,
      reasoningSummary,
      reasoningSource: reasoningSummary ? "provider_summary" : null,
    };
  });
  const addUsage = async (result: GeneratedDecision) => {
    if (!result.totalUsage) return;
    const usage = await result.totalUsage;
    inputTokenCount += Math.max(0, Math.trunc(usage.inputTokens ?? 0));
    outputTokenCount += Math.max(0, Math.trunc(usage.outputTokens ?? 0));
    usageObserved = true;
  };
  const baseState = buildReasonerState(input);
  const sensitiveTexts = [
    baseState.latestAnswer,
    ...baseState.recentTurns.flatMap((turn) => [turn.question, turn.answer]),
    ...baseState.recentEvents.flatMap((event) => [event.summary, event.date]),
    ...(baseState.currentTarget ? [baseState.currentTarget.summary, baseState.currentTarget.date] : []),
    ...baseState.opportunities.flatMap((opportunity) => opportunity.anchors),
  ];
  let reasoningSummary: string | null = null;

  recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "reasoner", outcome: "started", modelId, toolName: null, decisionAction: null, durationMs: null, errorCode: null, deploymentSha });
  try {
    const first = await generate(JSON.stringify(baseState), "initial");
    await addUsage(first);
    reasoningSummary = first.reasoningSource === "provider_summary"
      ? sanitizeReasoningSummary(first.reasoningSummary, sensitiveTexts)
      : null;
    let decision = rectificationDecisionSchema.parse(first.object);
    if (decision.action === "run_diagnostic") {
      const result = await readDiagnostic(decision.diagnostic);
      const second = await generate(JSON.stringify({
        ...baseState,
        requiredFinalAction: true,
        diagnosticResult: { diagnostic: decision.diagnostic, result },
      }), "after_diagnostic");
      await addUsage(second);
      reasoningSummary = second.reasoningSource === "provider_summary"
        ? sanitizeReasoningSummary(second.reasoningSummary, sensitiveTexts) ?? reasoningSummary
        : reasoningSummary;
      decision = rectificationDecisionSchema.parse(second.object);
      if (decision.action === "run_diagnostic") return fallback("reasoner_returned_nonfinal_diagnostic");
    }
    const latencyMs = Date.now() - started;
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "reasoner", outcome: "succeeded", modelId, toolName: null, decisionAction: decision.action, durationMs: latencyMs, errorCode: null, deploymentSha });
    return {
      decision, mode: "agent", fallbackReason: null, toolCalls,
      inputTokenCount: usageObserved ? inputTokenCount : null,
      outputTokenCount: usageObserved ? outputTokenCount : null,
      latencyMs,
      reasoningSummary,
    };
  } catch (error) {
    const reason = error instanceof DOMException && error.name === "TimeoutError" ? "reasoner_timeout"
      : error instanceof Error && error.message === "diagnostic_budget_exhausted" ? "diagnostic_budget_exhausted"
        : error instanceof Error && error.message === "reasoner_model_unavailable" ? "reasoner_model_unavailable"
          : "reasoner_failed";
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "reasoner", outcome: "failed", modelId, toolName: null, decisionAction: null, durationMs: Date.now() - started, errorCode: reason, deploymentSha });
    return fallback(reason);
  }
}
