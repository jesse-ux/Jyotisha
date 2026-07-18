import assert from "node:assert/strict";
import test from "node:test";
import { parseJourneyResponse } from "../src/lib/birth-time-journey-client.ts";
import {
  highConfirmationTurn,
} from "./birth-time-journey-client-test-support.ts";

const baselineQuestion = {
  questionId: "baseline_education_1",
  phase: "baseline",
  domain: "education",
  requestedPrecision: ["year", "month"],
  allowUnknown: true,
  purposeCode: "candidate_difference_education",
  plannerVersion: "candidate-difference-v1",
} as const;

const baselineProgress = {
  phase: "baseline",
  baselineDomainCount: 1,
  confirmedEvidenceCount: 2,
  adaptiveRound: 0,
  maxAdaptiveRounds: 3,
} as const;

test("client rejects inconsistent versioned route and result actions", () => {
  assert.throws(() => parseJourneyResponse({
    ...highConfirmationTurn,
    snapshot: {
      ...highConfirmationTurn.snapshot,
      state: "ready",
      input: "none",
      route: "direct_chart",
      canApply: false,
      activeTime: null,
    },
    nextAction: { kind: "ready", activeTime: "14:24" },
    permissions: { canConfirmCandidate: false },
  }));

  assert.throws(() => parseJourneyResponse({
    ...highConfirmationTurn,
    nextAction: {
      kind: "request_candidate_confirmation",
      resultId: "45857b75-4718-4590-aaf5-7113a03ea765",
    },
  }));

  assert.throws(() => parseJourneyResponse({
    ...highConfirmationTurn,
    candidateResult: null,
    snapshot: {
      ...highConfirmationTurn.snapshot,
      state: "rectifying",
      assistantIntent: "start_standard_rectification",
      input: "rectification_questions",
      route: "direct_chart",
      confidence: null,
      canApply: false,
      activeTime: "14:24",
    },
    nextAction: { kind: "ask_baseline_evidence", question: baselineQuestion },
    progress: { ...baselineProgress, baselineDomainCount: 0, confirmedEvidenceCount: 0 },
    permissions: { canConfirmCandidate: false },
  }));
});

test("client accepts a projected baseline action for a legacy snapshot", () => {
  const parsed = parseJourneyResponse({
    ...highConfirmationTurn,
    candidateResult: null,
    snapshot: {
      ...highConfirmationTurn.snapshot,
      state: "candidate",
      assistantIntent: "present_saved_candidate_range",
      input: "rectification_questions",
      route: "rectification",
      confidence: null,
      canApply: false,
    },
    nextAction: { kind: "ask_baseline_evidence", question: baselineQuestion },
    progress: baselineProgress,
    permissions: { canConfirmCandidate: false },
  });

  assert.equal(parsed.nextAction.kind, "ask_baseline_evidence");
});

test("client rejects versioned baseline and review invariant violations", () => {
  assert.throws(() => parseJourneyResponse({
    ...highConfirmationTurn,
    candidateResult: null,
    snapshot: {
      ...highConfirmationTurn.snapshot,
      state: "rectifying",
      assistantIntent: "continue_rectification_questions",
      input: "rectification_questions",
      route: "rectification",
      confidence: null,
      canApply: false,
    },
    nextAction: {
      kind: "ask_baseline_evidence",
      question: { ...baselineQuestion, questionId: "adaptive_education_1", phase: "adaptive" },
    },
    progress: {
      ...baselineProgress,
      baselineDomainCount: 2,
      confirmedEvidenceCount: 3,
    },
    permissions: { canConfirmCandidate: false },
  }));

  assert.throws(() => parseJourneyResponse({
    ...highConfirmationTurn,
    candidateResult: null,
    snapshot: {
      ...highConfirmationTurn.snapshot,
      state: "rectifying",
      assistantIntent: "collect_dated_life_events",
      input: "life_events",
      route: "rectification",
      confidence: null,
      canApply: false,
    },
    nextAction: {
      kind: "review_evidence_draft",
      draftId: "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5",
    },
    progress: {
      ...baselineProgress,
      phase: "review",
      baselineDomainCount: 2,
      confirmedEvidenceCount: 3,
    },
    permissions: { canConfirmCandidate: false },
    evidenceDraft: null,
  }));
});

test("client preserves optimistic turn versions", () => {
  const parsed = parseJourneyResponse({ ...highConfirmationTurn, turnVersion: 7 });

  assert.equal(parsed.turnVersion, 7);
  assert.throws(() => parseJourneyResponse({
    ...highConfirmationTurn,
    turnVersion: -1,
  }));
});
