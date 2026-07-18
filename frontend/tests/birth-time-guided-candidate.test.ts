import assert from "node:assert/strict";
import test from "node:test";
import { candidateResultSchema } from "../src/lib/birth-time-evidence.ts";
import { createGuidedCandidateActions } from "../src/lib/birth-time-guided-candidate.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import type { StoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";
import type { NextAction } from "../src/lib/birth-time-journey-turn.ts";
import {
  draftActionId,
  guidedCase,
  journeyCaseId,
  memoryStore,
  secondActionId,
} from "./birth-time-journey-test-support.ts";

const mediumCandidate = candidateResultSchema.parse({
  resultId: "345087cc-7e7f-4b37-90e5-f0c0a6e5b7a7",
  confidence: "medium",
  canApply: false,
  winningSegment: { startTime: "05:18", endTime: "05:24", representativeTime: "05:21", widthMinutes: 7 },
  eventCount: 4,
  domainCount: 3,
  topScore: 14.4,
  secondScore: 12.1,
  marginPercent: 15.97,
  reasons: [],
  evidence: [],
  algorithmVersion: "birth-time-event-scoring-v1",
});

const highCandidate = candidateResultSchema.parse({
  ...mediumCandidate,
  resultId: "8c48d5a8-cf2a-43a5-90f9-e39a726de265",
  confidence: "high",
  canApply: true,
  winningSegment: { startTime: "05:19", endTime: "05:23", representativeTime: "05:21", widthMinutes: 5 },
  eventCount: 5,
  domainCount: 4,
  topScore: 17.8,
  secondScore: 13.5,
  marginPercent: 24.16,
});

function candidateCase(candidate: typeof mediumCandidate | typeof highCandidate, version = 4) {
  const stored = guidedCase({ version, candidateResult: candidate });
  const baseTurn = stored.turnState;
  if (!baseTurn) throw new Error("test fixture requires a guided turn");
  const high = candidate.confidence === "high";
  const nextAction: NextAction = high
    ? { kind: "request_candidate_confirmation", resultId: candidate.resultId }
    : { kind: "present_medium_result", resultId: candidate.resultId };
  return {
    ...stored,
    snapshot: {
      ...stored.snapshot,
      state: high ? "confirming" : "candidate",
      assistantIntent: high ? "confirm_candidate_time" : "present_candidate_result",
      input: high ? "candidate_confirmation" : "candidate_actions",
      confidence: candidate.confidence,
      canApply: high,
    },
    turnState: {
      ...baseTurn,
      turnVersion: version,
      nextAction,
      progress: { ...baseTurn.progress, phase: "result" },
      permissions: { canConfirmCandidate: high },
    },
  } satisfies StoredRectificationCase;
}

test("medium candidate save advances one version without applying a minute", async () => {
  const memory = memoryStore(candidateCase(mediumCandidate));
  const actions = createGuidedCandidateActions({ store: memory.store });

  const result = await actions.save({ userId: "user-1", caseId: journeyCaseId, actionId: draftActionId, expectedVersion: 4, resultId: mediumCandidate.resultId });

  assert.equal(result.turnVersion, 5);
  assert.equal(result.nextAction.kind, "candidate_saved");
  assert.equal(result.snapshot.activeTime, null);
  assert.equal(memory.guidedCandidateWrites(), 1);
});

test("duplicate medium save replays once and stale new action fails", async () => {
  const memory = memoryStore(candidateCase(mediumCandidate));
  const actions = createGuidedCandidateActions({ store: memory.store });
  const first = await actions.save({ userId: "user-1", caseId: journeyCaseId, actionId: draftActionId, expectedVersion: 4, resultId: mediumCandidate.resultId });
  const duplicate = await actions.save({ userId: "user-1", caseId: journeyCaseId, actionId: draftActionId, expectedVersion: 4, resultId: mediumCandidate.resultId });

  assert.deepEqual(duplicate, first);
  assert.equal(memory.guidedCandidateWrites(), 1);
  await assert.rejects(
    actions.save({ userId: "user-1", caseId: journeyCaseId, actionId: secondActionId, expectedVersion: 4, resultId: mediumCandidate.resultId }),
    StaleJourneyTurnError,
  );
});

test("high confirmation requires matching result and representative time", async () => {
  const memory = memoryStore(candidateCase(highCandidate));
  const actions = createGuidedCandidateActions({ store: memory.store });

  await assert.rejects(actions.confirm({ userId: "user-1", caseId: journeyCaseId, actionId: draftActionId, expectedVersion: 4, resultId: highCandidate.resultId, time: "05:22" }));
  assert.equal(memory.guidedCandidateWrites(), 0);

  const ready = await actions.confirm({ userId: "user-1", caseId: journeyCaseId, actionId: secondActionId, expectedVersion: 4, resultId: highCandidate.resultId, time: "05:21" });
  assert.equal(ready.nextAction.kind, "ready");
  assert.equal(ready.snapshot.activeTime, "05:21");
  assert.equal(memory.guidedCandidateWrites(), 1);
});

test("medium result cannot use guided confirmation", async () => {
  const memory = memoryStore(candidateCase(mediumCandidate));
  const actions = createGuidedCandidateActions({ store: memory.store });

  await assert.rejects(actions.confirm({ userId: "user-1", caseId: journeyCaseId, actionId: draftActionId, expectedVersion: 4, resultId: mediumCandidate.resultId, time: "05:21" }));
  assert.equal(memory.guidedCandidateWrites(), 0);
});
