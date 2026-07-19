import assert from "node:assert/strict";
import test from "node:test";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import { dynamicCase, ownerId, persistedQuestion } from "./birth-time-dynamic-persistence-fixture.ts";
import { dynamicJobStore } from "./birth-time-dynamic-job-memory-store.ts";
import { memoryStore } from "./birth-time-journey-memory-store.ts";

const answerId = "9a921af8-ddcc-4d20-b4c8-fbbb3e6a814d";
const actionId = "700406ad-1ca6-437d-9f77-61354ba8e36a";

function flow(initial = dynamicCase()) {
  const memory = memoryStore(initial);
  const jobs = dynamicJobStore(memory.store, () => {
    const current = memory.savedCase();
    return current?.journeyProtocol === "dynamic-choice-v2" ? current : null;
  });
  const service = createBirthTimeJourneyService({
    store: jobs.store,
    engine: {
      async scan() { throw new Error("unexpected scan"); },
      async score() { throw new Error("unexpected score"); },
      async scoreEvents() { throw new Error("unexpected event score"); },
    },
  });
  return { memory, service };
}

test("unmatched context replays only the identical action and payload", async () => {
  const { service } = flow();
  const unmatched = persistedQuestion.options.find((option) => option.kind === "unmatched");
  if (!unmatched) throw new Error("missing unmatched option");
  const clarification = await service.answerDynamicChoice(ownerId, {
    caseId: dynamicCase().id,
    actionId: answerId,
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: unmatched.optionId,
  });
  const command = {
    caseId: dynamicCase().id,
    actionId,
    turnVersion: clarification.turnVersion,
    questionId: persistedQuestion.questionId,
    note: "更像是 2017 年",
  };
  const saved = await service.submitUnmatchedContext(ownerId, command);
  const replay = await service.submitUnmatchedContext(ownerId, command);
  assert.deepEqual(replay.nextAction, saved.nextAction);
  assert.equal(replay.turnVersion, saved.turnVersion);
  await assert.rejects(
    service.submitUnmatchedContext(ownerId, { ...command, note: "其实是 2018 年" }),
    StaleJourneyTurnError,
  );
  await assert.rejects(
    service.pauseDynamic(ownerId, dynamicCase().id, actionId, command.turnVersion),
    StaleJourneyTurnError,
  );
});

test("pause replays after a lost response but cannot impersonate finish", async () => {
  const { service } = flow();
  const saved = await service.pauseDynamic(ownerId, dynamicCase().id, actionId, 7);
  const replay = await service.pauseDynamic(ownerId, dynamicCase().id, actionId, 7);
  assert.deepEqual(replay.nextAction, saved.nextAction);
  assert.equal(replay.turnVersion, saved.turnVersion);
  await assert.rejects(
    service.finishDynamic(ownerId, dynamicCase().id, actionId, 7),
    StaleJourneyTurnError,
  );
});

test("finish replays after a lost response but cannot impersonate pause", async () => {
  const { service } = flow();
  const saved = await service.finishDynamic(ownerId, dynamicCase().id, actionId, 7);
  const replay = await service.finishDynamic(ownerId, dynamicCase().id, actionId, 7);
  assert.deepEqual(replay.nextAction, saved.nextAction);
  assert.equal(replay.turnVersion, saved.turnVersion);
  await assert.rejects(
    service.pauseDynamic(ownerId, dynamicCase().id, actionId, 7),
    StaleJourneyTurnError,
  );
});

test("answer replay is bound to the exact question and option", async () => {
  const { memory, service } = flow();
  const unknown = persistedQuestion.options.find((option) => option.kind === "unknown");
  const unmatched = persistedQuestion.options.find((option) => option.kind === "unmatched");
  if (!unknown || !unmatched) throw new Error("missing special options");
  const command = {
    caseId: dynamicCase().id,
    actionId,
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: unknown.optionId,
  };
  const saved = await service.answerDynamicChoice(ownerId, command);
  const replay = await service.answerDynamicChoice(ownerId, command);
  assert.equal(replay.turnVersion, saved.turnVersion);
  assert.equal(memory.savedCase()?.dynamicControl?.lastActionReceipt?.kind, "answer_choice");
  await assert.rejects(
    service.answerDynamicChoice(ownerId, { ...command, optionId: unmatched.optionId }),
    StaleJourneyTurnError,
  );
});

test("question commit replay is bound to the submitted fingerprints", async () => {
  const initial = {
    ...dynamicCase(),
    currentChoiceQuestion: null,
    dynamicTurnState: {
      ...dynamicCase().dynamicTurnState,
      nextAction: { kind: "generate_dynamic_question" as const },
    },
  };
  const { memory, service } = flow(initial);
  const question = {
    ...persistedQuestion,
    questionId: "af34edbf-b4b0-4ebf-9a07-5c177bc73add",
    questionFingerprint: "fresh-question",
    candidatePartitionFingerprint: "fresh-partition",
  };
  const command = { caseId: initial.id, actionId, turnVersion: 7, unmatchedNote: null };
  const saved = await service.commitDynamicQuestion(ownerId, command, question);
  const replay = await service.commitDynamicQuestion(ownerId, command, question);
  assert.deepEqual(replay.nextAction, saved.nextAction);
  assert.equal(memory.savedCase()?.dynamicControl?.lastActionReceipt?.kind, "commit_question");
  await assert.rejects(
    service.commitDynamicQuestion(ownerId, command, {
      ...question, questionFingerprint: "changed-question",
    }),
    StaleJourneyTurnError,
  );
});
