import assert from "node:assert/strict";
import test from "node:test";
import type { DynamicChoiceScoringResult } from "../src/lib/birth-time-dynamic-choice-internal.ts";
import { assertDynamicScoringResult } from "../src/lib/birth-time-dynamic-result-validator.ts";
import { BirthTimeScoringJobError } from "../src/lib/birth-time-scoring-job.ts";

const result: DynamicChoiceScoringResult = {
  candidate: {
    resultId: "097b7b4c-60f3-4ed8-b290-64b2084182e7",
    confidence: "medium",
    canApply: false,
    winningSegment: {
      startTime: "05:10", endTime: "05:12", representativeTime: "05:11", widthMinutes: 3,
    },
    eventCount: 3,
    domainCount: 2,
    topScore: 10,
    secondScore: 9,
    marginPercent: 10,
    reasons: [],
    evidence: [],
    algorithmVersion: "birth-time-choice-scoring-v2",
  },
  evidenceMode: "dynamic_choice",
  effectiveAnswerCount: 3,
  dimensionCount: 2,
};

const currentRange = { startTime: "05:00", endTime: "06:00" } as const;

test("medium and high results must satisfy deterministic confidence gates", () => {
  assert.doesNotThrow(() => assertDynamicScoringResult(result, currentRange));
  assert.doesNotThrow(() => assertDynamicScoringResult({
    ...result,
    effectiveAnswerCount: 4,
    dimensionCount: 3,
    candidate: {
      ...result.candidate,
      confidence: "high",
      canApply: true,
      eventCount: 4,
      domainCount: 3,
      marginPercent: 20,
    },
  }, currentRange));
  assert.throws(() => assertDynamicScoringResult({
    ...result,
    effectiveAnswerCount: 1,
    dimensionCount: 1,
    candidate: {
      ...result.candidate,
      winningSegment: null,
      eventCount: 1,
      domainCount: 1,
    },
  }, currentRange), BirthTimeScoringJobError);
});

test("winning segments must be a coherent subset of the persisted range", () => {
  for (const winningSegment of [
    { startTime: "04:59", endTime: "05:01", representativeTime: "05:00", widthMinutes: 3 },
    { startTime: "05:10", endTime: "05:12", representativeTime: "05:10", widthMinutes: 3 },
    { startTime: "05:10", endTime: "05:12", representativeTime: "05:11", widthMinutes: 2 },
  ] as const) {
    assert.throws(() => assertDynamicScoringResult({
      ...result,
      candidate: { ...result.candidate, winningSegment },
    }, currentRange), BirthTimeScoringJobError);
  }
});

test("cross-midnight ranges retain chronological segment validation", () => {
  assert.doesNotThrow(() => assertDynamicScoringResult({
    ...result,
    candidate: {
      ...result.candidate,
      winningSegment: {
        startTime: "23:59", endTime: "00:01", representativeTime: "00:00", widthMinutes: 3,
      },
    },
  }, { startTime: "23:58", endTime: "00:02" }));
});
