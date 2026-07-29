import path from "node:path";
import { Agent } from "@mastra/core/agent";
import { defaultLanguageModel, resolveLanguageModel } from "@/mastra/model";
import type { CandidateSnapshot, LifeEventRevision, PendingEvidence, RectificationV4Case } from "../rectification-v4/contracts.ts";
import { publicMessageSchema, type PublicMessage, type QuestionOpportunity, type ValidatedDecision } from "./contracts.ts";
import { recordRectificationAgentTelemetry } from "./telemetry.ts";

const skillPath = process.env.RECTIFICATION_SKILL_PATH?.trim() || path.resolve(process.cwd(), "..", "skills", "birth-time-rectification");
const agents = new Map<string, Agent>();
const bannedAcknowledgement = /(?:这个信息很有用|它不是单纯的|而是把|接下来最有价值的是|这样可以避免|已记录[:：]?|我记下了)/;
const overinterpretedAcknowledgement = /(?:职业方向正式落地|人生意义|意味着你|说明你(?:已经|开始|正式)|标志着你)/;
const internalTerms = /(?:opportunityId|snapshotId|eventId|targetEventId|requestedFields|fallbackPrompt|tool\s*call|tool_call|score|评分|模型名|opportunity|snapshot|D\d{1,2}|KP\b|Vimshottari)/i;
const multiQuestionMoves = /(?:另外|还有|同时再说|并且告诉我|顺便|再告诉我)/;
const cannedQuestion = /(?:承接[“\"']?.{0,80}[”\"']?，?请再说一件|接下来请继续讲另一件|我会顺着你的叙述继续核对)/;
const exactClockMinute = /(?:[01]?\d|2[0-3])[:：][0-5]\d|(?:[零〇一二两三四五六七八九十]{1,3}|(?:[01]?\d|2[0-3]))点(?:[零〇一二两三四五六七八九十]{1,3}|[0-5]?\d)分/;
const exactMinuteClaim = /(?:唯一|准确|精确|确切|确认|确定|代表).{0,12}(?:出生|生时)?(?:时间|时刻|分钟)|(?:出生|生时)(?:时间|时刻|分钟)?.{0,12}(?:唯一|准确|精确|确切|确认|确定|代表|就是)/;

function agentFor(modelId: string | null): { id: string; agent: Agent } | null {
  const selected = (modelId ? resolveLanguageModel(modelId) : null) ?? defaultLanguageModel();
  if (!selected) return null;
  const cached = agents.get(selected.id);
  if (cached) return { id: selected.id, agent: cached };
  const agent = new Agent({
    id: `rectification-v6-renderer-${selected.id}`,
    name: "Birth Time Rectification Response Renderer",
    model: selected.model,
    skills: [skillPath],
    instructions: "Write concise natural Simplified Chinese. Realize exactly one question from the supplied semantic opportunity. Do not invent events or dates, switch targets, interpret the life meaning of an experience, expose ids/scores/techniques, mention a representative minute, or claim an exact birth minute. Avoid canned acknowledgement. Return strict JSON only.",
  });
  agents.set(selected.id, agent);
  return { id: selected.id, agent };
}

function normalized(value: string): string {
  return value.normalize("NFKC").replace(/[“”"'\s，,。.!！?？:：；;]/g, "");
}

function includesAnchor(question: string, anchor: string): boolean {
  const normalizedQuestion = normalized(question);
  const normalizedAnchor = normalized(anchor);
  if (normalizedQuestion.includes(normalizedAnchor)) return true;
  for (let start = 0; start <= normalizedAnchor.length - 4; start += 1) {
    if (normalizedQuestion.includes(normalizedAnchor.slice(start, start + 4))) return true;
  }
  return false;
}

function visibleTextSafetyIssues(value: string): string[] {
  const issues: string[] = [];
  if (internalTerms.test(value)) issues.push("internal_information_exposed");
  if (exactClockMinute.test(value) || exactMinuteClaim.test(value)) issues.push("birth_minute_injected");
  return issues;
}

export function validateQuestionRealization(question: unknown, opportunity: QuestionOpportunity): Readonly<{ valid: boolean; issues: readonly string[] }> {
  if (typeof question !== "string") return { valid: false, issues: ["question_missing"] };
  const value = question.trim();
  const issues: string[] = [];
  if (value.length < 8 || value.length > 180) issues.push("question_length_invalid");
  if ((value.match(/[?？]/g) ?? []).length > 1) issues.push("multiple_question_marks");
  if ((value.match(/[。.!！?？]/g) ?? []).length > 2) issues.push("too_many_sentences");
  if (/\n\s*(?:[-*•]|\d+[.)、])/.test(value)) issues.push("question_list_forbidden");
  issues.push(...visibleTextSafetyIssues(value));
  if (multiQuestionMoves.test(value)) issues.push("multiple_question_instruction");
  if (cannedQuestion.test(value)) issues.push("canned_question_forbidden");
  if (opportunity.targetEventId || (opportunity.kind === "ask_new_event" && opportunity.anchors.length > 0)) {
    if (!opportunity.anchors.some((anchor) => includesAnchor(value, anchor))) issues.push("target_anchor_missing");
  }
  for (const field of opportunity.requestedFields) {
    if (field === "event_subject" && !/(?:本人|你自己|家人|伴侣|配偶)/.test(value)) issues.push("event_subject_not_requested");
    if (field === "event_month" && !/(?:月份|哪个月|几月|大概月份|时间段)/.test(value)) issues.push("event_month_not_requested");
    if (field === "event_day" && !/(?:哪一天|几号|具体日期|大概日期)/.test(value)) issues.push("event_day_not_requested");
    if (field === "event_range" && !/(?:大概时间|时间范围|什么时候|哪个时间|哪一段时间)/.test(value)) issues.push("event_range_not_requested");
    if (field === "event_stage" && !/(?:开始|高峰|结束|正式发生)/.test(value)) issues.push("event_stage_not_requested");
    if (field === "new_dated_event" && !/(?:哪次|哪件|一件|经历|变化|转折|发生)/.test(value)) issues.push("new_event_not_requested");
    if (field === "new_dated_event" && !/(?:时间|日期|什么时候|哪年|哪月|几月)/.test(value)) issues.push("new_event_date_not_requested");
    if (field === "event_year" && !/(?:哪年|年份|哪一年)/.test(value)) issues.push("event_year_not_requested");
  }
  return { valid: issues.length === 0, issues };
}

function primaryRange(snapshot: CandidateSnapshot | null): string | null {
  const primary = snapshot?.clusters[0];
  return primary ? `${primary.startTime}–${primary.endTime}` : null;
}

export function candidateUpdateFor(input: Readonly<{
  snapshot: CandidateSnapshot | null;
  previousSnapshot: CandidateSnapshot | null;
  decisionAction: ValidatedDecision["decision"]["action"];
}>): string | null {
  if (!input.snapshot?.canAcceptRange) return null;
  const current = primaryRange(input.snapshot);
  if (!current) return null;
  const previous = primaryRange(input.previousSnapshot);
  const firstStable = !input.previousSnapshot?.canAcceptRange;
  const changed = previous !== current;
  if (!firstStable && !changed) return null;
  return `目前通过稳定性门的候选范围是 ${current}；它仍是待验证范围，不代表其中某一分钟已被确认。`;
}

function naturalAcknowledgement(input: { latestAnswer: string; acceptedEvents: readonly LifeEventRevision[]; pendingEvidence: readonly PendingEvidence[] }): string {
  const latest = input.acceptedEvents.at(-1);
  if (latest) return `你提到的是 ${latest.dateRange.label} 的“${latest.summary}”。`;
  if (input.pendingEvidence.length) return "这段经历的事件或日期目前还不足以安全进入评分。";
  if (input.latestAnswer) return "我会保留你刚才的原始说法，不补写你没有确认的信息。";
  return "我们继续用时间相对明确的经历比较候选范围。";
}

function deterministic(input: {
  latestAnswer: string;
  acceptedEvents: readonly LifeEventRevision[];
  pendingEvidence: readonly PendingEvidence[];
  snapshot: CandidateSnapshot | null;
  previousSnapshot: CandidateSnapshot | null;
  validated: ValidatedDecision;
}): PublicMessage {
  return {
    acknowledgement: naturalAcknowledgement(input),
    candidateUpdate: candidateUpdateFor({ snapshot: input.snapshot, previousSnapshot: input.previousSnapshot, decisionAction: input.validated.decision.action }),
    limitation: input.validated.decision.action === "stop_low_confidence"
      ? "现有证据不足以安全缩小范围，我会在这里停下，不把不稳定结果包装成确定时间。"
      : null,
    question: input.validated.selectedOpportunity?.fallbackPrompt ?? null,
  };
}

export function realizePublicMessage(value: unknown, input: Parameters<typeof deterministic>[0]): PublicMessage {
  const parsed = publicMessageSchema.parse(value);
  const opportunity = input.validated.selectedOpportunity;
  const fallback = deterministic(input);
  const acknowledgement = visibleTextSafetyIssues(parsed.acknowledgement).length > 0
    || bannedAcknowledgement.test(parsed.acknowledgement)
    || overinterpretedAcknowledgement.test(parsed.acknowledgement)
    || (parsed.acknowledgement.match(/[。.!！?？]/g) ?? []).length > 2
    || (input.acceptedEvents.at(-1) && !normalized(parsed.acknowledgement).includes(normalized(input.acceptedEvents.at(-1)!.summary)))
    ? fallback.acknowledgement
    : parsed.acknowledgement;
  const question = opportunity
    ? validateQuestionRealization(parsed.question, opportunity).valid ? parsed.question : opportunity.fallbackPrompt
    : null;
  return {
    acknowledgement,
    candidateUpdate: fallback.candidateUpdate,
    limitation: fallback.limitation ?? (parsed.limitation && visibleTextSafetyIssues(parsed.limitation).length === 0 ? parsed.limitation : null),
    question,
  };
}

export async function renderPublicTurn(input: Readonly<{
  caseValue: RectificationV4Case;
  latestAnswer: string;
  acceptedEvents: readonly LifeEventRevision[];
  pendingEvidence: readonly PendingEvidence[];
  snapshot: CandidateSnapshot | null;
  previousSnapshot: CandidateSnapshot | null;
  validated: ValidatedDecision;
  timeoutMs?: number;
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
    const opportunity = input.validated.selectedOpportunity;
    const result = await selected.agent.generate(JSON.stringify({
      task: "Render one public turn and naturally realize the semantic question contract.",
      latestAnswer: input.latestAnswer,
      acceptedEvents: input.acceptedEvents.slice(-3).map((event) => ({ summary: event.summary, date: event.dateRange.label, subject: event.subject })),
      pendingEvidence: input.pendingEvidence.slice(-3).map((event) => ({ reasonCode: event.reasonCode })),
      action: input.validated.decision.action,
      selectedOpportunity: opportunity ? {
        kind: opportunity.kind,
        goal: opportunity.goal,
        requestedFields: opportunity.requestedFields,
        anchors: opportunity.anchors,
        contextFacts: opportunity.contextFacts,
        forbiddenMoves: opportunity.forbiddenMoves,
      } : null,
    }), { abortSignal: AbortSignal.timeout(input.timeoutMs ?? 15_000), structuredOutput: { schema: publicMessageSchema, jsonPromptInjection: "inline" } });
    const generated = publicMessageSchema.parse(result.object);
    const questionValidation = opportunity ? validateQuestionRealization(generated.question, opportunity) : null;
    const message = realizePublicMessage(generated, input);
    if (questionValidation && !questionValidation.valid) {
      recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "renderer", outcome: "rejected", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: questionValidation.issues[0] ?? "renderer_question_rejected", deploymentSha });
      recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "fallback", outcome: "succeeded", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: "renderer_question_rejected", deploymentSha });
      return message;
    }
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "renderer", outcome: "succeeded", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: null, deploymentSha });
    return message;
  } catch {
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "renderer", outcome: "failed", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: "renderer_failed", deploymentSha });
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "fallback", outcome: "succeeded", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: "renderer_failed", deploymentSha });
    return fallback;
  }
}
