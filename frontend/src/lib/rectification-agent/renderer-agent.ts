import path from "node:path";
import { Agent } from "@mastra/core/agent";
import { z } from "zod";
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
const cannedQuestion = /(?:承接[“\"']?.{0,80}[”\"']?，?请再说一件|接下来请继续讲另一件|我会顺着你的叙述继续核对|以[“\"']?.{0,80}[”\"']?为(?:时间)?参照|搬到新城市|长期离乡)/;
const exactClockMinute = /(?:[01]?\d|2[0-3])[:：][0-5]\d|(?:[零〇一二两三四五六七八九十]{1,3}|(?:[01]?\d|2[0-3]))点(?:[零〇一二两三四五六七八九十]{1,3}|[0-5]?\d)分/;
const exactMinuteClaim = /(?:唯一|准确|精确|确切|确认|确定|代表).{0,12}(?:出生|生时)?(?:时间|时刻|分钟)|(?:出生|生时)(?:时间|时刻|分钟)?.{0,12}(?:唯一|准确|精确|确切|确认|确定|代表|就是)/;
const distinctEventMove = /(?:除了|之外|另一(?:件|次)|下(?:一|1)次|之后|后来|此后|还记得)/;
const explicitAnchorReference = /(?:这次经历|这段经历|刚才那段|刚才这段|你刚说的|你刚提到的|刚说的|刚提到的|前面那段|这件事)/;
const newEventDomainTerms: Readonly<Partial<Record<QuestionOpportunity["domain"], RegExp>>> = {
  education: /(?:入学|升学|毕业|学校|大学|专业|考试|读书)/,
  relocation: /(?:搬家|搬到|搬去|迁居|迁到|迁往|移居|定居)/,
  relationship: /(?:恋爱|关系|结婚|离婚|分手|伴侣|对象)/,
  career: /(?:工作|实习|公司|研究院|职业|入职|离职|创业|职责|负责)/,
  finance: /(?:收入|负债|投资|资产|财务|买房|卖房)/,
  health_pressure: /(?:住院|手术|事故|健康|生病|确诊|康复)/,
};
const questionRealizationSchema = z.object({ question: z.string().trim().min(1).max(1_000) }).strict();
const openingMessageSchema = z.object({ message: z.string().trim().min(1).max(1_000) }).strict();
const domainChecklistTerms = /(?:学业|教育|搬家|迁居|感情|婚姻|工作|职业|财务|健康)/g;

export type OpeningQuestionGenerator = (prompt: string, phase: "generate" | "repair") => Promise<Readonly<{ object: unknown }>>;

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
    instructions: "Write concise natural Simplified Chinese for the supplied task. For an opening message, state that the supplied candidate window is only being checked and is not a confirmed birth minute, then invite one clearly remembered experience or connected sequence without a fixed-domain checklist. For a semantic opportunity, realize exactly one question; for a new event, use recall cues only as optional examples and ask whether it happened instead of assuming it did. Preserve the user's ability to be unsure, skip, decline, or change direction. Do not invent events, ages, date windows or dates, switch targets, interpret life meaning, expose ids/scores/techniques, mention a representative minute, or claim an exact birth minute. Avoid canned acknowledgement. Return strict JSON only.",
  });
  agents.set(selected.id, agent);
  return { id: selected.id, agent };
}


function validateOpeningMessage(value: unknown, range: Readonly<{ start: string; end: string }>) {
  const parsed = openingMessageSchema.safeParse(value);
  if (!parsed.success) return { message: null, issues: ["opening_schema_invalid"] };
  const message = parsed.data.message;
  const issues: string[] = [];
  if (!message.includes(range.start) || !message.includes(range.end)) issues.push("candidate_range_missing");
  if (!/(?:不是|并非|尚未|还未|不能).{0,16}(?:确认|确定)|待(?:核对|验证)/.test(message)) issues.push("unconfirmed_range_missing");
  if ((message.match(/[?？]/g) ?? []).length > 1) issues.push("multiple_questions");
  if (!/(?:经历|事情|事件|变化|转折|记得|想得起来)/.test(message) || !/(?:说|讲|分享|回忆|开始)/.test(message)) issues.push("experience_invitation_missing");
  if (internalTerms.test(message)) issues.push("private_detail_exposed");
  const positiveClaims = message.split(/[。；;！？?!]/).filter((sentence) => !/(?:不是|并非|尚未|还未|不能)/.test(sentence)).join(" ");
  if (exactMinuteClaim.test(positiveClaims)) issues.push("exact_minute_claimed");
  if ((message.match(domainChecklistTerms) ?? []).length >= 3) issues.push("fixed_domain_checklist");
  return { message: issues.length ? null : message, issues };
}

