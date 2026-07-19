import assert from "node:assert/strict";
import test from "node:test";
import { createJourneyTelemetry } from "../src/lib/birth-time-journey-telemetry.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import {
  actionIds,
  assertLegalTurn,
  candidate,
  confirmDirectEvidence,
  createHarness,
  guidedCase,
  journeyCaseId,
  reachScoring,
} from "./birth-time-agent-flow-test-support.ts";

test("fake Agent and engine complete baseline, adaptive, low, and no-apply flow", async () => {
  const harness = createHarness({ initial: guidedCase(), result: candidate("low", "10000000-0000-4000-8000-000000000001") });
  let turn = await reachScoring({ harness, useGuide: true });
  assert.equal(harness.scoreEventsCalls(), 0, "confirming evidence only creates a pending job");

  turn = await harness.service.pollScoringJob(
    "user-1", journeyCaseId, turn.nextAction.kind === "score_pending" ? turn.nextAction.jobId : "",
  );
  assertLegalTurn(turn);
  assert.equal(turn.nextAction.kind, "ask_adaptive_evidence");
  assert.equal(turn.snapshot.activeTime, null);

  let skipAction: (typeof actionIds)[number] = actionIds[6];
  while (turn.nextAction.kind === "ask_adaptive_evidence") {
    turn = await harness.service.skipEvidenceQuestion("user-1", journeyCaseId, skipAction, turn.turnVersion);
    assertLegalTurn(turn);
    skipAction = actionIds[actionIds.indexOf(skipAction) + 1] ?? actionIds[7];
  }
  assert.equal(turn.nextAction.kind, "present_low_result");
  assert.equal(turn.candidateResult?.confidence, "low");
  assert.equal(turn.snapshot.activeTime, null);
  assert.equal(harness.memory.savedCase()?.snapshot.activeTime, null);
  await assert.rejects(harness.candidateActions.confirm({
    userId: "user-1", caseId: journeyCaseId, actionId: actionIds[10], expectedVersion: turn.turnVersion,
    resultId: turn.candidateResult?.resultId ?? "", time: "14:24",
  }));
  assert.equal(harness.memory.savedCase()?.snapshot.activeTime, null);
});

test("medium result is save-only and never applies an active minute", async () => {
  const medium = candidate("medium", "20000000-0000-4000-8000-000000000001");
  const harness = createHarness({ initial: guidedCase(), result: medium });
  const pending = await reachScoring({ harness });
  const result = await harness.service.pollScoringJob("user-1", journeyCaseId, pending.nextAction.kind === "score_pending" ? pending.nextAction.jobId : "");
  assertLegalTurn(result);
  assert.equal(result.nextAction.kind, "present_medium_result");
  assert.equal(result.permissions.canConfirmCandidate, false);
  await assert.rejects(harness.candidateActions.confirm({
    userId: "user-1", caseId: journeyCaseId, actionId: actionIds[8], expectedVersion: result.turnVersion,
    resultId: medium.resultId, time: "14:24",
  }));
  assert.equal(harness.memory.savedCase()?.snapshot.activeTime, null);
  const saved = await harness.candidateActions.save({
    userId: "user-1", caseId: journeyCaseId, actionId: actionIds[6], expectedVersion: result.turnVersion, resultId: medium.resultId,
  });
  assertLegalTurn(saved);
  assert.equal(saved.nextAction.kind, "candidate_saved");
  assert.equal(saved.snapshot.activeTime, null);
});

