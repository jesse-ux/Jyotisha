import { createHash } from "node:crypto";
import type { CandidateSnapshot, EvidenceDomain, LifeEventRevision, RectificationV4Turn } from "../rectification-v4/contracts.ts";
import { domainScorerRegistry } from "../rectification-v4/domain-scorers.ts";
import { chronologicalEvents, latestEventRevisions } from "../rectification-v4/evidence-ledger.ts";
import type { TargetDisposition } from "../rectification-v4/extraction.ts";
import type { CandidateContrastPacket, DiagnosticsSummary, QuestionOpportunity, SemanticQuestionOpportunity } from "./contracts.ts";

const forbiddenMoves: SemanticQuestionOpportunity["forbiddenMoves"] = [
  "switch_target_event", "ask_multiple_questions", "claim_exact_birth_minute", "invent_event",
  "invent_date", "expose_private_score", "expose_internal_id", "expose_technique_trace",
];

function stableUuid(value: string): string {
  const hex = createHash("sha256").update(value).digest("hex").slice(0, 32).split("");
  hex[12] = "4";
  hex[16] = ((Number.parseInt(hex[16]!, 16) & 3) | 8).toString(16);
  return `${hex.slice(0, 8).join("")}-${hex.slice(8, 12).join("")}-${hex.slice(12, 16).join("")}-${hex.slice(16, 20).join("")}-${hex.slice(20).join("")}`;
}

const routingValue: Record<QuestionOpportunity["kind"], number> = {
  clarify_intake: .18,
  resolve_event_conflict: .16,
  clarify_event_subject: .14,
  refine_event_date: .08,
  pair_related_event: .05,
  disambiguate_candidate_split: .04,
  ask_new_event: 0,
};

type OpportunityInput = Omit<SemanticQuestionOpportunity, "contractVersion" | "opportunityId" | "utility" | "active" | "forbiddenMoves">;

function utility(value: OpportunityInput, contrastPriority = 0): number {
  return Number((
    .35 * value.expectedInformationGain + .20 * value.dateSensitivity + .15 * value.candidateSplitRelevance
    + .10 * value.domainCoverageGain + .10 * value.recallEase + .10 * value.novelty
    + routingValue[value.kind] + contrastPriority - value.repetitionPenalty - value.privacyCost
  ).toFixed(6));
}

function opportunity(caseId: string, input: OpportunityInput, contrastPriority = 0): QuestionOpportunity {
  return {
    contractVersion: "semantic-question-v2",
    ...input,
    forbiddenMoves,
    opportunityId: stableUuid(`${caseId}:${input.kind}:${input.targetEventId ?? input.domain}:${input.goal}:${input.fallbackPrompt}`),
    utility: utility(input, contrastPriority),
    active: true,
  };
}

function daysWide(event: LifeEventRevision): number {
  return Math.floor((Date.parse(`${event.dateRange.end}T00:00:00Z`) - Date.parse(`${event.dateRange.start}T00:00:00Z`)) / 86_400_000) + 1;
}

