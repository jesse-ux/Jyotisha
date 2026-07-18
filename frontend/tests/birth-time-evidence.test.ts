import assert from "node:assert/strict";
import test from "node:test";
import {
  candidateResultSchema,
  lifeEventSchema,
  withConfirmedCandidate,
} from "../src/lib/birth-time-evidence.ts";
import { journeySnapshotSchema } from "../src/lib/birth-time-journey.ts";
import { evidenceDraftSchema } from "../src/lib/birth-time-journey-turn.ts";

const baseEvent = {
  id: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
  domain: "career",
} as const;

test("life event dates must match their declared precision", () => {
  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "year", date: "2011" }).success, true);
  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "month", date: "2011-09" }).success, true);
  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "day", date: "2011-09-24" }).success, true);

  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "year", date: "2011-09" }).success, false);
  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "month", date: "2011" }).success, false);
  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "day", date: "2011" }).success, false);
  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "year", date: "2011.5" }).success, false);
});

test("life event day precision rejects impossible calendar dates", () => {
  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "day", date: "2024-02-29" }).success, true);
  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "day", date: "2023-02-29" }).success, false);
  assert.equal(lifeEventSchema.safeParse({ ...baseEvent, precision: "day", date: "2023-04-31" }).success, false);
});

test("evidence drafts carry one server-selected event and no confirmed events", () => {
  const parsed = evidenceDraftSchema.parse({
    draftId: baseEvent.id,
    questionId: "baseline_career_1",
    domain: "career",
    precision: "month",
    date: "2019-07",
    status: "draft",
    needsReview: false,
  });

  assert.equal(parsed.draftId, baseEvent.id);
  assert.equal(parsed.questionId, "baseline_career_1");
  assert.equal(parsed.status, "draft");
  assert.equal("events" in parsed, false);
  assert.equal("id" in parsed, false);
});

test("incomplete draft fields remain nullable and review-only", () => {
  const parsed = evidenceDraftSchema.parse({
    draftId: baseEvent.id,
    questionId: "adaptive_career_1",
    domain: "career",
    precision: null,
    date: null,
    status: "draft",
    needsReview: true,
  });

  assert.equal(parsed.precision, null);
  assert.equal(parsed.date, null);
  assert.equal(parsed.needsReview, true);
});

test("evidence drafts reject extra confirmed-event payloads", () => {
  assert.equal(evidenceDraftSchema.safeParse({
    draftId: baseEvent.id,
    questionId: "baseline_career_1",
    domain: "career",
    precision: "year",
    date: "2019",
    status: "draft",
    needsReview: false,
    events: [{ ...baseEvent, precision: "year", date: "2019" }],
  }).success, false);
});

const candidateBase = {
  resultId: "8c48d5a8-cf2a-43a5-90f9-e39a726de265",
  confidence: "high",
  canApply: true,
  winningSegment: {
    startTime: "14:22",
    endTime: "14:26",
    representativeTime: "14:24",
    widthMinutes: 5,
  },
  eventCount: 4,
  domainCount: 3,
  topScore: 18,
  secondScore: 12,
  marginPercent: 50,
  reasons: ["One segment has consistent evidence."],
  evidence: [],
  algorithmVersion: "birth-time-event-scoring-v1",
} as const;

test("high candidate results require every deterministic safety gate", () => {
  assert.equal(candidateResultSchema.safeParse(candidateBase).success, true);
  assert.equal(candidateResultSchema.safeParse({ ...candidateBase, eventCount: 3 }).success, false);
  assert.equal(candidateResultSchema.safeParse({ ...candidateBase, domainCount: 2 }).success, false);
  assert.equal(candidateResultSchema.safeParse({ ...candidateBase, canApply: false, winningSegment: null }).success, false);
  assert.equal(candidateResultSchema.safeParse({
    ...candidateBase,
    winningSegment: { ...candidateBase.winningSegment, widthMinutes: 6 },
  }).success, false);
  assert.equal(candidateResultSchema.safeParse({ ...candidateBase, marginPercent: 19 }).success, false);
});

test("confirmation rejects a high result forged below the deterministic gates", () => {
  const candidate = candidateResultSchema.parse(candidateBase);
  const forged = { ...candidate, eventCount: 3 };
  const snapshot = journeySnapshotSchema.parse({
    state: "confirming",
    assistantIntent: "confirm_candidate_time",
    input: "candidate_confirmation",
    route: "rectification",
    confidence: "high",
    canApply: true,
    activeTime: null,
    reportedRange: { label: "14:22—14:26", startTime: "14:22", endTime: "14:26" },
  });

  assert.throws(
    () => withConfirmedCandidate(snapshot, forged, "14:24"),
    { name: "CandidateConfirmationError" },
  );
});