test("high result applies only after explicit matching representative-time confirmation", async () => {
  const high = candidate("high", "30000000-0000-4000-8000-000000000001");
  const harness = createHarness({
    initial: guidedCase(),
    result: candidate("low", "30000000-0000-4000-8000-000000000002"),
    resultAfterAdaptive: high,
  });
  const pending = await reachScoring({ harness });
  const adaptive = await harness.service.pollScoringJob("user-1", journeyCaseId, pending.nextAction.kind === "score_pending" ? pending.nextAction.jobId : "");
  assert.equal(adaptive.nextAction.kind, "ask_adaptive_evidence");
  const nextPending = await confirmDirectEvidence({
    harness,
    turn: adaptive,
    proposalActionId: actionIds[6],
    confirmActionId: actionIds[7],
    date: "2013",
  });
  const result = await harness.service.pollScoringJob("user-1", journeyCaseId, nextPending.nextAction.kind === "score_pending" ? nextPending.nextAction.jobId : "");
  assertLegalTurn(result);
  assert.equal(result.nextAction.kind, "request_candidate_confirmation");
  assert.equal(result.permissions.canConfirmCandidate, true);
  await assert.rejects(harness.candidateActions.confirm({
    userId: "user-1", caseId: journeyCaseId, actionId: actionIds[8], expectedVersion: result.turnVersion,
    resultId: high.resultId, time: "14:23",
  }));
  assert.equal(harness.memory.savedCase()?.snapshot.activeTime, null);
  const ready = await harness.candidateActions.confirm({
    userId: "user-1", caseId: journeyCaseId, actionId: actionIds[9], expectedVersion: result.turnVersion,
    resultId: high.resultId, time: high.winningSegment?.representativeTime ?? "",
  });
  assertLegalTurn(ready);
  assert.equal(ready.nextAction.kind, "ready");
  assert.equal(ready.snapshot.activeTime, "14:24");
});

test("a scorer cannot forge four events and three domains over three persisted events", async () => {
  const declaredHigh = {
    ...candidate("high", "31000000-0000-4000-8000-000000000001"),
    domainCount: 3,
  };
  const harness = createHarness({ initial: guidedCase(), result: declaredHigh });
  const pending = await reachScoring({ harness });
  const result = await harness.service.pollScoringJob(
    "user-1",
    journeyCaseId,
    pending.nextAction.kind === "score_pending" ? pending.nextAction.jobId : "",
  );

  assertLegalTurn(result);
  assert.equal(result.nextAction.kind, "retry_scoring");
  assert.equal(result.candidateResult, null);
  assert.equal(harness.memory.savedCase()?.snapshot.activeTime, null);
});

test("resume preserves ask, draft, score-pending, and confirmation states", async () => {
  const ask = createHarness({ initial: guidedCase(), result: candidate("low", "71000000-0000-4000-8000-000000000001") });
  const askTurn = await ask.service.resume("user-1", journeyCaseId);
  assertLegalTurn(askTurn);
  assert.equal(askTurn.nextAction.kind, "ask_baseline_evidence");

  const draft = createHarness({ initial: guidedCase(), result: candidate("low", "72000000-0000-4000-8000-000000000001") });
  const draftStart = await draft.service.resume("user-1", journeyCaseId);
  assert.equal(draftStart.nextAction.kind, "ask_baseline_evidence");
  await draft.service.proposeEvidenceDraft("user-1", journeyCaseId, actionIds[0], draftStart.turnVersion, {
    domain: draftStart.nextAction.question.domain, precision: "year", date: "2010",
  });
  const draftResume = await draft.service.resume("user-1", journeyCaseId);
  assertLegalTurn(draftResume);
  assert.equal(draftResume.nextAction.kind, "review_evidence_draft");

  const scoring = createHarness({ initial: guidedCase(), result: candidate("medium", "73000000-0000-4000-8000-000000000001") });
  const pending = await reachScoring({ harness: scoring });
  const pendingResume = await scoring.service.resume("user-1", journeyCaseId);
  assertLegalTurn(pendingResume);
  assert.equal(pendingResume.nextAction.kind, "score_pending");
  assert.equal(pendingResume.nextAction.jobId, pending.nextAction.kind === "score_pending" ? pending.nextAction.jobId : "");

  const confirming = createHarness({
    initial: guidedCase(),
    result: candidate("low", "74000000-0000-4000-8000-000000000002"),
    resultAfterAdaptive: candidate("high", "74000000-0000-4000-8000-000000000001"),
  });
  const confirmPending = await reachScoring({ harness: confirming });
  const confirmAdaptive = await confirming.service.pollScoringJob("user-1", journeyCaseId, confirmPending.nextAction.kind === "score_pending" ? confirmPending.nextAction.jobId : "");
  const confirmNextPending = await confirmDirectEvidence({
    harness: confirming,
    turn: confirmAdaptive,
    proposalActionId: actionIds[6],
    confirmActionId: actionIds[7],
    date: "2013",
  });
  const confirmation = await confirming.service.pollScoringJob("user-1", journeyCaseId, confirmNextPending.nextAction.kind === "score_pending" ? confirmNextPending.nextAction.jobId : "");
  assert.equal(confirmation.nextAction.kind, "request_candidate_confirmation");
  const confirmationResume = await confirming.service.resume("user-1", journeyCaseId);
  assertLegalTurn(confirmationResume);
  assert.equal(confirmationResume.nextAction.kind, "request_candidate_confirmation");
});

