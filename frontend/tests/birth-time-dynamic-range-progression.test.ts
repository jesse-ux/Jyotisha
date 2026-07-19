import assert from "node:assert/strict";
import test from "node:test";
import { completeDynamicScoreTransition } from "../src/lib/birth-time-dynamic-transitions.ts";
import type { CandidateResult } from "../src/lib/birth-time-evidence.ts";
import { dynamicCase } from "./birth-time-dynamic-persistence-fixture.ts";

const narrowedLowCandidate: CandidateResult = {
  resultId: "615499c9-f4da-4da0-a8bd-da26b2b8477f",
  confidence: "low",
  canApply: false,
  winningSegment: {
    startTime: "05:10",
    endTime: "05:20",
    representativeTime: "05:15",
    widthMinutes: 11,
  },
  eventCount: 1,
  domainCount: 1,
  topScore: 1,
  secondScore: 0,
  marginPercent: 100,
  reasons: ["insufficient_effective_evidence"],
  evidence: [],
  algorithmVersion: "birth-time-choice-scoring-v2",
};

test("low-confidence continuation narrows the candidate universe for the next question", () => {
  const stored = dynamicCase();
  const result = completeDynamicScoreTransition({
    stored: { ...stored, currentChoiceQuestion: null },
    candidate: narrowedLowCandidate,
    usefulOpportunityCount: 1,
    repeatedOnly: false,
    nextVersion: stored.turnVersion + 1,
  });

  assert.equal(result.dynamicTurnState.nextAction.kind, "generate_dynamic_question");
  assert.deepEqual(
    result.dynamicTurnState.progress.currentRange,
    { startTime: "05:10", endTime: "05:20" },
  );
  assert.deepEqual(
    result.dynamicTurnState.progress.previousRange,
    stored.dynamicTurnState.progress.currentRange,
  );
  assert.deepEqual(result.dynamicControl.recentRanges.at(-1), {
    startTime: "05:10",
    endTime: "05:20",
  });
});

test("terminal low confidence publishes its final candidate segment", () => {
  const stored = dynamicCase();
  const result = completeDynamicScoreTransition({
    stored: { ...stored, currentChoiceQuestion: null },
    candidate: narrowedLowCandidate,
    usefulOpportunityCount: 0,
    repeatedOnly: false,
    nextVersion: stored.turnVersion + 1,
  });

  assert.equal(result.dynamicTurnState.nextAction.kind, "present_low_result");
  assert.deepEqual(result.dynamicTurnState.progress.currentRange, {
    startTime: "05:10",
    endTime: "05:20",
  });
});
