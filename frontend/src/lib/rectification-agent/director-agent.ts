import path from "node:path";
import { Agent } from "@mastra/core/agent";
import { z } from "zod";
import { defaultLanguageModel, resolveLanguageModel } from "@/mastra/model";
import type { CandidateSnapshot, EvidenceDomain, EventKind, LifeEventRevision, PendingEvidence, RectificationV4Case, RectificationV4Turn } from "../rectification-v4/contracts.ts";
import type { TargetDisposition } from "../rectification-v4/extraction.ts";
import { hasPolicyInvalidScoreableEvents } from "../rectification-v4/evidence-ledger.ts";
import { domainScorerRegistry } from "../rectification-v4/domain-scorers.ts";
import { buildCandidateContrastPacket } from "./opportunity-builder.ts";
import { rectificationCaseDossierSchema, rectificationTurnPlanSchema, type DiagnosticsSummary, type RectificationAgentTool, type RectificationCaseDossier, type RectificationDiagnostic, type RectificationTurnPlan, type ToolCallTrace, type ToolObservation } from "./contracts.ts";
import { assertRectificationSkillLoaded } from "./skill-runtime.ts";

const skillPath = process.env.RECTIFICATION_SKILL_PATH?.trim() || path.resolve(process.cwd(), "..", "skills", "birth-time-rectification");
const domains: EvidenceDomain[] = ["education", "relocation", "relationship", "career", "finance", "health_pressure", "family", "other"];
const kinds: EventKind[] = ["education_milestone", "relocation", "relationship_start", "relationship_end", "relationship_change", "career_change", "finance_change", "self_health_event", "family_health_event", "family_bereavement", "family_event", "other"];
const privatePattern = /(?:[0-9a-f]{8}-[0-9a-f-]{27,}|opportunity(?:id)?|snapshot(?:id)?|event(?:id)?|targetEventId|(?:raw|原始)?\s*(?:score|评分|得分)|权重|rule[_ -]?id|贡献矩阵|tool[_ -]?call|cluster[_ -]?id|\b(?:case_read|candidate_scan|evidence_gap|diagnostic_read)\b|工具原始(?:输出|轨迹)|内部推理链)/iu;
const quantifiedStructurePattern = /(?:(?:D\d{1,2}|KP|Vimshottari|Narayana|Shadbala|Ashtakavarga|Chaturvimshamsha|上升星座|宫位|分盘)[^。！？\n]{0,60}(?:切换|变化|变动|遍历)[^。！？\n]{0,16}(?:\d+|[一二三四五六七八九十百]+)\s*次|(?:\d+|[一二三四五六七八九十百]+)\s*次[^。！？\n]{0,60}(?:切换|变化|变动|遍历))/iu;
const exactMinutePattern = /(?:\b(?:[01]?\d|2[0-3]):[0-5]\d\b|(?:凌晨|清晨|上午|中午|下午|傍晚|晚上)?\s*[零〇一二两三四五六七八九十百\d]{1,4}\s*[点时]\s*[零〇一二两三四五六七八九十百\d]{1,4}\s*分)/u;
const questionClausePattern = /(?:请|你(?:还)?(?:记得|能否|是否|有没有)|再(?:说|补充|回忆)|哪(?:一|个|年|月|天)?|什么|多少|几(?:年|月|号|日)?|吗|呢)/u;
const genericAcknowledgementPattern = /^(?:好的|明白了|知道了|收到|已记录|我记下了|我已按你的描述整理这轮线索)[。！!]?$/u;
const groundedPublicReplyRequirement = "When the latest answer adds or refines a concrete event, the final public reply must: acknowledge the exact event and its date precision; summarize one to three evidence signals found in the user wording; use evidenceExplanation to map those signals to public method layers from dossier.capabilities.publicTechniqueCapabilities; distinguish a general method mapping from calculations actually present in tool observations; explain why the next question helps; and ask at most one question. Public method names such as D4, D24, Vimshottari, Narayana, UL, and A10 are allowed. Never expose internal ids, raw scores, weights, contribution matrices, raw tool traces, candidate minutes, or hidden reasoning. Never claim a numeric structural fact such as a division switching N times unless the dossier contains the matching window_sensitivity observation and publicExplanationGrounding cites its fact key.";

function containsExactMinute(value: string): boolean {
  return exactMinutePattern.test(value);
}

function asksMultipleQuestions(value: string): boolean {
  if ((value.match(/[?？]/g) ?? []).length > 1) return true;
  return value.split(/[。；;！!\n]+|[，,]\s*(?=(?:请|你|再))/u)
    .filter((part) => questionClausePattern.test(part))
    .length > 1;
}

