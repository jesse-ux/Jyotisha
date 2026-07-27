import { randomUUID } from "node:crypto";
import type { EvidenceDomain, LifeEventRevision, RectificationV4Question } from "./contracts.ts";
import { scoreableEvents } from "./evidence-ledger.ts";

const domainOrder: readonly EvidenceDomain[] = [
  "education", "relocation", "relationship", "career", "finance", "health_pressure", "family",
];
const recallCost: Readonly<Record<EvidenceDomain, number>> = {
  education: 1, relocation: 1, relationship: 1, career: 1, finance: 2, health_pressure: 2, family: 2, other: 3,
};
const prompts: Readonly<Record<EvidenceDomain, string>> = {
  education: "请说一件你记得最清楚的升学、复读、转学或毕业事件，并给出尽可能准确的年月。",
  relocation: "请说一次影响较大的搬家或长期迁居，并给出尽可能准确的年月。",
  relationship: "请说一段重要关系明确开始或结束的时间；开始和结束请分开说。",
  career: "请说一次明确的入职、离职、转行或职责突变，并给出尽可能准确的年月。",
  finance: "请说一次明显的收入、负债或资产变化，并给出尽可能准确的年月。",
  health_pressure: "请说一次明确的疾病、手术、事故或长期压力起点，并给出尽可能准确的年月。",
  family: "请说一件对你影响很大的家庭事件和时间；这一类先作为背景，不直接参与评分。",
  other: "请再补充一件日期明确、对人生方向影响较大的事件；如果暂时想不到，也可以回复“暂停”。",
};

function refinementQuestion(event: LifeEventRevision, id?: string): RectificationV4Question {
  return {
    id: id ?? randomUUID(),
    domain: event.domain,
    targetEventId: event.eventId,
    prompt: `你之前提到“${event.summary.slice(0, 120)}”，目前时间是${event.dateRange.label}。如果记得，请补充更具体的日期；不记得可以回复“跳过”。`,
    recallCost: "medium",
    reason: "缩小已有事件的日期范围，用于检验候选时间对日期误差是否稳定。",
  };
}

export function planNextQuestion(input: {
  readonly askedDomains: readonly EvidenceDomain[];
  readonly coveredDomains: readonly EvidenceDomain[];
  readonly candidateSplitByDomain?: Readonly<Partial<Record<EvidenceDomain, number>>>;
  readonly events?: readonly LifeEventRevision[];
  readonly attemptedRefinementEventIds?: readonly string[];
  readonly id?: string;
}): RectificationV4Question {
  const asked = new Set(input.askedDomains);
  const covered = new Set(input.coveredDomains);
  const candidates = domainOrder.filter((domain) => !asked.has(domain));
  if (candidates.length > 0) {
    candidates.sort((left, right) => {
      const leftValue = (input.candidateSplitByDomain?.[left] ?? 0) + (covered.has(left) ? 0 : 1) - recallCost[left] * 0.1;
      const rightValue = (input.candidateSplitByDomain?.[right] ?? 0) + (covered.has(right) ? 0 : 1) - recallCost[right] * 0.1;
      return rightValue - leftValue || domainOrder.indexOf(left) - domainOrder.indexOf(right);
    });
    const domain = candidates[0]!;
    const cost = recallCost[domain] === 1 ? "low" : recallCost[domain] === 2 ? "medium" : "high";
    return {
      id: input.id ?? randomUUID(),
      domain,
      targetEventId: null,
      prompt: prompts[domain],
      recallCost: cost,
      reason: input.candidateSplitByDomain?.[domain]
        ? "该领域最能区分当前候选时间，同时回忆成本较低。"
        : "先收集高回忆率、可核对日期的人生事件。",
    };
  }

  const attempted = new Set(input.attemptedRefinementEventIds ?? []);
  const target = scoreableEvents(input.events ?? [])
    .filter((event) => event.dateRange.precision !== "day" && !attempted.has(event.eventId))
    .sort((left, right) => left.createdAt.localeCompare(right.createdAt) || left.eventId.localeCompare(right.eventId))[0];
  if (target) return refinementQuestion(target, input.id);

  return {
    id: input.id ?? randomUUID(),
    domain: "other",
    targetEventId: null,
    prompt: prompts.other,
    recallCost: "high",
    reason: "现有事件仍不足以通过稳定性门槛，需要新的明确日期证据，或由用户主动暂停。",
  };
}

export function openingQuestion(id?: string): RectificationV4Question {
  return planNextQuestion({ askedDomains: [], coveredDomains: [], id });
}
