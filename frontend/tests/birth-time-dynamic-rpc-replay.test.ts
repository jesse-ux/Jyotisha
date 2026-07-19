import assert from "node:assert/strict";
import test from "node:test";
import { createDynamicScoringJobStore } from "../src/lib/birth-time-dynamic-scoring-job-store.ts";
import { createDynamicTurnPersistence } from "../src/lib/birth-time-journey-dynamic-persistence.ts";
import { createDynamicScoringJobSpec } from "../src/lib/birth-time-scoring-job.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import { answerTransition } from "../src/lib/birth-time-dynamic-transitions.ts";
import type { DynamicStoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";
import { actionId, dynamicCase, persistedQuestion } from "./birth-time-dynamic-persistence-fixture.ts";

function savedTurn(
  kind: "pause" | "finish" = "pause",
): DynamicStoredRectificationCase {
  const stored = dynamicCase();
  return {
    ...stored,
    turnVersion: 8,
    processedActionIds: [actionId],
    dynamicTurnState: {
      ...stored.dynamicTurnState,
      turnVersion: 8,
      nextAction: kind === "pause" ? { kind: "paused" } : { kind: "present_low_result", resultId: null },
    },
    dynamicControl: {
      ...stored.dynamicControl,
      lastActionReceipt: { actionId, kind, turnVersion: 7 },
    },
  };
}

test("normal and duplicate RPC success reload the exact receipt", async () => {
  const loaded = savedTurn();
  const proposed = { ...loaded, turnVersion: 7 };
  const persistence = createDynamicTurnPersistence({
    async rpc() { return { data: 8, error: null }; },
  }, async () => loaded, () => "2026-07-18");

  const first = await persistence.saveDynamicTurn(proposed, 7, actionId);
  const duplicate = await persistence.saveDynamicTurn(proposed, 7, actionId);

  assert.equal(first, loaded);
  assert.equal(duplicate, loaded);
});

test("a concurrent different action cannot use a successful RPC as replay", async () => {
  const proposed = { ...savedTurn(), turnVersion: 7 };
  const concurrent = savedTurn("finish");
  const persistence = createDynamicTurnPersistence({
    async rpc() { return { data: 8, error: null }; },
  }, async () => concurrent, () => "2026-07-18");

  await assert.rejects(
    persistence.saveDynamicTurn(proposed, 7, actionId),
    StaleJourneyTurnError,
  );
});

function pendingTurn(): DynamicStoredRectificationCase {
  const stored = dynamicCase();
  const option = persistedQuestion.options.find((item) => item.kind === "primary");
  if (!option) throw new Error("missing primary option");
  const transitioned = answerTransition({
    stored,
    option,
    answeredAt: "2026-07-18T08:00:00.000Z",
    jobId: "85b22d7e-3adc-473d-81e1-6ad29e9b06f4",
    nextVersion: 8,
  });
  return {
    ...transitioned,
    dynamicControl: {
      ...transitioned.dynamicControl,
      lastActionReceipt: {
        actionId,
        kind: "answer_choice",
        turnVersion: 7,
        questionId: persistedQuestion.questionId,
        optionId: option.optionId,
      },
    },
  };
}

test("dynamic scoring creation accepts only exact duplicate-success receipts", async () => {
  const pending = pendingTurn();
  const spec = createDynamicScoringJobSpec(
    "85b22d7e-3adc-473d-81e1-6ad29e9b06f4",
    pending.choiceEvidence,
    new Date("2026-07-18T08:00:00.000Z"),
  );
  let loaded = {
    ...pending,
    turnVersion: 8,
    dynamicTurnState: { ...pending.dynamicTurnState, turnVersion: 8 },
    processedActionIds: [actionId],
  };
  const store = createDynamicScoringJobStore({
    async rpc() { return { data: 8, error: null }; },
  }, async () => loaded);
  const exact = await store.createDynamicScoringJob(
    pending, 7, actionId, persistedQuestion.questionId, spec,
  );
  assert.equal(exact, loaded);

  loaded = {
    ...loaded,
    dynamicControl: {
      ...loaded.dynamicControl,
      lastActionReceipt: {
        actionId,
        kind: "answer_choice",
        turnVersion: 7,
        questionId: persistedQuestion.questionId,
        optionId: persistedQuestion.options[1].optionId,
      },
    },
  };
  await assert.rejects(
    store.createDynamicScoringJob(pending, 7, actionId, persistedQuestion.questionId, spec),
    StaleJourneyTurnError,
  );
});
