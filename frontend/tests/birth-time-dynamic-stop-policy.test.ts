import assert from "node:assert/strict";
import test from "node:test";
import { decideDynamicStop } from "../src/lib/birth-time-dynamic-stop-policy.ts";
import type { CandidateResult } from "../src/lib/birth-time-evidence.ts";

const lowCandidate: CandidateResult = {
  resultId: "11111111-1111-4111-8111-111111111111",
  confidence: "low",
  canApply: false,
  winningSegment: null,
  eventCount: 1,
  domainCount: 1,
  topScore: 10,
  secondScore: 9,
  marginPercent: 10,
  reasons: ["Candidate scores remain close."],
  evidence: [],
  algorithmVersion: "birth-time-choice-scoring-v2",
};

const mediumCandidate: CandidateResult = {
  ...lowCandidate,
  resultId: "22222222-2222-4222-8222-222222222222",
  confidence: "medium",
  marginPercent: 15,
};

function decisionFor(overrides: Partial<Parameters<typeof decideDynamicStop>[0]>) {
  return decideDynamicStop({
    result: lowCandidate,
    effectiveAnswer: true,
    previousResult: null,
    priorPlateauCount: 0,
    usefulOpportunityCount: 1,
    repeatedOnly: false,
    effectiveAnswerCount: 1,
    forcedReason: null,
    ...overrides,
  });
}

function finishReason(overrides: Partial<Parameters<typeof decideDynamicStop>[0]>) {
  const decision = decisionFor(overrides);
  if (decision.kind !== "finish") assert.fail("expected a terminal decision");
  return decision.reason;
}

test("two effective unchanged scores stop without starting another question", () => {
  const decision = decideDynamicStop({
    result: mediumCandidate,
    effectiveAnswer: true,
    previousResult: mediumCandidate,
    priorPlateauCount: 1,
    usefulOpportunityCount: 3,
    repeatedOnly: false,
    effectiveAnswerCount: 6,
    forcedReason: null,
  });

  assert.deepEqual(decision, { kind: "finish", reason: "plateau", plateauCount: 2 });
});

test("unknown answers do not advance plateau or the effective safety count", () => {
  const decision = decideDynamicStop({
    result: lowCandidate,
    effectiveAnswer: false,
    previousResult: lowCandidate,
    priorPlateauCount: 1,
    usefulOpportunityCount: 2,
    repeatedOnly: false,
    effectiveAnswerCount: 4,
    forcedReason: null,
  });

  assert.deepEqual(decision, { kind: "continue", plateauCount: 1 });
});

test("terminal conditions are deterministic", () => {
  assert.equal(finishReason({ result: null, forcedReason: "user_finished" }), "user_finished");
  assert.equal(finishReason({ result: null, forcedReason: "generation_unavailable" }), "generation_unavailable");
  assert.equal(finishReason({ result: { ...lowCandidate, confidence: "high", canApply: true, winningSegment: {
    startTime: "09:00", endTime: "09:05", representativeTime: "09:03", widthMinutes: 5,
  }, eventCount: 4, domainCount: 3, marginPercent: 20 } }), "high_confidence");
  assert.equal(finishReason({ usefulOpportunityCount: 0 }), "no_information_gain");
  assert.equal(finishReason({ repeatedOnly: true }), "repeated_partition");
  assert.equal(finishReason({ effectiveAnswerCount: 10 }), "safety_cap");
});

test("forced terminal reasons win over a high-confidence score", () => {
  assert.equal(finishReason({
    result: { ...lowCandidate, confidence: "high", canApply: true, winningSegment: {
      startTime: "09:00", endTime: "09:05", representativeTime: "09:03", widthMinutes: 5,
    }, eventCount: 4, domainCount: 3, marginPercent: 20 },
    forcedReason: "user_finished",
  }), "user_finished");
});

test("a two point margin change resets the plateau", () => {
  const decision = decisionFor({
    result: { ...mediumCandidate, marginPercent: 17 },
    previousResult: mediumCandidate,
    priorPlateauCount: 1,
  });

  assert.deepEqual(decision, { kind: "continue", plateauCount: 0 });
});