export async function generateOpeningQuestion(input: Readonly<{
  caseId: string;
  candidateRange: Readonly<{ start: string; end: string }>;
  modelId: string | null;
  timeoutMs?: number;
  generate?: OpeningQuestionGenerator;
}>): Promise<string> {
  const selected = input.generate ? null : agentFor(input.modelId);
  const modelId = selected?.id ?? input.modelId;
  const started = Date.now();
  const deploymentSha = process.env.DEPLOYMENT_SHA?.trim() || process.env.VERCEL_GIT_COMMIT_SHA?.trim() || null;
  const generate = input.generate ?? (async (prompt: string) => {
    if (!selected) throw new Error("opening_model_unavailable");
    return selected.agent.generate(prompt, {
      abortSignal: AbortSignal.timeout(input.timeoutMs ?? 15_000),
      structuredOutput: { schema: openingMessageSchema, jsonPromptInjection: "inline" },
    });
  });
  const context = {
    task: "Write the opening message for this new rectification case.",
    candidateRange: input.candidateRange,
    requirements: [
      "State that this candidate range is unconfirmed and only being checked.",
      "Invite one clearly remembered experience or a connected sequence.",
      "Use at most one natural question and no fixed-domain checklist.",
      "Allow the user to be unsure, skip, or change direction.",
    ],
  };

  recordRectificationAgentTelemetry({ caseId: input.caseId, phase: "renderer", outcome: "started", modelId, toolName: null, decisionAction: "opening_question", durationMs: null, errorCode: null, deploymentSha });
  try {
    let result = validateOpeningMessage((await generate(JSON.stringify(context), "generate")).object, input.candidateRange);
    if (!result.message) {
      recordRectificationAgentTelemetry({ caseId: input.caseId, phase: "renderer", outcome: "rejected", modelId, toolName: null, decisionAction: "opening_question", durationMs: Date.now() - started, errorCode: result.issues[0] ?? "opening_rejected", deploymentSha });
      result = validateOpeningMessage((await generate(JSON.stringify({ ...context, task: "Repair the rejected opening message once.", validationIssues: result.issues }), "repair")).object, input.candidateRange);
    }
    if (!result.message) throw new Error(`opening_rejected:${result.issues.join(",")}`);
    recordRectificationAgentTelemetry({ caseId: input.caseId, phase: "renderer", outcome: "succeeded", modelId, toolName: null, decisionAction: "opening_question", durationMs: Date.now() - started, errorCode: null, deploymentSha });
    return result.message;
  } catch (error) {
    recordRectificationAgentTelemetry({ caseId: input.caseId, phase: "renderer", outcome: "failed", modelId, toolName: null, decisionAction: "opening_question", durationMs: Date.now() - started, errorCode: error instanceof Error ? error.message.slice(0, 120) : "opening_failed", deploymentSha });
    throw error;
  }
}