test("scoring failure is retryable and resume does not invoke the engine", async () => {
  const medium = candidate("medium", "40000000-0000-4000-8000-000000000001");
  const harness = createHarness({ initial: guidedCase(), result: medium, failFirstScore: true });
  const pending = await reachScoring({ harness });
  const jobId = pending.nextAction.kind === "score_pending" ? pending.nextAction.jobId : "";
  const failed = await harness.service.pollScoringJob("user-1", journeyCaseId, jobId);
  assertLegalTurn(failed);
  assert.equal(failed.nextAction.kind, "retry_scoring");
  const callsAfterFailure = harness.scoreEventsCalls();
  const resumed = await harness.service.resume("user-1", journeyCaseId);
  assertLegalTurn(resumed);
  assert.deepEqual(resumed.nextAction, failed.nextAction);
  assert.equal(harness.scoreEventsCalls(), callsAfterFailure);
  const recovered = await harness.service.pollScoringJob("user-1", journeyCaseId, jobId);
  assertLegalTurn(recovered);
  assert.equal(recovered.nextAction.kind, "present_medium_result");
});

test("duplicate actions replay once and stale versions cannot overwrite a turn", async () => {
  const harness = createHarness({ initial: guidedCase(), result: candidate("low", "50000000-0000-4000-8000-000000000001") });
  const initial = await harness.service.resume("user-1", journeyCaseId);
  assertLegalTurn(initial);
  assert.equal(initial.nextAction.kind, "ask_baseline_evidence");
  const first = await harness.service.proposeEvidenceDraft("user-1", journeyCaseId, actionIds[0], initial.turnVersion, {
    domain: initial.nextAction.question.domain, precision: "year", date: "2010",
  });
  assertLegalTurn(first);
  assert.equal(first.nextAction.kind, "review_evidence_draft");
  const duplicate = await harness.service.proposeEvidenceDraft("user-1", journeyCaseId, actionIds[0], initial.turnVersion, {
    domain: initial.nextAction.question.domain, precision: "year", date: "2010",
  });
  assert.deepEqual(duplicate.nextAction, first.nextAction);
  assert.equal(harness.memory.committedTurnWrites(), 1);
  await assert.rejects(harness.service.skipEvidenceQuestion("user-1", journeyCaseId, actionIds[2], initial.turnVersion), StaleJourneyTurnError);
  assert.equal(harness.memory.savedCase()?.turnVersion, first.turnVersion);
});

test("telemetry-facing flow state contains no personal fields", async () => {
  const harness = createHarness({ initial: guidedCase(), result: candidate("low", "60000000-0000-4000-8000-000000000001") });
  const turn = await harness.service.resume("user-1", journeyCaseId);
  assertLegalTurn(turn);
  const emitted: unknown[] = [];
  const record = createJourneyTelemetry((payload) => emitted.push(payload));
  record("turn_advanced", { phase: turn.nextAction.kind === "ask_baseline_evidence" ? "baseline" : "result" });
  const payload = emitted[0];
  assert.ok(payload !== null && typeof payload === "object");
  assert.deepEqual(Object.keys(payload), ["name", "phase"]);
  assert.equal("caseId" in payload, false);
  assert.equal("userId" in payload, false);
  assert.equal("birthDate" in payload, false);
  assert.equal("coordinates" in payload, false);
  assert.equal("message" in payload, false);
});
