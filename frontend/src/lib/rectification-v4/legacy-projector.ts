import { randomUUID } from "node:crypto";
import type { PublicMessage } from "../rectification-agent/contracts.ts";
import type { CandidateSnapshot, LifeEventRevision, RectificationV4Question } from "./contracts.ts";
import { scoreableEvents } from "./evidence-ledger.ts";

export function projectLegacyV4Question(input: Readonly<{
  events: readonly LifeEventRevision[];
  attemptedRefinementEventIds: readonly string[];
  latestAnswer: string;
  snapshot: CandidateSnapshot | null;
}>): RectificationV4Question | null {
  if (input.snapshot?.canAcceptRange) return null;
  const attempted = new Set(input.attemptedRefinementEventIds);
  const target = scoreableEvents(input.events)
    .filter((event) => !["day", "month"].includes(event.dateRange.precision) && !attempted.has(event.eventId))
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt) || left.eventId.localeCompare(right.eventId))[0];
  if (target) return {
    id: randomUUID(),
    domain: target.domain,
    targetEventId: target.eventId,
    prompt: `你刚才提到的“${target.summary.slice(0, 120)}”很重要。你目前记得的时间是${target.dateRange.label}；如果还能想起更具体的月份或日期，可以继续说，不确定也没关系。`,
    recallCost: "medium",
    reason: "V4 legacy projector：细化已有事件日期。",
  };
  return {
    id: randomUUID(),
    domain: "other",
    targetEventId: null,
    prompt: input.latestAnswer
      ? "我记下了这段经历。接下来请继续讲另一件你自己最确定、时间也比较清楚的人生变化；可以一次讲几件连续发生的事，我会顺着你的叙述继续核对。"
      : "请从你自己最确定、时间也比较清楚的一段人生经历开始说。你可以一次讲几件连续发生的事，不需要按固定领域回答。",
    recallCost: "low",
    reason: "V4 legacy projector：保持开放叙述。",
  };
}

export function projectLegacyV4Turn(input: Readonly<{
  events: readonly LifeEventRevision[];
  newEvents: readonly LifeEventRevision[];
  attemptedRefinementEventIds: readonly string[];
  latestAnswer: string;
  snapshot: CandidateSnapshot | null;
}>): Readonly<{
  nextQuestion: RectificationV4Question | null;
  publicMessage: PublicMessage;
  status: "awaiting_answer" | "range_ready";
  phase: "collecting_evidence" | "complete";
}> {
  const nextQuestion = projectLegacyV4Question(input);
  const latest = input.newEvents.at(-1);
  const primary = input.snapshot?.clusters[0];
  const rangeReady = Boolean(input.snapshot?.canAcceptRange && primary);
  return {
    nextQuestion,
    publicMessage: {
      acknowledgement: latest
        ? `我记下了你提到的“${latest.summary}”，并保留了你给出的时间精度。`
        : input.latestAnswer
          ? "我保留了你刚才的原始描述；目前还没有足够明确的新日期可以直接进入评分。"
          : "我会继续根据已确认的人生事件比较候选范围。",
      candidateUpdate: primary
        ? `目前较集中的候选仍是 ${primary.startTime}–${primary.endTime}；这只是待验证范围，不代表其中某一分钟已被确认。`
        : null,
      limitation: null,
      question: nextQuestion?.prompt ?? null,
    },
    status: rangeReady ? "range_ready" : "awaiting_answer",
    phase: rangeReady ? "complete" : "collecting_evidence",
  };
}
