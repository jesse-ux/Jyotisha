import assert from "node:assert/strict";
import test from "node:test";
import { randomUUID } from "node:crypto";
import { buildCandidateClusters } from "../src/lib/rectification-v4/candidate-clusters.ts";
import { dateRangeFromDeclared, sampledDates } from "../src/lib/rectification-v4/date-range.ts";
import { evaluateDecisionGate } from "../src/lib/rectification-v4/decision-gate.ts";
import { appendEventRevision, latestEventRevisions } from "../src/lib/rectification-v4/evidence-ledger.ts";
import { extractV4EventRevisions } from "../src/lib/rectification-v4/extraction.ts";
import { planNextQuestion } from "../src/lib/rectification-v4/question-planner.ts";

const now = new Date("2026-07-26T00:00:00.000Z");

test("declared month, quarter and year retain real boundaries instead of invented midpoints", () => {
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

test("relationship start and end remain separate immutable events", () => {
  const startId = randomUUID();
  const endId = randomUUID();
  const start = appendEventRevision([], {
    eventId: startId, domain: "relationship", eventKind: "relationship_start", summary: "关系开始",
    rawText: "2024年5月开始", dateRange: dateRangeFromDeclared("2024-05", "month"),
  }, { id: randomUUID(), now });
  const end = appendEventRevision([start], {
    eventId: endId, domain: "relationship", eventKind: "relationship_end", summary: "关系结束",
    rawText: "2024年8月结束", dateRange: dateRangeFromDeclared("2024-08", "month"),
  }, { id: randomUUID(), now });
  assert.notEqual(start.eventId, end.eventId);
  assert.equal(start.eventKind, "relationship_start");
  assert.equal(end.eventKind, "relationship_end");
});

test("family evidence is retained explicitly as context only", () => {
  const revision = appendEventRevision([], {
    eventId: randomUUID(), domain: "family", eventKind: "family_event", summary: "家庭变化",
    rawText: "家庭发生变化", dateRange: dateRangeFromDeclared("2020", "year"),
  }, { id: randomUUID(), now });
  assert.equal(revision.scoreability, "context_only");
});

test("candidate minutes merge into ranked contiguous clusters", () => {
  const id = randomUUID();
  const clusters = buildCandidateClusters([
    { time: "05:13", score: 100, supportingEventIds: [id], conflictingEventIds: [] },
    { time: "05:14", score: 99, supportingEventIds: [id], conflictingEventIds: [] },
    { time: "05:15", score: 98, supportingEventIds: [id], conflictingEventIds: [] },
    { time: "05:16", score: 70, supportingEventIds: [], conflictingEventIds: [id] },
    { time: "05:17", score: 97, supportingEventIds: [id], conflictingEventIds: [] },
    { time: "05:18", score: 97, supportingEventIds: [id], conflictingEventIds: [] },
  ]);
  assert.deepEqual(clusters.map((cluster) => [cluster.rank, cluster.startTime, cluster.endTime]), [
    [1, "05:13", "05:15"], [2, "05:17", "05:18"],
  ]);
});

test("decision gate can accept a stable range but never an exact minute", () => {
  const result = evaluateDecisionGate({
    clusters: [{ rank: 1, startTime: "05:13", endTime: "05:15", representativeTime: "05:13", widthMinutes: 3, peakScore: 10, scoreMass: 29 }],
    robustness: { neighborSupportMinutes: 3, leaveOneOutRetentionRate: 1, dateSensitivityRetentionRate: 0.9, calculationSpecHashMatched: true },
    scoreableEventCount: 10,
    scoreableDomainCount: 5,
  });
  assert.equal(result.canAcceptRange, true);
  assert.equal(result.canConfirmExactMinute, false);
});

test("question planner asks one deterministic low-recall question at a time", () => {
  const question = planNextQuestion({
    askedDomains: ["education"], coveredDomains: ["education"],
    candidateSplitByDomain: { relocation: 0.8, relationship: 0.2 }, id: randomUUID(),
  });
  assert.equal(question.domain, "relocation");
  assert.equal(question.targetEventId, null);
  assert.equal(question.prompt.includes("搬家"), true);
});

test("question planner refines imprecise scoreable events after domain coverage", () => {
  const eventId = randomUUID();
  const event = appendEventRevision([], {
    eventId, domain: "education", eventKind: "education_milestone", summary: "高中毕业",
    rawText: "2016年高中毕业", dateRange: dateRangeFromDeclared("2016", "year"),
  }, { id: randomUUID(), now });
  const question = planNextQuestion({
    askedDomains: ["education", "relocation", "relationship", "career", "finance", "health_pressure", "family"],
    coveredDomains: ["education", "relocation", "relationship", "career", "finance", "health_pressure", "family"],
    events: [event],
    attemptedRefinementEventIds: [],
    id: randomUUID(),
  });
  assert.equal(question.targetEventId, eventId);
  assert.equal(question.prompt.includes("高中毕业"), true);

  const fallback = planNextQuestion({
    askedDomains: ["education", "relocation", "relationship", "career", "finance", "health_pressure", "family"],
    coveredDomains: ["education", "relocation", "relationship", "career", "finance", "health_pressure", "family"],
    events: [event],
    attemptedRefinementEventIds: [eventId],
    id: randomUUID(),
  });
  assert.equal(fallback.targetEventId, null);
  assert.equal(fallback.domain, "other");
  assert.equal(fallback.prompt.includes("暂停"), true);
});

test("targeted date answer appends a revision without duplicating the scoreable event", () => {
  const eventId = randomUUID();
  const original = appendEventRevision([], {
    eventId, domain: "education", eventKind: "education_milestone", summary: "高中毕业",
    rawText: "2016年高中毕业", dateRange: dateRangeFromDeclared("2016", "year"),
  }, { id: randomUUID(), now });
  const revisions = extractV4EventRevisions({
    answer: "2016年6月8日",
    sourceTurnId: randomUUID(),
    asOfDate: "2026-07-26",
    existing: [original],
    targetEventId: eventId,
    now,
  });
  assert.equal(revisions.length, 1);
  assert.equal(revisions[0]?.eventId, eventId);
  assert.equal(revisions[0]?.revision, 2);
  assert.equal(revisions[0]?.dateRange.precision, "day");
  assert.equal(revisions[0]?.dateRange.start, "2016-06-08");
  assert.equal(latestEventRevisions([original, ...revisions]).length, 1);
});
