import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";
import { buildQuestionOpportunities } from "../src/lib/rectification-agent/opportunity-builder.ts";
import { buildCandidateClusters } from "../src/lib/rectification-v4/candidate-clusters.ts";
import { dateRangeFromDeclared, sampledDates } from "../src/lib/rectification-v4/date-range.ts";
import { evaluateDecisionGate } from "../src/lib/rectification-v4/decision-gate.ts";
import { appendEventRevision, latestEventRevisions } from "../src/lib/rectification-v4/evidence-ledger.ts";
import { extractV4EventRevisions } from "../src/lib/rectification-v4/extraction.ts";
import { openingQuestion } from "../src/lib/rectification-v4/opening-question.ts";

const now = new Date("2026-07-28T00:00:00.000Z");
const revision = (input: Parameters<typeof appendEventRevision>[1]) => appendEventRevision([], input, { id: randomUUID(), now });

test("declared month, quarter and year retain boundaries instead of invented midpoints", () => {
  assert.deepEqual(dateRangeFromDeclared("2024-02", "month"), {
    start: "2024-02-01", end: "2024-02-29", precision: "month", label: "2024-02",
  });
  assert.deepEqual(dateRangeFromDeclared("2024-Q2", "quarter"), {
    start: "2024-04-01", end: "2024-06-30", precision: "quarter", label: "2024-Q2",
  });
  assert.deepEqual(dateRangeFromDeclared("2024", "year"), {
    start: "2024-01-01", end: "2024-12-31", precision: "year", label: "2024",
  });
  assert.equal(sampledDates(dateRangeFromDeclared("2024-02", "month")).includes("2024-02-15"), false);
});

test("relationship start and end remain separate self/partner events", () => {
  const start = revision({
    eventId: randomUUID(), domain: "relationship", eventKind: "relationship_start", subject: "self", relatedPerson: "partner",
    summary: "关系开始", rawText: "2024年5月开始", dateRange: dateRangeFromDeclared("2024-05", "month"), scoreability: "scoreable",
  });
  const end = revision({
    eventId: randomUUID(), domain: "relationship", eventKind: "relationship_end", subject: "self", relatedPerson: "partner",
    summary: "关系结束", rawText: "2024年8月结束", dateRange: dateRangeFromDeclared("2024-08", "month"), scoreability: "scoreable",
  });
  assert.notEqual(start.eventId, end.eventId);
  assert.deepEqual([start.eventKind, end.eventKind], ["relationship_start", "relationship_end"]);
});

test("family health and bereavement stay context-only while self health is scoreable", () => {
  for (const eventKind of ["family_health_event", "family_bereavement"] as const) {
    const event = revision({
      eventId: randomUUID(), domain: "family", eventKind, subject: "family", relatedPerson: "mother",
      summary: "家人健康事件", rawText: "2020年家人住院", dateRange: dateRangeFromDeclared("2020", "year"), scoreability: "context_only",
    });
    assert.equal(event.scoreability, "context_only");
  }
  const selfHealth = revision({
    eventId: randomUUID(), domain: "health_pressure", eventKind: "self_health_event", subject: "self", relatedPerson: null,
    summary: "本人手术", rawText: "2021年3月手术", dateRange: dateRangeFromDeclared("2021-03", "month"), scoreability: "scoreable",
  });
  assert.equal(selfHealth.scoreability, "scoreable");
  assert.throws(() => revision({
    eventId: randomUUID(), domain: "health_pressure", eventKind: "self_health_event", subject: "family", relatedPerson: "mother",
    summary: "母亲手术", rawText: "2021年3月母亲手术", dateRange: dateRangeFromDeclared("2021-03", "month"), scoreability: "scoreable",
  }), /non_self_event_not_scoreable/);
});