function normalized(value: string): string {
  return value.normalize("NFKC").replace(/[“”"'\s，,。.!！?？:：；;]/g, "");
}

function matchingAnchorFragment(question: string, anchor: string): string | null {
  const normalizedQuestion = normalized(question);
  const normalizedAnchor = normalized(anchor);
  if (!normalizedAnchor) return null;
  if (normalizedQuestion.includes(normalizedAnchor)) return normalizedAnchor;
  for (let length = Math.min(normalizedQuestion.length, normalizedAnchor.length); length >= 4; length -= 1) {
    for (let start = 0; start <= normalizedAnchor.length - length; start += 1) {
      const fragment = normalizedAnchor.slice(start, start + length);
      if (normalizedQuestion.includes(fragment)) return fragment;
    }
  }
  return null;
}

function includesStrictAnchor(question: string, anchor: string): boolean {
  const normalizedAnchor = normalized(anchor);
  return normalizedAnchor.length > 0 && normalized(question).includes(normalizedAnchor);
}

function withoutMatchedAnchors(question: string, anchors: readonly string[]): string {
  let remaining = normalized(question);
  for (const anchor of anchors) {
    const matched = matchingAnchorFragment(remaining, anchor);
    if (matched) remaining = remaining.replace(matched, "");
  }
  return remaining;
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
  if (opportunity.targetEventId) {
    if (!opportunity.anchors.some((anchor) => includesStrictAnchor(value, anchor))) issues.push("target_anchor_missing");
  } else if (opportunity.kind === "ask_new_event") {
    const anchorMatched = opportunity.anchors.some((anchor) => matchingAnchorFragment(value, anchor) !== null);
    if (opportunity.anchors.length > 0 && !anchorMatched && !explicitAnchorReference.test(value)) issues.push("target_anchor_missing");
    if (opportunity.anchors.length > 0 && !distinctEventMove.test(value)) issues.push("new_event_not_distinct");
    const domainTerms = newEventDomainTerms[opportunity.domain];
    const questionWithoutAnchor = withoutMatchedAnchors(value, opportunity.anchors);
    if (domainTerms && !domainTerms.test(questionWithoutAnchor)) issues.push("new_event_domain_mismatch");
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
  if (input.decisionAction !== "offer_candidate_range" && !firstStable && !changed) return null;
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
  onRealization?: (outcome: Readonly<{
    mode: "model_validated" | "server_fallback";
    reason: "model_unavailable" | "question_rejected" | "model_failed" | null;
  }>) => void;
}>): Promise<PublicMessage> {
  const started = Date.now();
  const deploymentSha = process.env.DEPLOYMENT_SHA?.trim() || null;
  const fallback = deterministic(input);
  const selected = agentFor(input.caseValue.narrationModelId);
  if (!selected) {
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "fallback", outcome: "succeeded", modelId: input.caseValue.narrationModelId, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: "renderer_model_unavailable", deploymentSha });
    input.onRealization?.({ mode: "server_fallback", reason: "model_unavailable" });
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
      input.onRealization?.({ mode: "server_fallback", reason: "question_rejected" });
      return message;
    }
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "renderer", outcome: "succeeded", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: null, deploymentSha });
    input.onRealization?.({ mode: "model_validated", reason: null });
    return message;
  } catch {
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "renderer", outcome: "failed", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: "renderer_failed", deploymentSha });
    recordRectificationAgentTelemetry({ caseId: input.caseValue.id, phase: "fallback", outcome: "succeeded", modelId: selected.id, toolName: null, decisionAction: input.validated.decision.action, durationMs: Date.now() - started, errorCode: "renderer_failed", deploymentSha });
    input.onRealization?.({ mode: "server_fallback", reason: "model_failed" });
    return fallback;
  }
}

export async function regenerateQuestionRealization(input: Readonly<{
  caseValue: RectificationV4Case;
  currentPrompt: string;
  latestAnswer: string;
  acceptedEvents: readonly LifeEventRevision[];
  opportunity: QuestionOpportunity;
  timeoutMs?: number;
}>): Promise<string> {
  const selected = agentFor(input.caseValue.narrationModelId);
  if (!selected) return input.currentPrompt;
  try {
    const result = await selected.agent.generate(JSON.stringify({
      task: "Rewrite the current question naturally without changing its semantic target. Return one question only.",
      currentPrompt: input.currentPrompt,
      latestAnswer: input.latestAnswer,
      recentEvents: input.acceptedEvents.slice(-5).map((event) => ({
        summary: event.summary,
        date: event.dateRange.label,
        subject: event.subject,
      })),
      selectedOpportunity: {
        kind: input.opportunity.kind,
        goal: input.opportunity.goal,
        requestedFields: input.opportunity.requestedFields,
        anchors: input.opportunity.anchors,
        contextFacts: input.opportunity.contextFacts,
        forbiddenMoves: input.opportunity.forbiddenMoves,
      },
    }), {
      abortSignal: AbortSignal.timeout(input.timeoutMs ?? 15_000),
      structuredOutput: { schema: questionRealizationSchema, jsonPromptInjection: "inline" },
    });
    const question = questionRealizationSchema.parse(result.object).question;
    return validateQuestionRealization(question, input.opportunity).valid ? question : input.currentPrompt;
  } catch {
    return input.currentPrompt;
  }
}