function anchorFor(event: LifeEventRevision): string {
  return event.summary.replace(/[“”"']/g, "").trim().slice(0, 80);
}

function declinedSensitiveDomains(turns: readonly RectificationV4Turn[]): ReadonlySet<EvidenceDomain> {
  const result = new Set<EvidenceDomain>();
  for (const turn of turns) {
    if (turn.questionDomain && /不想说|不方便说|不想回答|跳过|这个不说|换个方向|不聊这个/.test(turn.answer)) result.add(turn.questionDomain);
  }
  return result;
}

const genericTechniqueLayers = new Set(["vimshottari", "narayana"]);

export function buildCandidateContrastPacket(input: Readonly<{
  events: readonly LifeEventRevision[];
  snapshot: CandidateSnapshot | null;
  diagnostics: DiagnosticsSummary | null;
}>): CandidateContrastPacket | null {
  const split = input.diagnostics?.candidateSplits[0];
  if (!split) return null;
  const discriminatingLayers = split.techniqueLayers.filter((layer) => !genericTechniqueLayers.has(layer.toLowerCase()));
  const existingKinds = new Set(latestEventRevisions(input.events)
    .filter((event) => event.scoreability === "scoreable")
    .map((event) => event.eventKind));
  const missingEvidence = (Object.entries(domainScorerRegistry) as [EvidenceDomain, (typeof domainScorerRegistry)[EvidenceDomain]][])
    .flatMap(([domain, policy]) => {
      if (!policy.techniqueLayers.some((layer) => discriminatingLayers.includes(layer))) return [];
      return policy.supportedKinds
        .filter((eventKind) => !existingKinds.has(eventKind))
        .map((eventKind) => ({ domain, eventKind, reason: "highest_candidate_separation" as const }));
    });
  return {
    primaryClusterRank: input.snapshot?.clusters[0]?.rank ?? null,
    secondaryClusterRank: input.snapshot?.clusters[1]?.rank ?? null,
    discriminatingLayers,
    relevantEventIds: [...split.eventIds],
    missingEvidence,
  };
}

export function buildQuestionOpportunities(input: Readonly<{
  caseId: string;
  events: readonly LifeEventRevision[];
  turns: readonly RectificationV4Turn[];
  snapshot: CandidateSnapshot | null;
  diagnostics: DiagnosticsSummary | null;
  targetDisposition?: TargetDisposition;
  retryTargetEventIds?: readonly string[];
}>): readonly QuestionOpportunity[] {
  const targetAttempts = new Map<string, number>();
  for (const turn of input.turns) {
    if (turn.questionTargetEventId) targetAttempts.set(turn.questionTargetEventId, (targetAttempts.get(turn.questionTargetEventId) ?? 0) + 1);
  }
  const retryTargets = new Set(input.retryTargetEventIds ?? []);
  const scoreableDomains = new Set(input.events.filter((event) => event.scoreability === "scoreable").map((event) => event.domain));
  const refusedDomains = declinedSensitiveDomains(input.turns);
  const latestEvent = chronologicalEvents(input.events).at(-1);
  const opportunities: QuestionOpportunity[] = [];
  const contrastPacket = buildCandidateContrastPacket(input);

  if (input.targetDisposition === "answered_other_event") {
    for (const eventId of retryTargets) {
      const event = input.events.find((value) => value.eventId === eventId);
      if (!event || (targetAttempts.get(eventId) ?? 0) > 1) continue;
      const anchor = anchorFor(event);
      opportunities.push(opportunity(input.caseId, {
        kind: "resolve_event_conflict", domain: event.domain, targetEventId: event.eventId,
        goal: `温和确认“${anchor}”尚缺的日期或主体；允许用户直接跳过。`,
        requestedFields: ["event_range"], anchors: [anchor], contextFacts: [`用户刚补充了另一件完整事件。`, `同一目标最多补问一次。`],
        fallbackPrompt: `关于“${anchor}”，如果还记得大概时间范围，可以补充一下吗？`,
        reason: "用户回答了另一件新事件，原目标只允许一次温和补问。",
        expectedInformationGain: .78, dateSensitivity: .7, candidateSplitRelevance: .55, domainCoverageGain: 0,
        recallEase: .72, novelty: .55, repetitionPenalty: .25, privacyCost: .05,
      }));
    }
  }

  const targetClosed = input.targetDisposition === "unknown"
    || input.targetDisposition === "declined"
    || input.targetDisposition === "direction_change";
  for (const event of input.events) {
    if (targetClosed && retryTargets.has(event.eventId)) continue;
    const attemptCount = targetAttempts.get(event.eventId) ?? 0;
    const anchor = anchorFor(event);
    if (event.subject === "other" && attemptCount === 0) {
      opportunities.push(opportunity(input.caseId, {
        kind: "clarify_event_subject", domain: event.domain, targetEventId: event.eventId,
        goal: `确认“${anchor}”发生在本人、家人还是伴侣。`, requestedFields: ["event_subject"],
        anchors: [anchor], contextFacts: [`当前主体为 ${event.subject}。`],
        fallbackPrompt: `“${anchor}”主要发生在你本人、家人还是伴侣身上？`,
        reason: "事件主体决定是否允许进入个人评分。",
        expectedInformationGain: .9, dateSensitivity: .2, candidateSplitRelevance: .3, domainCoverageGain: .2,
        recallEase: .95, novelty: .9, repetitionPenalty: 0, privacyCost: event.domain === "health_pressure" || event.domain === "family" ? .24 : .05,
      }));
    }
    if (event.scoreability !== "scoreable" || event.dateRange.precision === "day" || attemptCount > 0) continue;
    const sensitivity = input.diagnostics?.eventDateSensitivity.find((item) => item.eventId === event.eventId);
    const dateSensitive = Boolean(sensitivity && (sensitivity.winnerRetentionRate < .65 || sensitivity.candidateClusterRetentionRate < .65));
    const precision = event.dateRange.precision;
    const shouldRefine = precision === "quarter" || precision === "year" || (precision === "month" && dateSensitive)
      || (precision === "range" && daysWide(event) > 120 && dateSensitive);
    if (!shouldRefine) continue;
    const requestedFields: SemanticQuestionOpportunity["requestedFields"] = precision === "year" || precision === "quarter"
      ? ["event_month"]
      : precision === "range" ? ["event_range"] : ["event_day"];
    const fallbackPrompt = precision === "year" || precision === "quarter"
      ? `“${anchor}”大概发生在哪个月，或一年中的哪个时间段？`
      : precision === "range"
        ? `“${anchor}”的时间范围还能再缩小一些吗？`
        : `关于“${anchor}”，你还记得大概哪一天吗？`;
    opportunities.push(opportunity(input.caseId, {
      kind: "refine_event_date", domain: event.domain, targetEventId: event.eventId,
      goal: `仅在必要精度上细化“${anchor}”的日期。`, requestedFields, anchors: [anchor],
      contextFacts: [`现有精度为 ${precision}。`, ...(sensitivity ? [`候选保持率 ${sensitivity.candidateClusterRetentionRate}。`] : [])],
      fallbackPrompt, reason: dateSensitive ? "日期敏感性诊断显示该事件可能改变候选排序。" : "当前日期范围较宽。",
      expectedInformationGain: sensitivity ? 1 - sensitivity.winnerRetentionRate : .66,
      dateSensitivity: sensitivity ? 1 - sensitivity.candidateClusterRetentionRate : .55,
      candidateSplitRelevance: .55, domainCoverageGain: 0, recallEase: precision === "year" ? .8 : .62,
      novelty: .78, repetitionPenalty: 0, privacyCost: .05,
    }));
  }

  const split = input.diagnostics?.candidateSplits[0];
  if (split) {
    const target = input.events.find((event) => event.scoreability === "scoreable"
      && split.eventIds.includes(event.eventId)
      && (targetAttempts.get(event.eventId) ?? 0) === 0
      && !(targetClosed && retryTargets.has(event.eventId)));
    const anchor = target ? anchorFor(target) : null;
    if (target) opportunities.push(opportunity(input.caseId, {
      kind: "disambiguate_candidate_split", domain: target?.domain ?? "other", targetEventId: target?.eventId ?? null,
      goal: `确认“${anchor}”更接近开始、高峰还是正式结束。`,
      requestedFields: ["event_stage"], anchors: [anchor!],
      contextFacts: [`候选分歧涉及 ${split.techniqueLayers.length} 个已计算技术层。`],
      fallbackPrompt: `“${anchor}”当时更接近事情开始、达到高峰，还是正式结束？`,
      reason: "候选簇在现有诊断中出现可检验分歧。",
      expectedInformationGain: .88, dateSensitivity: .45, candidateSplitRelevance: .95, domainCoverageGain: 0,
      recallEase: .65, novelty: .9, repetitionPenalty: 0, privacyCost: .1,
    }));
  }

  const scoreableCount = input.events.filter((event) => event.scoreability === "scoreable").length;
  const latestAnchor = latestEvent ? anchorFor(latestEvent) : null;
  const contrastEvidence = contrastPacket?.missingEvidence.filter((item) => !refusedDomains.has(item.domain)) ?? [];
  opportunities.push(opportunity(input.caseId, {
    kind: "ask_new_event",
    domain: "other",
    targetEventId: null,
    goal: "根据完整事件账本、用户拒答记录和候选差异，自主选择最有区分力且不重复的经历方向，再自然询问一件大致时间明确的新经历；不要按固定领域顺序轮询。",
    requestedFields: ["new_dated_event"],
    anchors: latestAnchor ? [latestAnchor] : [],
    contextFacts: [
      `已有 ${scoreableCount} 件可评分事件。`,
      `已覆盖领域：${[...scoreableDomains].sort().join(", ") || "无"}。`,
      `已拒绝领域：${[...refusedDomains].sort().join(", ") || "无"}。`,
      ...contrastEvidence.map((item) => `候选差异诊断建议优先考虑 ${item.domain}/${item.eventKind} 类型的独立证据；这是策略线索，不是必须照抄的公开问题。`),
      "由 Agent 自主决定下一方向和措辞，不使用预写领域问题、关键词命中或测试样例作为脚本。",
      "这是存在性询问，不得假定用户一定经历过该事件。",
      "只询问一件带大致时间的新事件，不要求用户逐项回答例子。",
      "允许用户回答没有、记不清、不想回答或换方向。",
      "不得发明年龄或日期窗口，只能引用 anchors 中已确认的经历。",
    ],
    fallbackPrompt: `${latestAnchor ? `在“${latestAnchor}”之外，` : ""}你愿意再讲一件与已有经历不同、时间大致明确的经历吗？没有、记不清或不想回答也可以换个方向。`,
    reason: contrastEvidence.length ? "候选差异仍需要新的独立证据，由 Agent 决定最有价值的询问方向。" : "仍需要一件与现有记录不同的独立事件，由 Agent 决定询问方向。",
    expectedInformationGain: contrastEvidence.length ? .9 : .65,
    dateSensitivity: input.snapshot ? .5 : .35,
    candidateSplitRelevance: contrastEvidence.length ? .95 : input.diagnostics?.candidateSplits.length ? .58 : .42,
    domainCoverageGain: scoreableDomains.size < 2 ? 1 : .15,
    recallEase: .7,
    novelty: .9,
    repetitionPenalty: 0,
    privacyCost: 0,
  }, contrastEvidence.length ? .08 : 0));

  return opportunities
    .sort((left, right) => right.utility - left.utility || left.opportunityId.localeCompare(right.opportunityId))
    .slice(0, 5);
}
