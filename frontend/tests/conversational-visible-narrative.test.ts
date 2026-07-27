import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import type { ConversationalRectificationTurn } from "../src/lib/conversational-rectification/contracts.ts";
import { visibleRectificationNarrative } from "../src/lib/conversational-rectification/visible-narrative.ts";

function turn(overrides: Partial<ConversationalRectificationTurn> = {}): ConversationalRectificationTurn {
  return {
    caseId: "00000000-0000-4000-8000-000000000921",
    journeyProtocol: "conversational-evidence-v3",
    status: "active",
    turnVersion: 1,
    narrative: "internal narrative",
    candidate: {
      status: "pending_validation",
      representativeTime: "05:20",
      rangeStart: "04:50",
      rangeEnd: "05:50",
    },
    technicalReceipt: {
      calculationVersion: "rectification-technical-v1",
      stableLayers: ["D1"],
      sensitiveLayers: ["D9", "D10"],
      candidateDifferenceRefs: ["consult-d9", "consult-d10"],
    },
    evidenceRequest: {
      domains: ["relationship", "career"],
      datePrecision: "month_preferred",
      freeTextAllowed: true,
    },
    evidenceRecap: [],
    actions: ["answer", "pause", "abandon"],
    pendingConsultationQuestion: null,
    ...overrides,
  };
}

test("visible rectification copy preserves the Agent's concrete follow-up", () => {
  const narrative = visibleRectificationNarrative(turn({
    narrative: "你提到离开家去北京开始工作，这次迁居和工作变化很关键。它大致是什么年月？",
    evidenceRecap: [{
      id: "00000000-0000-4000-8000-000000000922",
      summary: "离开家去北京开始工作",
      dateLabel: "日期待补充",
      domain: "relocation",
      isCorrection: false,
    }],
  }));

  assert.match(narrative, /你提到离开家去北京开始工作/);
  assert.match(narrative, /大致是什么年月/);
  assert.doesNotMatch(narrative, /接下来请说一件/);
});

test("visible rectification copy does not replace a tailored Agent answer with a template", () => {
  const narrative = visibleRectificationNarrative(turn({
    narrative: "结婚这件事我已经记下了。接下来想核对一次事业转折：你是哪一年、哪一月开始第一份长期工作的？",
    evidenceRecap: [{
      id: "00000000-0000-4000-8000-000000000923",
      summary: "结婚",
      dateLabel: "2020-05",
      domain: "relationship",
      isCorrection: false,
    }],
  }));

  assert.match(narrative, /结婚这件事我已经记下了/);
  assert.match(narrative, /事业转折/);
});

test("the v4 rectification chat renders persisted turns as alternating message history", () => {
  const source = readFileSync(
    new URL("../src/components/rectification-v4-panel.tsx", import.meta.url),
    "utf8",
  );

  assert.match(source, /for \(const turn of data\.turns\)/);
  assert.match(source, /role: "assistant"[\s\S]*?text: turn\.question/);
  assert.match(source, /role: "user"[\s\S]*?text: turn\.answer/);
  assert.match(source, /messages\.map\(\(message\) => <ChatMessageRow/);
  assert.doesNotMatch(source, /rectification-progress-details|evidenceRecap\.map/);
});
