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

test("merges same-date same-domain clauses into one scoreable life event", () => {
  const rawText = "2017年7月入职第一家公司，并从事数据分析工作";
  const evidence = extractLifeEventEvidence({
    rawText,
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence.length, 1);
  assert.equal(evidence[0]?.domain, "career");
  assert.equal(evidence[0]?.dateValue, "2017-07");
  assert.equal(evidence[0]?.eventSummary, "入职第一家公司；从事数据分析工作");
  assert.equal(evidence[0]?.scoreable, true);
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

test("expands abbreviated historical years without losing the first scoreable event", () => {
  const evidence = extractLifeEventEvidence({
    rawText: "之后 21 年元旦回家准备备考考研，然后又遇到疫情封控，一直到21年底，我实际上在家呆到23年才出来",
    sourceTurnId,
    asOfDate: "2026-07-24",
  });

  assert.equal(evidence[0]?.dateValue, "2021");
  assert.equal(evidence[0]?.eventSummary, "元旦回家准备备考考研");
  assert.equal(evidence[0]?.scoreable, true);
  assert.ok(evidence.some((item) => item.dateValue === "2023"));
});

test("accepts nineteenth-century Chinese and ISO dates as scoreable historical evidence", () => {
  const [education] = extractLifeEventEvidence({
    rawText: "1891年11月进入巴黎大学学习",
    sourceTurnId,
    asOfDate: "2026-07-20",
  });
  const [relationship] = extractLifeEventEvidence({
    rawText: "1895-07-26结婚",
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.deepEqual(
    [education?.dateValue, education?.domain, education?.scoreable],
    ["1891-11", "education", true],
  );
  assert.deepEqual(
    [relationship?.dateValue, relationship?.domain, relationship?.scoreable],
    ["1895-07-26", "relationship", true],
  );
});

test("classifies the user's dated illness as scoreable self-health evidence", () => {
  const [evidence] = extractLifeEventEvidence({
    rawText: "2003年确诊癌症并接受手术",
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence?.domain, "health_pressure");
  assert.equal(evidence?.eventKind, "self_health_event");
  assert.equal(evidence?.subject, "self");
  assert.equal(evidence?.scoreable, true);
  assert.equal(lifeEventEvidenceSchema.safeParse(evidence).success, true);
});

test("keeps a partner's bereavement as family context instead of personal-health scoring", () => {
  const [evidence] = extractLifeEventEvidence({
    rawText: "2006年丈夫因交通事故去世",
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence?.domain, "family");
  assert.equal(evidence?.eventKind, "family_bereavement");
  assert.equal(evidence?.subject, "family");
  assert.equal(evidence?.relatedPerson, "partner");
  assert.equal(evidence?.scoreability, "context_only");
  assert.equal(evidence?.scoreable, false);
  assert.equal(lifeEventEvidenceSchema.safeParse(evidence).success, true);
});

test("classifies dated income and asset changes as finance evidence", () => {
  const [evidence] = extractLifeEventEvidence({
    rawText: "2022年8月收入大幅增加并开始投资",
    sourceTurnId,
    asOfDate: "2026-07-20",
  });

  assert.equal(evidence?.domain, "finance");
  assert.equal(evidence?.eventKind, "finance_change");
  assert.equal(evidence?.dateValue, "2022-08");
  assert.equal(evidence?.scoreable, true);
  assert.equal(lifeEventEvidenceSchema.safeParse(evidence).success, true);
});

for (const rawText of [
  "2020年8月开始承担管理职责",
  "2020年8月职位发生明显变化",
  "2020年8月开始任职部门负责人",
]) {
  test(`classifies dated role and management changes as career evidence: ${rawText}`, () => {
    const [evidence] = extractLifeEventEvidence({ rawText, sourceTurnId, asOfDate: "2026-07-20" });

    assert.equal(evidence?.domain, "career");
    assert.equal(evidence?.dateValue, "2020-08");
    assert.equal(evidence?.scoreable, true);
    assert.equal(lifeEventEvidenceSchema.safeParse(evidence).success, true);
  });
}

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
  "2021年7月毕业并来年工作",
  "2021年7月毕业并翌年工作",
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
