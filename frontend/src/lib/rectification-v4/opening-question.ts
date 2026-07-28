import { randomUUID } from "node:crypto";
import type { RectificationV4Question } from "./contracts.ts";

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
    reason: "首轮允许开放叙述，由后续系统根据真实经历选择高信息量问题。",
  };
}
