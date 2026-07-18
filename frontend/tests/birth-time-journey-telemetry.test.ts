import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  createJourneyTelemetry,
  recordJourneyTransitionMetric,
  recordScoringJourneyMetric,
  recordJourneyMetricEvent,
} from "../src/lib/birth-time-journey-telemetry.ts";
import type { VersionedJourneyResponse } from "../src/lib/birth-time-journey-service.ts";
import { highConfirmationTurn } from "./birth-time-journey-client-test-support.ts";

const scoringJobId = "75a5fbb3-bf1d-44b2-8c74-c92cf7578f82";

function scoringResponse(
  action: "score_pending" | "retry_scoring",
  version: number,
  adaptiveRound = 0,
): VersionedJourneyResponse {
  return {
    ...highConfirmationTurn,
    snapshot: {
      ...highConfirmationTurn.snapshot,
      state: "rectifying",
      assistantIntent: "collect_dated_life_events",
      input: "life_events",
      confidence: null,
      canApply: false,
    },
    candidateResult: null,
    turnVersion: version,
    nextAction: { kind: action, jobId: scoringJobId },
    progress: {
      ...highConfirmationTurn.progress,
      phase: "scoring",
      adaptiveRound,
    },
    permissions: { canConfirmCandidate: false },
  };
}

function highResultResponse(version: number, adaptiveRound = 0): VersionedJourneyResponse {
  const candidate = highConfirmationTurn.candidateResult;
  return {
    ...highConfirmationTurn,
    answers: { ...highConfirmationTurn.answers },
    lifeEvents: [...highConfirmationTurn.lifeEvents],
    candidateResult: {
      ...candidate,
      winningSegment: { ...candidate.winningSegment },
      reasons: [...candidate.reasons],
      evidence: [...candidate.evidence],
    },
    turnVersion: version,
    progress: { ...highConfirmationTurn.progress, adaptiveRound },
  };
}

test("telemetry emits only the closed metric payload", () => {
  const emitted: unknown[] = [];
  const record = createJourneyTelemetry((payload) => {
    emitted.push(payload);
  });

  record("turn_advanced", { phase: "baseline" });
  record("scoring_recovered", { phase: "result", confidence: "high" });

  assert.deepEqual(emitted, [
    { name: "turn_advanced", phase: "baseline" },
    { name: "scoring_recovered", phase: "result", confidence: "high" },
  ]);
  const firstPayload = emitted[0];
  assert.ok(firstPayload !== null && typeof firstPayload === "object");
  assert.deepEqual(Object.keys(firstPayload), ["name", "phase"]);
});

test("telemetry rejects raw personal fields at runtime", () => {
  const emitted: unknown[] = [];
  const record = createJourneyTelemetry((payload) => {
    emitted.push(payload);
  });

  for (const labels of [
    { phase: "baseline", message: "free text" },
    { phase: "baseline", eventDate: "2019-04" },
    { phase: "baseline", birthDate: "1993-04-17" },
    { phase: "baseline", coordinates: "31.2304,121.4737" },
    { phase: "baseline", caseId: "case-1" },
    { phase: "baseline", userId: "user-1" },
  ]) {
    assert.throws(() => Reflect.apply(record, undefined, ["turn_advanced", labels]));
  }
  assert.deepEqual(emitted, []);
});

test("telemetry sink failures never escape into the journey response", () => {
  const record = createJourneyTelemetry(() => {
    throw new Error("analytics offline");
  });

  assert.doesNotThrow(() => record("journey_paused", { phase: "adaptive" }));
});

test("route telemetry decisions distinguish scoring failures, recovery, and illegal state", () => {
  const emitted: unknown[] = [];
  const record = createJourneyTelemetry((payload) => {
    emitted.push(payload);
  });

  recordJourneyMetricEvent({ kind: "transition", name: "turn_advanced", phase: "baseline" }, record);
  recordJourneyMetricEvent({ kind: "scoring", outcome: "succeeded", priorFailure: false, phase: "result", confidence: "medium" }, record);
  recordJourneyMetricEvent({ kind: "scoring", outcome: "failed", phase: "result" }, record);
  recordJourneyMetricEvent({ kind: "scoring", outcome: "succeeded", priorFailure: true, phase: "result", confidence: "high" }, record);
  recordJourneyMetricEvent({ kind: "error", reason: "illegal_state", phase: "result" }, record);
  recordJourneyMetricEvent({ kind: "error", reason: "scoring_failure", phase: "result" }, record);
  recordJourneyMetricEvent({ kind: "transition", name: "turn_advanced", phase: "adaptive", confidence: "medium" }, record);

  assert.deepEqual(emitted, [
    { name: "turn_advanced", phase: "baseline" },
    { name: "turn_advanced", phase: "result", confidence: "medium" },
    { name: "scoring_failed", phase: "result" },
    { name: "scoring_recovered", phase: "result", confidence: "high" },
    { name: "illegal_snapshot", phase: "result" },
    { name: "scoring_failed", phase: "result" },
    { name: "turn_advanced", phase: "adaptive", confidence: "medium" },
  ]);
});

test("route metric wiring derives adaptive drafts and scoring outcomes from real turns", () => {
  const emitted: unknown[] = [];
  const record = createJourneyTelemetry((payload) => emitted.push(payload));
  const firstPending = scoringResponse("score_pending", 4);
  const retry = scoringResponse("retry_scoring", 5);
  const adaptiveRetry = scoringResponse("retry_scoring", 8, 1);
  const firstResult = highResultResponse(5);
  const recovered = highResultResponse(9, 1);
  const adaptiveDraft = {
    ...adaptiveRetry,
    turnVersion: 9,
    nextAction: {
      kind: "review_evidence_draft",
      draftId: "8a93c52a-e773-4cb9-9c04-fdcb82067a96",
    },
    progress: { ...adaptiveRetry.progress, phase: "review" },
    evidenceDraft: {
      draftId: "8a93c52a-e773-4cb9-9c04-fdcb82067a96",
      questionId: "adaptive_relationship_1",
      domain: "relationship",
      precision: "year",
      date: "2019",
      status: "draft",
      needsReview: true,
    },
  } satisfies VersionedJourneyResponse;

  recordScoringJourneyMetric(firstPending, firstResult, record);
  recordScoringJourneyMetric(firstPending, retry, record);
  recordScoringJourneyMetric(adaptiveRetry, recovered, record);
  recordJourneyTransitionMetric(adaptiveDraft, "turn_advanced", record);

  assert.deepEqual(emitted, [
    { name: "turn_advanced", phase: "result", confidence: "high" },
    { name: "scoring_failed", phase: "baseline" },
    { name: "scoring_recovered", phase: "result", confidence: "high" },
    { name: "turn_advanced", phase: "adaptive" },
  ]);
});

test("both HTTP routes use derived turn metrics and reserve illegal snapshots for invariants", () => {
  const journeyRoute = readFileSync(new URL("../src/app/api/birth-time-journey/route.ts", import.meta.url), "utf8");
  const guideRoute = readFileSync(new URL("../src/app/api/birth-time-guide/route.ts", import.meta.url), "utf8");

  assert.match(journeyRoute, /recordScoringJourneyMetric\(before, response\)/);
  assert.match(guideRoute, /recordJourneyTransitionMetric\(response\.turn, "turn_advanced"\)/);
  assert.doesNotMatch(guideRoute, /draft_success[^\n]+phase:\s*"baseline"/);
  assert.doesNotMatch(journeyRoute, /z\.ZodError\s*\|\|\s*error instanceof JourneyTurnInvariantError/);
});
