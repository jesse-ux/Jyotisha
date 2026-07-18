import assert from "node:assert/strict";
import test from "node:test";
import { createDynamicTurnPersistence } from "../src/lib/birth-time-journey-dynamic-persistence.ts";
import {
  BirthTimeJourneyStoreError,
  StaleJourneyTurnError,
} from "../src/lib/birth-time-journey-turn-persistence.ts";
import type { DynamicStoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";
import {
  caseId,
  dynamicCase,
  ownerId,
} from "./birth-time-dynamic-persistence-fixture.ts";
import { lowCandidate } from "./birth-time-journey-test-support.ts";

const jobId = "8c9d09e8-91b6-4335-b891-122f205a050c";
const fingerprint = "evidence-fingerprint";
const algorithmVersion = "birth-time-event-scoring-v1";

function scoringCase(
  action: "complete" | "fail",
): DynamicStoredRectificationCase {
  const stored = dynamicCase();
  return {
    ...stored,
    candidateResult: action === "complete" ? lowCandidate : null,
    dynamicTurnState: {
      ...stored.dynamicTurnState,
      nextAction: action === "complete"
        ? { kind: "present_low_result", resultId: lowCandidate.resultId }
        : { kind: "retry_scoring", jobId },
      progress: { ...stored.dynamicTurnState.progress, phase: action === "complete" ? "result" : "scoring" },
    },
  };
}

function successfulRpc(target: DynamicStoredRectificationCase) {
  let stored = dynamicCase();
  let committed = false;
  const calls: { readonly name: string; readonly args: Readonly<Record<string, unknown>> }[] = [];
  const persistence = createDynamicTurnPersistence({
    async rpc(name, args) {
      calls.push({ name, args });
      if (!committed) {
        stored = {
          ...target,
          turnVersion: 8,
          dynamicTurnState: { ...target.dynamicTurnState, turnVersion: 8 },
        };
        committed = true;
      }
      return { data: 8, error: null };
    },
  }, async () => stored, () => "2026-07-18");
  return { calls, persistence };
}

function assertNoPublicLeak(args: Readonly<Record<string, unknown>>) {
  const publicPayload = JSON.stringify({
    turn: args.p_public_turn_state,
    snapshot: args.p_snapshot,
    candidate: args.p_candidate_result,
  });
  for (const forbidden of [
    "partitionId",
    "candidateScores",
    "agentContext",
    "active_birth_time",
    "birth_time",
    "activeBirthTime",
    "birthTime",
  ]) assert.equal(publicPayload.includes(forbidden), false);
}

test("dynamic scoring completion calls the exact RPC and replays the stored turn", async () => {
  const value = scoringCase("complete");
  const fake = successfulRpc(value);
  const command = { expectedVersion: 7, jobId, evidenceFingerprint: fingerprint, algorithmVersion };

  const first = await fake.persistence.completeDynamicScoringJob(value, command);
  const replay = await fake.persistence.completeDynamicScoringJob(value, command);

  assert.equal(first.turnVersion, 8);
  assert.equal(replay, first);
  assert.deepEqual(fake.calls.map((call) => call.name), [
    "complete_birth_time_dynamic_scoring_job",
    "complete_birth_time_dynamic_scoring_job",
  ]);
  assert.deepEqual(fake.calls[0]?.args, {
    p_user_id: ownerId,
    p_case_id: caseId,
    p_job_id: jobId,
    p_expected_version: 7,
    p_evidence_fingerprint: fingerprint,
    p_algorithm_version: algorithmVersion,
    p_public_turn_state: { ...value.dynamicTurnState, turnVersion: 8 },
    p_snapshot: value.snapshot,
    p_candidate_result: lowCandidate,
    p_private_state: {
      candidateModel: value.candidateModel,
      currentChoiceQuestion: value.currentChoiceQuestion,
      choiceAnswers: value.choiceAnswers,
      choiceEvidence: value.choiceEvidence,
      dynamicControl: value.dynamicControl,
      agentContext: value.agentContext,
    },
  });
  assertNoPublicLeak(fake.calls[0]?.args ?? {});
});

test("dynamic scoring failure calls the exact RPC and replays the stored turn", async () => {
  const value = scoringCase("fail");
  const fake = successfulRpc(value);
  const command = {
    expectedVersion: 7,
    jobId,
    evidenceFingerprint: fingerprint,
    algorithmVersion,
    failureCode: "engine_unavailable",
  };

  const first = await fake.persistence.failDynamicScoringJob(value, command);
  const replay = await fake.persistence.failDynamicScoringJob(value, command);

  assert.equal(first.turnVersion, 8);
  assert.equal(replay, first);
  assert.deepEqual(fake.calls.map((call) => call.name), [
    "fail_birth_time_dynamic_scoring_job",
    "fail_birth_time_dynamic_scoring_job",
  ]);
  assert.deepEqual(fake.calls[0], {
    name: "fail_birth_time_dynamic_scoring_job",
    args: {
      p_user_id: ownerId,
      p_case_id: caseId,
      p_job_id: jobId,
      p_expected_version: 7,
      p_evidence_fingerprint: fingerprint,
      p_algorithm_version: algorithmVersion,
      p_failure_code: "engine_unavailable",
      p_public_turn_state: { ...value.dynamicTurnState, turnVersion: 8 },
      p_private_state: {
        candidateModel: value.candidateModel,
        currentChoiceQuestion: value.currentChoiceQuestion,
        choiceAnswers: value.choiceAnswers,
        choiceEvidence: value.choiceEvidence,
        dynamicControl: value.dynamicControl,
        agentContext: value.agentContext,
      },
    },
  });
  assertNoPublicLeak(fake.calls[0]?.args ?? {});
});

test("dynamic scoring persistence rejects malformed versions and maps RPC errors", async () => {
  const value = scoringCase("fail");
  let currentVersion = 9;
  let completionCalls = 0;
  const persistence = createDynamicTurnPersistence({
    async rpc(name) {
      if (name === "complete_birth_time_dynamic_scoring_job") {
        completionCalls += 1;
        return { data: completionCalls === 1 ? "8" : 9, error: null };
      }
      if (name === "fail_birth_time_dynamic_scoring_job" && currentVersion === 9) {
        return { data: null, error: { message: "stale_birth_time_dynamic_scoring_job" } };
      }
      return { data: null, error: { message: "database unavailable" } };
    },
  }, async () => ({
    ...dynamicCase(),
    turnVersion: currentVersion,
    dynamicTurnState: { ...dynamicCase().dynamicTurnState, turnVersion: currentVersion },
  }), () => "2026-07-18");

  await assert.rejects(
    persistence.completeDynamicScoringJob({ ...value, candidateResult: lowCandidate }, {
      expectedVersion: 7, jobId, evidenceFingerprint: fingerprint, algorithmVersion,
    }),
    BirthTimeJourneyStoreError,
  );
  await assert.rejects(
    persistence.completeDynamicScoringJob({ ...value, candidateResult: lowCandidate }, {
      expectedVersion: 7, jobId, evidenceFingerprint: fingerprint, algorithmVersion,
    }),
    BirthTimeJourneyStoreError,
  );
  await assert.rejects(
    persistence.failDynamicScoringJob(value, {
      expectedVersion: 7, jobId, evidenceFingerprint: fingerprint,
      algorithmVersion, failureCode: "engine_unavailable",
    }),
    (error) => error instanceof StaleJourneyTurnError
      && error.expectedVersion === 7
      && error.currentVersion === 9,
  );
  currentVersion = 10;
  await assert.rejects(
    persistence.failDynamicScoringJob(value, {
      expectedVersion: 7, jobId, evidenceFingerprint: fingerprint,
      algorithmVersion, failureCode: "engine_unavailable",
    }),
    BirthTimeJourneyStoreError,
  );
});
