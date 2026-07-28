import { createHash } from "node:crypto";
import type { CandidateSnapshot, EvidenceDomain, LifeEventRevision, RectificationV4Turn } from "../rectification-v4/contracts.ts";
import type { DiagnosticsSummary, QuestionOpportunity } from "./contracts.ts";

const domains: readonly EvidenceDomain[] = ["education", "relocation", "relationship", "career", "finance", "health_pressure"];

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

function utility(value: Omit<QuestionOpportunity, "opportunityId" | "utility" | "active">): number {
  return Number((
    .35 * value.expectedInformationGain + .20 * value.dateSensitivity + .15 * value.candidateSplitRelevance
    + .10 * value.domainCoverageGain + .10 * value.recallEase + .10 * value.novelty
    + routingValue[value.kind] - value.repetitionPenalty - value.privacyCost
  ).toFixed(6));
}

function opportunity(caseId: string, input: Omit<QuestionOpportunity, "opportunityId" | "utility" | "active">): QuestionOpportunity {
  const result = { ...input, opportunityId: stableUuid(`${caseId}:${input.kind}:${input.targetEventId ?? input.domain}:${input.prompt}`), utility: utility(input), active: true };
  return result;
}

export function buildQuestionOpportunities(input: Readonly<{
  caseId: string;
  events: readonly LifeEventRevision[];
  turns: readonly RectificationV4Turn[];
  snapshot: CandidateSnapshot | null;
  diagnostics: DiagnosticsSummary | null;
  retryTargetEventIds?: readonly string[];
}>): readonly QuestionOpportunity[] {
  const attempted = new Set(input.turns.flatMap((turn) => turn.questionTargetEventId ? [turn.questionTargetEventId] : []));
  const retryTargets = new Set(input.retryTargetEventIds ?? []);
  const scoreableDomains = new Set(input.events.filter((event) => event.scoreability === "scoreable").map((event) => event.domain));
  const opportunities: QuestionOpportunity[] = [];
  for (const eventId of retryTargets) {
    const event = input.events.find((value) => value.eventId === eventId);
    if (!event) continue;
    opportunities.push(opportunity(input.caseId, {
      kind: "resolve_event_conflict", domain: event.domain, targetEventId: event.eventId,
      prompt: `你刚才补充的新经历已经另行保存。关于“${event.summary}”的时间仍没有确定；如果记不清，可以直接说不知道。`,
      reason: "用户补充了另一件事，原事件的日期或主体仍待确认。",
      expectedInformationGain: .85, dateSensitivity: .75, candidateSplitRelevance: .6, domainCoverageGain: 0, recallEase: .8, novelty: .7, repetitionPenalty: .15, privacyCost: .05,
    }));
  }
  if (opportunities.length > 0) {
    return opportunities.sort((left, right) =>
      right.utility - left.utility
      || left.opportunityId.localeCompare(right.opportunityId));
  }
  for (const event of input.events) {
    if (retryTargets.has(event.eventId)) continue;
    if ((event.scoreability === "pending_review" || event.subject === "other") && !attempted.has(event.eventId)) {
      opportunities.push(opportunity(input.caseId, {
        kind: "clarify_event_subject", domain: event.domain, targetEventId: event.eventId,
        prompt: `你刚才提到“${event.summary}”，这件事主要发生在你本人，还是家人或伴侣身上？`, reason: "事件主体决定是否允许进入个人分盘评分。",
        expectedInformationGain: .9, dateSensitivity: .2, candidateSplitRelevance: .3, domainCoverageGain: .2, recallEase: .95, novelty: .9, repetitionPenalty: 0, privacyCost: .05,
      }));
    }
    if (event.scoreability === "scoreable" && event.dateRange.precision !== "day" && !attempted.has(event.eventId)) {
      const sensitivity = input.diagnostics?.eventDateSensitivity.find((item) => item.eventId === event.eventId);
      opportunities.push(opportunity(input.caseId, {
        kind: "refine_event_date", domain: event.domain, targetEventId: event.eventId,
        prompt: `关于“${event.summary}”，你还记得更具体的月份或日期吗？不确定也可以只说大概范围。`, reason: "日期采样显示这件事的时间精度可能影响候选排序。",
        expectedInformationGain: sensitivity ? 1 - sensitivity.winnerRetentionRate : .72,
        dateSensitivity: sensitivity ? 1 - sensitivity.candidateClusterRetentionRate : .7,
        candidateSplitRelevance: .55, domainCoverageGain: 0, recallEase: .72, novelty: .8, repetitionPenalty: 0, privacyCost: .05,
      }));
    }
  }
  const split = input.diagnostics?.candidateSplits[0];
  if (split) {
    const target = input.events.find((event) => split.eventIds.includes(event.eventId));
    opportunities.push(opportunity(input.caseId, {
      kind: "disambiguate_candidate_split", domain: target?.domain ?? "other", targetEventId: target?.eventId ?? null,
      prompt: target ? `围绕“${target.summary}”，当时最明显的转折是事情开始、达到高峰，还是正式结束？` : "剩余候选在同一事件的阶段上有差异：你记得当时更接近开始、达到高峰，还是正式结束吗？",
      reason: `候选簇在 ${split.techniqueLayers.slice(0, 3).join("、") || "技术层"} 上出现可检验分歧。`,
      expectedInformationGain: .88, dateSensitivity: .45, candidateSplitRelevance: .95, domainCoverageGain: 0, recallEase: .65, novelty: .9, repetitionPenalty: target && attempted.has(target.eventId) ? .35 : 0, privacyCost: .1,
    }));
  }
  const missingDomain = domains.find((domain) => !scoreableDomains.has(domain));
  if (missingDomain) {
    const prompts: Record<EvidenceDomain, string> = {
      education: "你人生中有没有一次入学、毕业、考试或专业变化，时间大致在什么时候？",
      relocation: "你有没有一次印象深刻的搬家、离乡或长期迁居？大致在什么时候？",
      relationship: "你有没有一段关系正式开始、结束或进入婚姻的明确时间点？",
      career: "你有没有一次入职、离职、升职、转行或创业的明确时间点？",
      finance: "你有没有一次收入、投资、负债或资产状况明显改变的时间点？",
      health_pressure: "你本人有没有一次住院、手术、事故或明显健康转折？大致在什么时候？",
      family: "请补充一个家庭事件。", other: "请补充一个有明确时间的重要人生事件。",
    };
    opportunities.push(opportunity(input.caseId, {
      kind: "ask_new_event", domain: missingDomain, targetEventId: null, prompt: prompts[missingDomain], reason: "当前证据领域覆盖不足。",
      expectedInformationGain: .7, dateSensitivity: .45, candidateSplitRelevance: .5, domainCoverageGain: 1, recallEase: .7, novelty: 1, repetitionPenalty: 0, privacyCost: missingDomain === "health_pressure" ? .2 : .08,
    }));
  }
  return opportunities.sort((left, right) =>
    right.utility - left.utility
    || left.opportunityId.localeCompare(right.opportunityId));
}
