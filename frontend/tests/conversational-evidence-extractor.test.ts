import assert from "node:assert/strict";
import test from "node:test";
import { extractLifeEventEvidence } from "../src/lib/conversational-rectification/evidence-extractor.ts";
import { lifeEventEvidenceSchema } from "../src/lib/conversational-rectification/persistence-contracts.ts";

const sourceTurnId = "00000000-0000-4000-8000-000000000610";

test("preserves raw text and splits two clear facts sharing an explicit month", () => {
  const rawText = "2021年7月毕业并去外地工作";
  const evidence = extractLifeEventEvidence({
    rawText,
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence.length, 2);
  assert.deepEqual(evidence.map((item) => item.rawText), [rawText, rawText]);
  assert.deepEqual(evidence.map((item) => item.eventSummary), ["毕业", "去外地工作"]);
  assert.deepEqual(evidence.map((item) => item.domain), ["education", "relocation"]);
  assert.deepEqual(evidence.map((item) => item.dateValue), ["2021-07", "2021-07"]);
  assert.deepEqual(evidence.map((item) => item.datePrecision), ["month", "month"]);
  assert.ok(evidence.every((item) => item.extractionStatus === "clear" && item.scoreable));
  assert.ok(evidence.every((item) => lifeEventEvidenceSchema.safeParse(item).success));
  assert.equal(new Set(evidence.map((item) => item.id)).size, 2);
});

test("removes the date-picker transport labels from the visible event summary", () => {
  const rawText = "发生时间：2016 年 6 月\n事件详情：大学毕业";
  const [evidence] = extractLifeEventEvidence({
    rawText,
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence?.eventSummary, "大学毕业");
  assert.equal(evidence?.dateValue, "2016-06");
  assert.equal(evidence?.domain, "education");
  assert.equal(evidence?.scoreable, true);
});

test("keeps vague evidence non-scoreable and asks for clarification", () => {
  const rawText = "那几年工作不太顺";
  const [evidence] = extractLifeEventEvidence({ rawText, sourceTurnId, asOfDate: "2026-07-20" });

  assert.equal(evidence?.rawText, rawText);
  assert.equal(evidence?.eventSummary, rawText);
  assert.equal(evidence?.dateValue, null);
  assert.equal(evidence?.datePrecision, "unknown");
  assert.equal(evidence?.extractionStatus, "needs_clarification");
  assert.equal(evidence?.scoreable, false);
});

test("preserves a nonblank punctuation-only answer as one clarification row", () => {
  const rawText = "？";
  const evidence = extractLifeEventEvidence({ rawText, sourceTurnId, asOfDate: "2026-07-20" });

  assert.equal(evidence.length, 1);
  assert.equal(evidence[0]?.rawText, rawText);
  assert.equal(evidence[0]?.extractionStatus, "needs_clarification");
  assert.equal(evidence[0]?.scoreable, false);
});

test("never invents a missing month or day", () => {
  const [evidence] = extractLifeEventEvidence({
    rawText: "2021年毕业",
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence?.dateValue, "2021");
  assert.equal(evidence?.datePrecision, "year");
  assert.equal(evidence?.eventSummary, "毕业");
});

test("classifies dated income and asset changes as finance evidence", () => {
  const [evidence] = extractLifeEventEvidence({
    rawText: "2022年8月收入大幅增加并开始投资",
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence?.domain, "finance");
  assert.equal(evidence?.dateValue, "2022-08");
  assert.equal(evidence?.scoreable, true);
  assert.equal(lifeEventEvidenceSchema.safeParse(evidence).success, true);
});

test("keeps a bare year as non-scoreable clarification instead of an event summary", () => {
  const rawText = "2021年";
  const [evidence] = extractLifeEventEvidence({
    rawText,
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence?.rawText, rawText);
  assert.equal(evidence?.dateValue, "2021");
  assert.equal(evidence?.datePrecision, "year");
  assert.notEqual(evidence?.eventSummary, rawText);
  assert.equal(evidence?.extractionStatus, "needs_clarification");
  assert.equal(evidence?.scoreable, false);
  assert.equal(lifeEventEvidenceSchema.safeParse(evidence).success, true);
});

for (const rawText of [
  "2021年7月毕业并次年工作",
  "2021年7月毕业并后来工作",
  "2021年7月毕业并第二年工作",
  "2021年7月毕业并此前工作",
  "2021年7月毕业然后工作",
  "2021年7月毕业后来又工作",
]) {
  test(`does not propagate a shared date through an unresolved relative clause: ${rawText}`, () => {
    const evidence = extractLifeEventEvidence({ rawText, sourceTurnId, asOfDate: "2026-07-20" });

    assert.equal(evidence.length, 2);
    assert.deepEqual(evidence.map((item) => item.eventSummary), ["毕业", "工作"]);
    assert.equal(evidence[0]?.dateValue, "2021-07");
    assert.equal(evidence[0]?.extractionStatus, "clear");
    assert.equal(evidence[0]?.scoreable, true);
    assert.equal(evidence[1]?.dateValue, null);
    assert.equal(evidence[1]?.datePrecision, "unknown");
    assert.equal(evidence[1]?.extractionStatus, "needs_clarification");
    assert.equal(evidence[1]?.scoreable, false);
  });
}

test("marks a future event as context-only and non-scoreable", () => {
  const [evidence] = extractLifeEventEvidence({
    rawText: "2030年3月计划结婚",
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence?.dateValue, "2030-03");
  assert.equal(evidence?.datePrecision, "month");
  assert.equal(evidence?.extractionStatus, "clear");
  assert.equal(evidence?.scoreable, false);
});

test("clear replacement evidence is explicitly marked corrected", () => {
  const targetId = "00000000-0000-4000-8000-000000000611";
  const [evidence] = extractLifeEventEvidence({
    rawText: "更正：2020年11月离职",
    sourceTurnId,
    asOfDate: "2026-07-20",
    correctsEvidenceId: targetId,
  });

  assert.equal(evidence?.eventSummary, "离职");
  assert.equal(evidence?.extractionStatus, "corrected");
  assert.equal(evidence?.scoreable, true);
  assert.deepEqual(evidence?.correctsEvidenceIds, [targetId]);
  assert.equal(lifeEventEvidenceSchema.safeParse(evidence).success, true);
});

test("an unclear correction keeps durable lineage while withholding both old and new scoring", () => {
  const targetId = "00000000-0000-4000-8000-000000000611";
  const [evidence] = extractLifeEventEvidence({
    rawText: "更正：具体年月记不清",
    sourceTurnId,
    asOfDate: "2026-07-20",
    correctsEvidenceId: targetId,
  });

  assert.equal(evidence?.extractionStatus, "needs_clarification");
  assert.equal(evidence?.scoreable, false);
  assert.deepEqual(evidence?.correctsEvidenceIds, [targetId]);
  assert.equal(lifeEventEvidenceSchema.safeParse(evidence).success, true);
});
