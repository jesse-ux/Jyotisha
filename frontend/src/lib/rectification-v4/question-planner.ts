import { randomUUID } from "node:crypto";
import type { LifeEventRevision, RectificationV4Question } from "./contracts.ts";
import { scoreableEvents } from "./evidence-ledger.ts";

function refinementQuestion(event: LifeEventRevision, id?: string): RectificationV4Question {
  return {
    id: id ?? randomUUID(),
    domain: event.domain,
    targetEventId: event.eventId,
    prompt: `你刚才提到的“${event.summary.slice(0, 120)}”很重要。你目前记得的时间是${event.dateRange.label}；如果还能想起更具体的月份或日期，可以继续说，不确定也没关系。`,
    recallCost: "medium",
    reason: "缩小已有事件的日期范围，用于检验候选范围对日期误差是否稳定。",
  };
}

export function planNextQuestion(input: {
  readonly events?: readonly LifeEventRevision[];
  readonly attemptedRefinementEventIds?: readonly string[];
  readonly latestAnswer?: string;
  readonly id?: string;
}): RectificationV4Question {
  const attempted = new Set(input.attemptedRefinementEventIds ?? []);
  const target = scoreableEvents(input.events ?? [])
    .filter((event) => event.dateRange.precision !== "day" && !attempted.has(event.eventId))
    .sort((left, right) => right.createdAt.localeCompare(left.createdAt) || left.eventId.localeCompare(right.eventId))[0];
  if (target) return refinementQuestion(target, input.id);

  return {
    id: input.id ?? randomUUID(),
    domain: "other",
    targetEventId: null,
    prompt: input.latestAnswer
      ? "我记下了这段经历。接下来请继续讲另一件你自己最确定、时间也比较清楚的人生变化；可以一次讲几件连续发生的事，我会顺着你的叙述继续核对。"
      : "请从你自己最确定、时间也比较清楚的一段人生经历开始说。你可以一次讲几件连续发生的事，不需要按固定领域回答。",
    recallCost: "low",
    reason: "模型不可用时保持开放叙述，不退回固定领域问卷。",
  };
}

export function openingQuestion(
  candidateRange: Readonly<{ start: string; end: string }>,
  id?: string,
): RectificationV4Question {
  return {
    id: id ?? randomUUID(),
    domain: "other",
    targetEventId: null,
    prompt: `我会先在 ${candidateRange.start}–${candidateRange.end} 这个范围内核对，它还不是已确认的出生分钟。请从你自己最确定、时间也比较清楚的一段人生经历开始说；可以一次讲几件连续发生的事，不需要按固定领域回答。`,
    recallCost: "low",
    reason: "首轮允许开放叙述，由后续模型根据真实经历选择高信息量问题。",
  };
}
