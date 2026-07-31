import { randomUUID } from "node:crypto";
import type { RectificationV4Question } from "./contracts.ts";

export function openingQuestion(prompt: string, id?: string): RectificationV4Question {
  return {
    id: id ?? randomUUID(),
    domain: "other",
    targetEventId: null,
    prompt,
    recallCost: "low",
    reason: "首轮由 Agent 根据候选范围生成自然引导。",
  };
}
