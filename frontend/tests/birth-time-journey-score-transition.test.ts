import assert from "node:assert/strict";
import test from "node:test";
import { candidateResultSchema } from "../src/lib/birth-time-journey.ts";
import { completeScoreTransition } from "../src/lib/birth-time-journey-score-transition.ts";
import type { CandidateResult } from "../src/lib/birth-time-evidence.ts";
import type { StoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";
import {
  existingCareerEvent,
  existingEducationEvent,
  guidedCase,
} from "./birth-time-journey-test-support.ts";

const scoreJobId = "c70ea014-f8b4-41f2-9305-e4ae60c0d4d1";

function candidate(
  confidence: CandidateResult["confidence"],
  resultId: string,
) {
  const winningSegment = confidence === "high"
    ? { startTime: "14:22", endTime: "14:26", representativeTime: "14:24", widthMinutes: 5 }
    : null;
  return candidateResultSchema.parse({
    resultId,
    confidence,
    canApply: confidence === "high",
    winningSegment,
    eventCount: 4,
    domainCount: 3,
    topScore: 12,
    secondScore: 8,
    marginPercent: 33,
    reasons: confidence === "low" ? ["Candidate scores remain close."] : [],
    evidence: [],
    algorithmVersion: "birth-time-event-scoring-v1",
  });
}

function scoringCase(adaptiveRound: number): StoredRectificationCase {
  const stored = guidedCase({
    version: 6,
    adaptiveRound,
    askedDomains: ["education", "career"],
    lifeEvents: [existingEducationEvent, existingCareerEvent],
  });
  return {
    ...stored,
    turnState: {
      turnVersion: 6,
      nextAction: { kind: "score_pending", jobId: scoreJobId },
      progress: {
        phase: "scoring",
        baselineDomainCount: 2,
        confirmedEvidenceCount: 2,
        adaptiveRound,
        maxAdaptiveRounds: 3,
      },
      permissions: { canConfirmCandidate: false },
      evidenceDraft: null,
    },
  };
}

test("completed baseline low score advances to adaptive round one", () => {
  const low = candidate("low", "d833c219-8dd6-4ff4-a89d-d13b56c3084c");

  const result = completeScoreTransition({
    stored: scoringCase(0),
    candidateResult: low,
    nextVersion: 7,
  });

  assert.equal(result.turnState?.nextAction.kind, "ask_adaptive_evidence");
  assert.equal(result.turnState?.progress.adaptiveRound, 1);
  assert.equal(result.candidateResult, low);
});

test("completed adaptive round one low score advances to round two", () => {
  const low = candidate("low", "e4ee1f83-4ae1-45ef-a917-a14ed3e40c02");

  const result = completeScoreTransition({
    stored: scoringCase(1),
    candidateResult: low,
    nextVersion: 7,
  });

  assert.equal(result.turnState?.nextAction.kind, "ask_adaptive_evidence");
  assert.equal(result.turnState?.progress.adaptiveRound, 2);
});

test("completed adaptive round three low score becomes terminal", () => {
  const low = candidate("low", "6370de71-b768-4faf-910f-5b6dc447b825");

  const result = completeScoreTransition({
    stored: scoringCase(3),
    candidateResult: low,
    nextVersion: 7,
  });

  assert.deepEqual(result.turnState?.nextAction, {
    kind: "present_low_result",
    resultId: low.resultId,
  });
  assert.equal(result.snapshot.state, "candidate");
});

test("completed medium score becomes terminal save-only", () => {
  const medium = candidate("medium", "c73cf3cb-b95e-4d1b-94e4-56d7ae067a6b");

  const result = completeScoreTransition({
    stored: scoringCase(0),
    candidateResult: medium,
    nextVersion: 7,
  });

  assert.deepEqual(result.turnState?.nextAction, {
    kind: "present_medium_result",
    resultId: medium.resultId,
  });
  assert.equal(result.turnState?.permissions.canConfirmCandidate, false);
});

test("completed high score requests guarded candidate confirmation", () => {
  const high = candidate("high", "3253fca4-e812-4d81-961c-9a6ef680295b");

  const result = completeScoreTransition({
    stored: scoringCase(0),
    candidateResult: high,
    nextVersion: 7,
  });

  assert.deepEqual(result.turnState?.nextAction, {
    kind: "request_candidate_confirmation",
    resultId: high.resultId,
  });
  assert.equal(result.turnState?.permissions.canConfirmCandidate, true);
  assert.equal(result.snapshot.state, "confirming");
});