test("candidate minutes merge into ranked contiguous clusters and never confirm one minute", () => {
  const id = randomUUID();
  const clusters = buildCandidateClusters([
    { time: "05:13", score: 100, supportingEventIds: [id], conflictingEventIds: [] },
    { time: "05:14", score: 99, supportingEventIds: [id], conflictingEventIds: [] },
    { time: "05:15", score: 98, supportingEventIds: [id], conflictingEventIds: [] },
    { time: "05:16", score: 70, supportingEventIds: [], conflictingEventIds: [id] },
    { time: "05:17", score: 97, supportingEventIds: [id], conflictingEventIds: [] },
    { time: "05:18", score: 97, supportingEventIds: [id], conflictingEventIds: [] },
  ]);
  assert.deepEqual(clusters.map((cluster) => [cluster.rank, cluster.startTime, cluster.endTime]), [[1, "05:13", "05:15"], [2, "05:17", "05:18"]]);
  const gate = evaluateDecisionGate({
    clusters: [clusters[0]!],
    robustness: { neighborSupportMinutes: 3, leaveOneOutRetentionRate: 1, leaveOneDomainOutRetentionRate: 1, dateSensitivityRetentionRate: 0.9, calculationSpecHashMatched: true },
    scoreableEventCount: 10,
    scoreableDomains: ["education", "relocation", "relationship", "career", "finance"],
  });
  assert.equal(gate.canAcceptRange, true);
  assert.equal(gate.canConfirmExactMinute, false);
});

test("opening question is open narration, not a fixed-domain questionnaire", () => {
  const question = openingQuestion({ start: "04:50", end: "05:10" }, randomUUID());
  assert.equal(question.domain, "other");
  assert.equal(question.targetEventId, null);
  assert.match(question.prompt, /04:50–05:10/);
  assert.match(question.prompt, /不是已确认的出生分钟/);
  assert.match(question.prompt, /不需要按固定领域回答/);
  assert.doesNotMatch(question.prompt, /毕业|搬家|恋爱|工作|财务|健康/);
});

test("Opportunity Builder prioritizes event-local date refinement and never asks family as self health", () => {
  const event = revision({
    eventId: randomUUID(), domain: "education", eventKind: "education_milestone", subject: "self", relatedPerson: null,
    summary: "离家去外地上大学", rawText: "2016年离家去外地上大学", dateRange: dateRangeFromDeclared("2016", "year"), scoreability: "scoreable",
  });
  const opportunities = buildQuestionOpportunities({ caseId: randomUUID(), events: [event], turns: [], snapshot: null, diagnostics: null });
  const local = opportunities.find((item) => item.kind === "refine_event_date");
  assert.equal(local?.targetEventId, event.eventId);
  assert.equal(local?.domain, "education");
  assert.match(local?.fallbackPrompt ?? "", /离家去外地上大学/);
  assert.match(local?.fallbackPrompt ?? "", /哪个月|时间段/);
  assert.ok(opportunities.every((item, index) => index === 0 || opportunities[index - 1]!.utility >= item.utility));
  assert.ok(opportunities.every((item) => item.domain !== "family"));
});

test("targeted date answer appends a revision without duplicating the event", () => {
  const eventId = randomUUID();
  const original = revision({
    eventId, domain: "education", eventKind: "education_milestone", subject: "self", relatedPerson: null,
    summary: "高中毕业", rawText: "2016年高中毕业", dateRange: dateRangeFromDeclared("2016", "year"), scoreability: "scoreable",
  });
  const revisions = extractV4EventRevisions({
    answer: "2016年6月8日", sourceTurnId: randomUUID(), asOfDate: "2026-07-28", existing: [original], targetEventId: eventId, now,
  });
  assert.equal(revisions.length, 1);
  assert.equal(revisions[0]?.eventId, eventId);
  assert.equal(revisions[0]?.revision, 2);
  assert.equal(revisions[0]?.dateRange.start, "2016-06-08");
  assert.equal(latestEventRevisions([original, ...revisions]).length, 1);
});
