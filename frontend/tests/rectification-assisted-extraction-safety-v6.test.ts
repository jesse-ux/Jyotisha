import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";
import { validatedModelAssistedEvidence } from "../src/lib/conversational-rectification/evidence-extractor.ts";

test("模型辅助提取拒绝 self 与家庭 relatedPerson 的矛盾组合", () => {
  const rawText = "2020年4月老爸进了ICU。";
  const result = validatedModelAssistedEvidence({
    rawText,
    sourceTurnId: randomUUID(),
    asOfDate: "2026-07-29",
    extraction: {
      sourceSpan: "2020年4月老爸进了ICU",
      summary: "老爸进了ICU",
      domain: "health_pressure",
      eventKind: "self_health_event",
      subject: "self",
      relatedPerson: "father",
      dateText: "2020年4月",
    },
  });

  assert.equal(result, null);
});

test("明确家庭主体不能被模型伪装为 self scoreable", () => {
  const rawText = "2021年6月家里老人病危。";
  const result = validatedModelAssistedEvidence({
    rawText,
    sourceTurnId: randomUUID(),
    asOfDate: "2026-07-29",
    extraction: {
      sourceSpan: "2021年6月家里老人病危",
      summary: "家里老人病危",
      domain: "health_pressure",
      eventKind: "self_health_event",
      subject: "self",
      relatedPerson: null,
      dateText: "2021年6月",
    },
  });

  assert.equal(result, null);
});

test("合法家庭健康事件只作为 context_only", () => {
  const rawText = "2020年4月老爸进了ICU。";
  const result = validatedModelAssistedEvidence({
    rawText,
    sourceTurnId: randomUUID(),
    asOfDate: "2026-07-29",
    extraction: {
      sourceSpan: "2020年4月老爸进了ICU",
      summary: "老爸进了ICU",
      domain: "family",
      eventKind: "family_health_event",
      subject: "family",
      relatedPerson: "father",
      dateText: "2020年4月",
    },
  });

  assert.ok(result);
  assert.equal(result.scoreability, "context_only");
  assert.equal(result.scoreable, false);
});
