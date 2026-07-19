import assert from "node:assert/strict";
import test from "node:test";
import { createDynamicScoringJobStore } from "../src/lib/birth-time-dynamic-scoring-job-store.ts";
import { createDynamicScoringJobSpec } from "../src/lib/birth-time-scoring-job.ts";
import { answerTransition } from "../src/lib/birth-time-dynamic-transitions.ts";
import type { DynamicStoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";
import {
  dynamicCase,
  ownerId,
  persistedQuestion,
} from "./birth-time-dynamic-persistence-fixture.ts";

const actionId = "ab2d936b-5ce7-45d8-a0fb-33f48f960f36";

function freshCase(): DynamicStoredRectificationCase {
  const stored = dynamicCase();
  return {
    ...stored,
    eventContext: { birthDate: "1993-04-17", lat: 31.23, lon: 121.47, tz: 8 },
    dynamicControl: {
      ...stored.dynamicControl,
      answeredCount: 0,
      effectiveAnswerCount: 0,
    },
    dynamicTurnState: {
      ...stored.dynamicTurnState,
      progress: {
        ...stored.dynamicTurnState.progress,
        answeredCount: 0,
        effectiveAnswerCount: 0,
      },
    },
  };
}

test("dynamic job store sends exact private create and typed claim RPCs", async () => {
  const jobId = "85b22d7e-3adc-473d-81e1-6ad29e9b06f4";
  const now = new Date("2026-07-18T08:00:00.000Z");
  const option = persistedQuestion.options.find((candidate) => candidate.kind === "primary");
  if (!option) throw new Error("missing primary option");
  const transitioned = answerTransition({
    stored: freshCase(),
    option,
    answeredAt: now.toISOString(),
    jobId,
    nextVersion: 8,
  });
  const pending = {
    ...transitioned,
    dynamicControl: {
      ...transitioned.dynamicControl,
      lastActionReceipt: {
        actionId,
        kind: "answer_choice" as const,
        turnVersion: 7,
        questionId: persistedQuestion.questionId,
        optionId: option.optionId,
      },
    },
  };
  const spec = createDynamicScoringJobSpec(jobId, pending.choiceEvidence, now);
  let loaded = freshCase();
  const calls: { readonly name: string; readonly args: Readonly<Record<string, unknown>> }[] = [];
  const store = createDynamicScoringJobStore({
    async rpc(name, args) {
      calls.push({ name, args });
      if (name === "create_birth_time_dynamic_scoring_job") {
        loaded = {
          ...pending,
          turnVersion: 8,
          dynamicTurnState: { ...pending.dynamicTurnState, turnVersion: 8 },
          processedActionIds: [actionId],
        };
        return { data: 8, error: null };
      }
      return {
        data: [{
          claim_state: "claimed",
          algorithm_version: "birth-time-choice-scoring-v2",
        }],
        error: null,
      };
    },
  }, async () => loaded);

  const created = await store.createDynamicScoringJob(
    pending,
    7,
    actionId,
    persistedQuestion.questionId,
    spec,
  );
  const claim = await store.claimDynamicScoringJob({
    userId: ownerId,
    caseId: pending.id,
    jobId,
    evidenceFingerprint: spec.evidenceFingerprint,
    algorithmVersion: spec.algorithmVersion,
    now: now.toISOString(),
  });

  assert.equal(created.turnVersion, 8);
  assert.deepEqual(claim, {
    kind: "claimed",
    algorithmVersion: "birth-time-choice-scoring-v2",
  });
  assert.deepEqual(calls.map((call) => call.name), [
    "create_birth_time_dynamic_scoring_job",
    "claim_birth_time_dynamic_scoring_job",
  ]);
  assert.equal(calls[0]?.args.p_question_id, persistedQuestion.questionId);
  assert.equal(JSON.stringify(calls[0]?.args.p_public_turn_state).includes("candidateScores"), false);
  assert.deepEqual(
    Reflect.get(calls[0]?.args.p_private_state ?? {}, "choiceEvidence"),
    pending.choiceEvidence,
  );
});