function normalizedQuestion(value: string): string {
  return value.normalize("NFKC").toLocaleLowerCase().replace(/[\s?？。！!，,、；;：:“”‘’'"（）()]/gu, "");
}

function mentionsTechnique(value: string, technique: string): boolean {
  const escaped = technique.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
  return new RegExp(`(?<![A-Za-z0-9])${escaped}(?![A-Za-z0-9])`, "iu").test(value);
}
const declinedPattern = /(?:不想说|不方便说|不想回答|跳过|这个不说|换个方向|不聊这个)/u;
type Generated = Readonly<{ object: unknown; totalUsage?: { inputTokens?: number; outputTokens?: number } | Promise<{ inputTokens?: number; outputTokens?: number }> }>;
const regeneratedQuestionSchema = z.object({ question: z.string().trim().min(8).max(500) }).strict();
export type RectificationDirectorGenerator = (prompt: string, phase: "evidence" | "final" | "after_observation" | "converge" | "repair") => Promise<Generated>;

function summarizeEarlierTurns(turns: readonly RectificationV4Turn[]): string | null {
  const older = turns.slice(0, -12);
  if (!older.length) return null;
  return older.map((turn, index) => `${index + 1}. 问：${turn.question.slice(0, 240)}\n答：${turn.answer.slice(0, 500)}`).join("\n").slice(-12_000);
}

function diagnosticResult(kind: RectificationDiagnostic, value: DiagnosticsSummary) {
  switch (kind) {
    case "leave_one_event_out": return { retentionRate: value.leaveOneEventOutRetentionRate, unstableEventIds: value.unstableEventIds };
    case "leave_one_domain_out": return { retentionRate: value.leaveOneDomainOutRetentionRate };
    case "date_sensitivity": return { retentionRate: value.dateSensitivityRetentionRate, events: value.eventDateSensitivity };
    case "neighbor_stability": return { supportMinutes: value.neighborSupportMinutes, clusterMassRatio: value.clusterMassRatio };
    case "candidate_split": return { marginPercent: value.primarySecondaryMarginPercent, splits: value.candidateSplits };
  }
}

export function buildRectificationCaseDossier(input: Readonly<{ caseValue: RectificationV4Case; turns: readonly RectificationV4Turn[]; events: readonly LifeEventRevision[]; pendingEvidence?: readonly PendingEvidence[]; snapshot: CandidateSnapshot | null; previousSnapshot?: CandidateSnapshot | null; diagnostics: DiagnosticsSummary | null; targetDisposition: TargetDisposition; currentTargetEventId: string | null }>): RectificationCaseDossier {
  const latest = new Map<string, number>();
  input.events.forEach((event) => latest.set(event.eventId, Math.max(latest.get(event.eventId) ?? 0, event.revision)));
  const recent = input.turns.slice(-12);
  const publicRangeAllowed = Boolean(input.snapshot?.canAcceptRange) && !hasPolicyInvalidScoreableEvents(input.events);
  return rectificationCaseDossierSchema.parse({
    case: { candidateWindow: input.caseValue.calculationSpec.candidateRange, birthDate: input.caseValue.calculationSpec.birthDate, location: { latitude: input.caseValue.calculationSpec.latitude, longitude: input.caseValue.calculationSpec.longitude, timezoneId: input.caseValue.calculationSpec.timezoneId ?? null, timezoneOffsetHours: input.caseValue.calculationSpec.timezoneOffsetHours }, birthTimeSource: input.caseValue.calculationSpec.birthTimeSource ?? null, algorithmVersion: input.caseValue.algorithmVersion },
    conversation: { recentRawTurns: recent.map(({ question, answer }) => ({ question, answer })), earlierConversationSummary: summarizeEarlierTurns(input.turns) },
    eventLedger: input.events.map((event) => ({ eventId: event.eventId, revision: event.revision, summary: event.summary, rawText: event.rawText, domain: event.domain, eventKind: event.eventKind, subject: event.subject, relatedPerson: event.relatedPerson, dateRange: event.dateRange, scoreability: event.scoreability, status: latest.get(event.eventId) === event.revision ? "active" : "superseded" })),
    interviewState: { currentTargetEventId: input.currentTargetEventId, declinedDomains: [...new Set(input.turns.flatMap((turn) => turn.questionDomain && declinedPattern.test(turn.answer) ? [turn.questionDomain] : []))], unresolvedTargets: [...new Set([...(input.currentTargetEventId && ["unresolved", "answered_other_event"].includes(input.targetDisposition) ? [input.currentTargetEventId] : []), ...(input.pendingEvidence ?? []).flatMap((item) => item.targetEventId ? [item.targetEventId] : [])])], pendingEvidence: (input.pendingEvidence ?? []).filter((item) => !item.resolvedAt).map(({ rawText, reasonCode, targetEventId, createdAt }) => ({ rawText, reasonCode, targetEventId, createdAt })), askedTopics: input.turns.slice(-50).map((turn) => turn.question), turnCount: input.turns.length, targetDisposition: input.targetDisposition },
    candidateState: { hasSnapshot: Boolean(input.snapshot), publicRangeAllowed, rangeChanged: input.previousSnapshot?.clusters[0]?.startTime !== input.snapshot?.clusters[0]?.startTime || input.previousSnapshot?.clusters[0]?.endTime !== input.snapshot?.clusters[0]?.endTime, topClusters: (input.snapshot?.clusters ?? []).slice(0, 4).map((cluster) => ({ rank: cluster.rank, widthMinutes: cluster.widthMinutes, stability: publicRangeAllowed ? "stable" : "unstable" })), contrasts: (input.diagnostics?.candidateSplits ?? []).map((split) => ({ techniqueLayers: split.techniqueLayers, relevantEventIds: split.eventIds })), contrastIntelligence: buildCandidateContrastPacket({ events: input.events, snapshot: input.snapshot, diagnostics: input.diagnostics }), eventDiagnostics: (input.diagnostics?.eventDateSensitivity ?? []).map((item) => ({ eventId: item.eventId, winnerRetentionRate: item.winnerRetentionRate, scoreVariance: item.scoreVariance })), gateReasons: input.snapshot?.gateReasons ?? [], currentSnapshotId: input.snapshot?.id ?? null },
    runtime: {
      revision: 0,
      observations: [],
      hypotheses: (input.snapshot?.clusters ?? []).slice(0, 4).map((cluster) => {
        const candidate = input.snapshot?.candidates.find((item) => item.time === cluster.representativeTime);
        return { candidateRank: cluster.rank, supportingEventIds: candidate?.supportingEventIds ?? [], conflictingEventIds: candidate?.conflictingEventIds ?? [] };
      }),
    },
    capabilities: {
      supportedDomains: domains,
      supportedEventKinds: kinds,
      publicTechniqueCapabilities: domains.map((domain) => ({ domain, techniqueLayers: [...domainScorerRegistry[domain].techniqueLayers] })),
      maxQuestionsPerTurn: 1,
      maxToolRounds: 10,
      forbiddenPublicClaims: ["exact_birth_minute", "private_scores", "internal_ids", "raw_technique_trace", "ungrounded_numeric_structure"],
    },
  });
}

function latestGroundedEvent(dossier: RectificationCaseDossier, latestAnswer: string) {
  return [...dossier.eventLedger].reverse().find((event) => event.status === "active" && (event.rawText === latestAnswer || latestAnswer.includes(event.summary))) ?? null;
}

function fallback(dossier: RectificationCaseDossier, latestAnswer: string): RectificationTurnPlan {
  if (dossier.candidateState.publicRangeAllowed && dossier.candidateState.currentSnapshotId) return { contractVersion: "rectification-turn-plan-v1", targetDisposition: dossier.interviewState.targetDisposition, evidenceProposals: [], action: { type: "offer_candidate_range", snapshotId: dossier.candidateState.currentSnapshotId }, publicReply: { acknowledgement: "现有事件已经完成本轮复核。", evidenceExplanation: null, candidateCommentary: "候选范围已通过当前稳定性门槛，可以作为工作范围查看。", limitation: "这仍不是对某个精确出生分钟的确认。" }, publicExplanationGrounding: [] };
  const targetEventId = dossier.interviewState.currentTargetEventId;
  const keepTarget = Boolean(targetEventId && ["unresolved", "answered_other_event"].includes(dossier.interviewState.targetDisposition));
  const targetEvent = keepTarget ? dossier.eventLedger.find((event) => event.eventId === targetEventId && event.status === "active") : null;
  const groundedEvent = latestGroundedEvent(dossier, latestAnswer);
  const safeSummary = groundedEvent && !privatePattern.test(groundedEvent.summary) && !containsExactMinute(groundedEvent.summary)
    ? groundedEvent.summary.slice(0, 120)
    : null;
  const safeTargetSummary = targetEvent && !privatePattern.test(targetEvent.summary) && !containsExactMinute(targetEvent.summary)
    ? `“${targetEvent.summary.slice(0, 120)}”`
    : "刚才那件事";
  const targetNeedsMonth = targetEvent?.dateRange.precision === "year" || targetEvent?.dateRange.precision === "quarter";
  const targetQuestion = targetNeedsMonth
    ? `${safeTargetSummary}大概发生在哪个月，或一年中的哪个时间段？`
    : `关于${safeTargetSummary}，你还记得更具体的时间或阶段吗？`;
  const question = keepTarget ? targetQuestion : "你愿意再讲一件与已有记录不同、时间大致明确的经历吗？没有、记不清或不想回答也可以换个方向。";
  const focus = keepTarget
    ? { mode: "clarify_existing_event" as const, targetEventId, domain: targetEvent?.domain ?? null, requestedFacts: [targetNeedsMonth ? "month" as const : "day_or_period" as const], rationaleCodes: ["unresolved_current_event"] }
    : { mode: "collect_independent_event" as const, targetEventId: null, domain: null, requestedFacts: ["independent_event" as const, "year" as const], rationaleCodes: ["model_unavailable_neutral_fallback"] };
  const techniqueLayers = groundedEvent ? domainScorerRegistry[groundedEvent.domain].techniqueLayers : [];
  const evidenceExplanation = safeSummary && techniqueLayers.length
    ? `按当前校正能力，这类事件通常会参考 ${techniqueLayers.join("、")}；这里只是在说明方法映射，尚未把它写成某个候选时间的计算结论。`
    : safeSummary ? "这条经历提供了可核对的时间和变化类型；目前只是整理证据，还不是候选时间的计算结论。" : null;
  return {
    contractVersion: "rectification-turn-plan-v1",
    targetDisposition: dossier.interviewState.targetDisposition,
    evidenceProposals: [],
    action: { type: "ask_question", focus, question, optionalQuickReplies: [] },
    publicReply: {
      acknowledgement: safeSummary ? `你提到的是“${safeSummary}”。` : latestAnswer.trim() ? "我会保留你刚才的原始说法，不补写你没有确认的信息。" : "我们先从真实经历建立事件线索。",
      evidenceExplanation,
      candidateCommentary: safeSummary ? "这条线索有明确时间，也说明了具体发生的变化，可以和其他独立经历交叉比较候选范围。" : null,
      limitation: null,
    },
    publicExplanationGrounding: groundedEvent ? [{ source: "capability_matrix", factKey: `domain:${groundedEvent.domain}` }] : [],
  };
}

export function validateRectificationTurnPlan(input: Readonly<{ plan: unknown; dossier: RectificationCaseDossier; latestAnswer: string; phase: "evidence" | "final" }>): Readonly<{ plan: RectificationTurnPlan | null; issues: readonly string[] }> {
  const parsed = rectificationTurnPlanSchema.safeParse(input.plan);
  if (!parsed.success) return { plan: null, issues: ["turn_plan_schema_invalid"] };
  const plan = parsed.data;
  const issues: string[] = [];
  const known = new Set(input.dossier.eventLedger.map((event) => event.eventId));
  plan.evidenceProposals.forEach((proposal) => {
    if (!input.latestAnswer.includes(proposal.sourceSpan)) issues.push("evidence_source_not_in_latest_answer");
    if (proposal.dateText && !input.latestAnswer.includes(proposal.dateText)) issues.push("evidence_date_not_in_latest_answer");
    if (proposal.operation === "create" && proposal.targetEventId) issues.push("create_must_not_target_event");
    if ((proposal.operation === "revise_date" || proposal.operation === "reclassify") && (!proposal.targetEventId || !known.has(proposal.targetEventId))) issues.push("revision_target_invalid");
  });
  const currentTarget = input.dossier.interviewState.currentTargetEventId;
  if (input.phase === "final") {
    if (plan.evidenceProposals.length) issues.push("final_plan_contains_evidence");
    if (plan.targetDisposition !== input.dossier.interviewState.targetDisposition) issues.push("final_target_disposition_changed");
  } else if (!currentTarget && plan.targetDisposition !== "not_applicable") {
    issues.push("target_disposition_requires_target");
  } else if (currentTarget) {
    const revisedCurrentTarget = plan.evidenceProposals.some((proposal) => (proposal.operation === "revise_date" || proposal.operation === "reclassify") && proposal.targetEventId === currentTarget);
    const createdOtherEvent = plan.evidenceProposals.some((proposal) => proposal.operation === "create");
    if (plan.targetDisposition === "not_applicable") issues.push("target_disposition_missing");
    if (plan.targetDisposition === "resolved" && !revisedCurrentTarget) issues.push("resolved_target_not_revised");
    if (plan.targetDisposition === "answered_other_event" && !createdOtherEvent) issues.push("other_event_not_proposed");
  }
  const publicText = [plan.publicReply.acknowledgement, plan.publicReply.evidenceExplanation, plan.publicReply.candidateCommentary, plan.publicReply.limitation, plan.action.type === "ask_question" ? plan.action.question : null].filter(Boolean).join(" ");
  if (privatePattern.test(publicText)) issues.push("private_detail_exposed");
  if (containsExactMinute(publicText)) issues.push("exact_minute_claimed");
  const groundedEvent = latestGroundedEvent(input.dossier, input.latestAnswer);
  const capabilityFacts = new Map(input.dossier.capabilities.publicTechniqueCapabilities.map((item) => [`domain:${item.domain}`, item]));
  const observationFacts = new Map<"window_sensitivity" | "candidate_scan" | "diagnostic", Set<string>>([
    ["window_sensitivity", new Set()], ["candidate_scan", new Set()], ["diagnostic", new Set()],
  ]);
  input.dossier.runtime.observations.forEach((observation) => {
    if (observation.outcome !== "succeeded") return;
    const direct = Object.keys(observation.result);
    const window = observation.result.windowSensitivity;
    if (window && typeof window === "object" && !Array.isArray(window)) {
      Object.keys(window as Record<string, unknown>).forEach((key) => observationFacts.get("window_sensitivity")?.add(key));
    }
    if (observation.tool === "candidate_scan") direct.forEach((key) => observationFacts.get("candidate_scan")?.add(key));
    if (observation.tool === "diagnostic_read") direct.forEach((key) => observationFacts.get("diagnostic")?.add(key));
  });
  plan.publicExplanationGrounding.forEach((grounding) => {
    if (grounding.source === "capability_matrix") {
      const capability = capabilityFacts.get(grounding.factKey);
      if (!capability || (groundedEvent && capability.domain !== groundedEvent.domain)) issues.push("public_grounding_invalid");
      return;
    }
    if (!observationFacts.get(grounding.source)?.has(grounding.factKey)) issues.push("public_grounding_invalid");
  });
  if (groundedEvent && plan.publicReply.evidenceExplanation) {
    const citedCapabilities = plan.publicExplanationGrounding.flatMap((grounding) => {
      const capability = grounding.source === "capability_matrix" ? capabilityFacts.get(grounding.factKey) : null;
      return capability && capability.domain === groundedEvent.domain ? [capability] : [];
    });
    const allowedTechniques = new Set(citedCapabilities.flatMap((item) => item.techniqueLayers.map((layer) => layer.toLocaleLowerCase())));
    const knownTechniques = [...new Set([
      ...input.dossier.capabilities.publicTechniqueCapabilities.flatMap((item) => item.techniqueLayers),
      "KP", "Shadbala", "Ashtakavarga", "Chaturvimshamsha",
    ])];
    if (knownTechniques.some((technique) => mentionsTechnique(plan.publicReply.evidenceExplanation ?? "", technique)
      && !allowedTechniques.has(technique.toLocaleLowerCase()))) issues.push("public_technique_not_grounded");
  }
  if (quantifiedStructurePattern.test(publicText)) {
    const windowFactKeys = new Set(plan.publicExplanationGrounding.filter((item) => item.source === "window_sensitivity").map((item) => item.factKey));
    const observedFactKeys = observationFacts.get("window_sensitivity") ?? new Set<string>();
    if (![...windowFactKeys].some((factKey) => observedFactKeys.has(factKey))) issues.push("ungrounded_numeric_structure_claim");
  }
  if (plan.action.type === "ask_question") {
    if (asksMultipleQuestions(plan.action.question)) issues.push("multiple_questions");
    const nextQuestion = normalizedQuestion(plan.action.question);
    if (nextQuestion && input.dossier.interviewState.askedTopics.some((question) => normalizedQuestion(question).endsWith(nextQuestion))) issues.push("question_repeated");
    if (input.phase === "final" && groundedEvent) {
      if (genericAcknowledgementPattern.test(plan.publicReply.acknowledgement.trim())) issues.push("event_acknowledgement_generic");
      if (!plan.publicReply.evidenceExplanation || plan.publicReply.evidenceExplanation.trim().length < 12) issues.push("event_explanation_missing");
      if (!plan.publicReply.candidateCommentary || plan.publicReply.candidateCommentary.trim().length < 12) issues.push("event_value_commentary_missing");
    }
    if (plan.action.focus.targetEventId && !known.has(plan.action.focus.targetEventId)) issues.push("focus_target_invalid");
    if (plan.action.focus.domain && input.dossier.interviewState.declinedDomains.includes(plan.action.focus.domain)) issues.push("declined_domain_reopened");
    if (currentTarget && ["unresolved", "answered_other_event"].includes(plan.targetDisposition)
      && plan.action.focus.targetEventId !== currentTarget) issues.push("unresolved_target_abandoned");
    if (["unknown", "declined", "direction_change"].includes(plan.targetDisposition)
      && (plan.action.focus.targetEventId === input.dossier.interviewState.currentTargetEventId
        || ["clarify_existing_event", "resolve_conflict"].includes(plan.action.focus.mode))) issues.push("declined_target_reopened");
  }
  if (plan.action.type === "offer_candidate_range" && (!input.dossier.candidateState.publicRangeAllowed || plan.action.snapshotId !== input.dossier.candidateState.currentSnapshotId)) issues.push("candidate_range_gate_failed");
  return { plan: issues.length ? null : plan, issues };
}

export async function regenerateDirectorQuestion(input: Readonly<{
  caseValue: RectificationV4Case;
  currentQuestion: string;
  latestAnswer: string;
  acceptedEvents: readonly LifeEventRevision[];
  focus: Extract<RectificationTurnPlan["action"], { type: "ask_question" }>["focus"];
  generateQuestion?: (prompt: string, phase: "regenerate" | "repair") => Promise<Generated>;
}>): Promise<string> {
  const model = (input.caseValue.orchestrationModelId ? resolveLanguageModel(input.caseValue.orchestrationModelId) : null) ?? defaultLanguageModel();
  const agent = model ? new Agent({ id: `rectification-director-regenerate-${model.id}`, name: "Birth Time Rectification Director", model: model.model, skills: [skillPath], instructions: "Rewrite one natural interview question while preserving the supplied structured focus. Do not expose internal ids, scores, tools, or a birth minute. Return only structured output." }) : null;
  const skillReady = agent ? assertRectificationSkillLoaded(agent, { caseId: input.caseValue.id, modelId: model?.id ?? null, deploymentSha: process.env.DEPLOYMENT_SHA?.trim() || null }) : null;
  const generate = input.generateQuestion ?? (async (prompt: string) => {
    if (!agent || !skillReady) throw new Error("director_model_unavailable");
    await skillReady;
    return agent.generate(prompt, { structuredOutput: { schema: regeneratedQuestionSchema, jsonPromptInjection: "inline" } });
  });
  const validate = (value: unknown) => {
    const parsed = regeneratedQuestionSchema.safeParse(value);
    if (!parsed.success) return { question: null, issues: ["question_schema_invalid"] };
    const issues: string[] = [];
    if (asksMultipleQuestions(parsed.data.question)) issues.push("multiple_questions");
    if (privatePattern.test(parsed.data.question)) issues.push("private_detail_exposed");
    if (containsExactMinute(parsed.data.question)) issues.push("exact_minute_claimed");
    return { question: issues.length ? null : parsed.data.question, issues };
  };
  try {
    const context = { task: "Rewrite the current question without changing its structured focus.", currentQuestion: input.currentQuestion, latestAnswer: input.latestAnswer, focus: input.focus, acceptedEvents: input.acceptedEvents.map(({ summary, domain, eventKind, dateRange }) => ({ summary, domain, eventKind, dateRange })) };
    let result = validate((await generate(JSON.stringify(context), "regenerate")).object);
    if (!result.question) result = validate((await generate(JSON.stringify({ ...context, task: "Repair the rejected rewrite once.", validationIssues: result.issues }), "repair")).object);
    return result.question ?? input.currentQuestion;
  } catch {
    return input.currentQuestion;
  }
}

export async function runRectificationDirector(input: Readonly<{ caseValue: RectificationV4Case; dossier: RectificationCaseDossier; latestAnswer: string; phase: "evidence" | "final"; diagnostics: DiagnosticsSummary; timeoutMs?: number; generatePlan?: RectificationDirectorGenerator }>) {
  const started = Date.now();
  const model = (input.caseValue.orchestrationModelId ? resolveLanguageModel(input.caseValue.orchestrationModelId) : null) ?? defaultLanguageModel();
  const agent = model ? new Agent({ id: `rectification-director-${model.id}`, name: "Birth Time Rectification Director", model: model.model, skills: [skillPath], instructions: `Direct the interview from the server-owned dossier and tool observations. Propose every explicit event in the latest answer, independently choose the current focus and wording from the full ledger, declined domains, candidate contrasts, and observations, and write the public reply plus at most one natural question. Do not follow a fixed domain rotation or treat examples, tests, or prior wording as a script. In final planning, use the server-owned read-only tools to inspect the case, candidate scan, evidence gaps, or one diagnostic at a time. Adapt after every observation, never repeat an immutable tool call in the same run, and converge as soon as another tool adds no value. ${groundedPublicReplyRequirement} Never write scores, internal ids, profile values, candidate minutes, status, phase, or database mutations. Return strict structured output.` }) : null;
  const skillReady = agent ? assertRectificationSkillLoaded(agent, { caseId: input.caseValue.id, modelId: model?.id ?? null, deploymentSha: process.env.DEPLOYMENT_SHA?.trim() || null }) : null;
  const generate = input.generatePlan ?? (async (prompt: string) => {
    if (!agent || !skillReady) throw new Error("director_model_unavailable");
    await skillReady;
    return agent.generate(prompt, { abortSignal: AbortSignal.timeout(input.timeoutMs ?? 25_000), structuredOutput: { schema: rectificationTurnPlanSchema, jsonPromptInjection: "inline" } });
  });
  let inputTokens = 0, outputTokens = 0;
  let usageObserved = false;
  const toolCalls: ToolCallTrace[] = [];
  let dossier = input.dossier;
  const addUsage = async (generated: Generated) => {
    if (!generated.totalUsage) return;
    const usage = await generated.totalUsage;
    inputTokens += Math.max(0, Math.trunc(usage.inputTokens ?? 0));
    outputTokens += Math.max(0, Math.trunc(usage.outputTokens ?? 0));
    usageObserved = true;
  };
  const requestedTool = (action: RectificationTurnPlan["action"]): Readonly<{ tool: RectificationAgentTool; diagnostic: RectificationDiagnostic | null }> | null => {
    if (action.type === "request_tool") {
      if ((action.tool === "diagnostic_read") !== Boolean(action.diagnostic)) throw new Error("director_tool_request_invalid");
      return { tool: action.tool, diagnostic: action.diagnostic };
    }
    if (action.type === "request_diagnostic") return { tool: "diagnostic_read", diagnostic: action.diagnostic };
    return null;
  };
  const toolKey = (request: Readonly<{ tool: RectificationAgentTool; diagnostic: RectificationDiagnostic | null }>) => `${request.tool}:${request.diagnostic ?? ""}`;
  const promptDossier = () => input.phase === "evidence" ? dossier : {
    interviewState: { askedTopics: dossier.interviewState.askedTopics },
    runtime: { revision: dossier.runtime.revision, observations: dossier.runtime.observations },
    capabilities: dossier.capabilities,
    availableTools: {
      readOnly: ["case_read", "candidate_scan", "evidence_gap"],
      diagnostics: ["leave_one_event_out", "leave_one_domain_out", "date_sensitivity", "neighbor_stability", "candidate_split"],
    },
  };
  const executeTool = (request: Readonly<{ tool: RectificationAgentTool; diagnostic: RectificationDiagnostic | null }>, round: number): ToolObservation => {
    const result = request.tool === "case_read"
      ? { case: dossier.case, conversation: dossier.conversation, eventLedger: dossier.eventLedger, interviewState: dossier.interviewState }
      : request.tool === "candidate_scan"
        ? { candidateState: dossier.candidateState, hypotheses: dossier.runtime.hypotheses }
        : request.tool === "evidence_gap"
          ? { pendingEvidence: dossier.interviewState.pendingEvidence, contrastIntelligence: dossier.candidateState.contrastIntelligence, hypotheses: dossier.runtime.hypotheses }
          : { diagnostic: request.diagnostic, result: diagnosticResult(request.diagnostic!, input.diagnostics) };
    return { round, tool: request.tool, diagnostic: request.diagnostic, outcome: "succeeded", result, dossierRevision: dossier.runtime.revision + 1, errorCode: null };
  };
  try {
    const first = await generate(JSON.stringify({ task: input.phase === "evidence" ? "Interpret the latest answer and propose every explicit event. The action is provisional." : "Choose the final action and public response. evidenceProposals must be empty. Use a read-only tool only when its observation can materially change the next action.", publicReplyRequirement: input.phase === "final" ? groundedPublicReplyRequirement : undefined, latestAnswer: input.latestAnswer, dossier: promptDossier() }), input.phase);
    await addUsage(first);
    let candidate = rectificationTurnPlanSchema.parse(first.object);
    const observedTools = new Set<string>();
    let convergenceReason: "tool_repeated" | "tool_round_limit" | null = null;
    let request = requestedTool(candidate.action);
    while (input.phase === "final" && request) {
      const key = toolKey(request);
      if (observedTools.has(key)) {
        convergenceReason = "tool_repeated";
        break;
      }
      if (toolCalls.length >= dossier.capabilities.maxToolRounds) {
        convergenceReason = "tool_round_limit";
        break;
      }
      const toolStarted = Date.now();
      const observation = executeTool(request, toolCalls.length + 1);
      observedTools.add(key);
      dossier = rectificationCaseDossierSchema.parse({
        ...dossier,
        runtime: { ...dossier.runtime, revision: observation.dossierRevision, observations: [...dossier.runtime.observations, observation] },
      });
      toolCalls.push({ tool: request.tool, diagnostic: request.diagnostic, outcome: observation.outcome, durationMs: Date.now() - toolStarted, errorCode: observation.errorCode });
      const next = await generate(JSON.stringify({
        task: "Read the updated dossier and latest observation. Request another unobserved read-only tool only if it can materially change the interview strategy; otherwise converge to one final non-tool action. evidenceProposals must stay empty.",
        publicReplyRequirement: groundedPublicReplyRequirement,
        latestAnswer: input.latestAnswer,
        dossier: promptDossier(),
        latestObservation: observation,
        loopState: { round: toolCalls.length, maxRounds: dossier.capabilities.maxToolRounds, observedTools: [...observedTools] },
      }), "after_observation");
      await addUsage(next);
      candidate = rectificationTurnPlanSchema.parse(next.object);
      request = requestedTool(candidate.action);
    }
    if (input.phase === "final" && requestedTool(candidate.action)) {
      const converged = await generate(JSON.stringify({
        task: "The tool loop has reached its convergence boundary. Return one safe final non-tool action now; do not request another tool and keep evidenceProposals empty.",
        publicReplyRequirement: groundedPublicReplyRequirement,
        latestAnswer: input.latestAnswer,
        dossier: promptDossier(),
        loopState: { round: toolCalls.length, maxRounds: dossier.capabilities.maxToolRounds, observedTools: [...observedTools], convergenceReason: convergenceReason ?? "tool_round_limit" },
      }), "converge");
      await addUsage(converged);
      candidate = rectificationTurnPlanSchema.parse(converged.object);
      if (requestedTool(candidate.action)) throw new Error("director_final_plan_not_final");
    }
    let validated = validateRectificationTurnPlan({ plan: candidate, dossier, latestAnswer: input.latestAnswer, phase: input.phase });
    if (!validated.plan) {
      const repaired = await generate(JSON.stringify({ task: "Repair the rejected plan once. Preserve grounded facts, return one safe final plan, and address every validation issue.", publicReplyRequirement: input.phase === "final" ? groundedPublicReplyRequirement : undefined, latestAnswer: input.latestAnswer, dossier: promptDossier(), rejectedPlan: candidate, validationIssues: validated.issues }), "repair");
      await addUsage(repaired);
      candidate = rectificationTurnPlanSchema.parse(repaired.object);
      if (requestedTool(candidate.action)) throw new Error("director_repair_requested_tool");
      validated = validateRectificationTurnPlan({ plan: candidate, dossier, latestAnswer: input.latestAnswer, phase: input.phase });
    }
    if (!validated.plan) throw new Error(`director_plan_rejected:${validated.issues.join(",")}`);
    return { plan: validated.plan, dossier, mode: "agent" as const, fallbackReason: null, toolCalls, inputTokenCount: usageObserved ? inputTokens : null, outputTokenCount: usageObserved ? outputTokens : null, latencyMs: Date.now() - started };
  } catch (error) {
    return { plan: fallback(dossier, input.latestAnswer), dossier, mode: "deterministic_fallback" as const, fallbackReason: error instanceof Error ? error.message.slice(0, 120) : "director_failed", toolCalls, inputTokenCount: usageObserved ? inputTokens : null, outputTokenCount: usageObserved ? outputTokens : null, latencyMs: Date.now() - started };
  }
}
