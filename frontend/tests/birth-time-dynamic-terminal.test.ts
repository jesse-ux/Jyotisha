import assert from "node:assert/strict";
import test from "node:test";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import { BirthTimeDynamicActionError } from "../src/lib/birth-time-dynamic-actions.ts";
import type { DynamicStoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";
import { dynamicCase, ownerId, persistedQuestion } from "./birth-time-dynamic-persistence-fixture.ts";
import { memoryStore } from "./birth-time-journey-memory-store.ts";

const actionId = "38dd8315-7d6f-4af8-b2e4-a4062926f5ca";

function terminalCase() {
  const stored = dynamicCase();
  return {
    ...stored,
    currentChoiceQuestion: null,
    dynamicTurnState: {
      ...stored.dynamicTurnState,
      nextAction: { kind: "present_medium_result" as const, resultId: "result-1" },
      progress: { ...stored.dynamicTurnState.progress, phase: "result" as const },
    },
  };
}

function journeyFlow(initial: DynamicStoredRectificationCase = terminalCase()) {
  const memory = memoryStore(initial);
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: {
      async scan() { throw new Error("unexpected scan"); },
      async score() { throw new Error("unexpected score"); },
      async scoreEvents() { throw new Error("unexpected event score"); },
      async buildDifferencePacket() { throw new Error("unexpected packet"); },
      async scoreChoices() { throw new Error("unexpected choice score"); },
    },
  });
  return { memory, service };
}

test("terminal resume returns the stored action byte-for-byte", async () => {
  const flow = journeyFlow();
  const resumed = await flow.service.resumeDynamic(ownerId, dynamicCase().id);

  assert.deepEqual(resumed.nextAction, terminalCase().dynamicTurnState.nextAction);
  assert.equal(flow.memory.committedTurnWrites(), 0);
});

test("terminal answer pause finish and generation commits are rejected", async () => {
  const operations = [
    (service: ReturnType<typeof journeyFlow>["service"]) => service.answerDynamicChoice(ownerId, {
      caseId: dynamicCase().id,
      actionId,
      turnVersion: 7,
      questionId: persistedQuestion.questionId,
      optionId: persistedQuestion.options[0].optionId,
    }),
    (service: ReturnType<typeof journeyFlow>["service"]) => service.pauseDynamic(ownerId, dynamicCase().id, actionId, 7),
    (service: ReturnType<typeof journeyFlow>["service"]) => service.finishDynamic(ownerId, dynamicCase().id, actionId, 7),
    (service: ReturnType<typeof journeyFlow>["service"]) => service.generateDynamicQuestion(ownerId, {
      caseId: dynamicCase().id,
      actionId,
      turnVersion: 7,
      unmatchedNote: null,
    }),
    (service: ReturnType<typeof journeyFlow>["service"]) => service.commitDynamicQuestion(ownerId, {
      caseId: dynamicCase().id,
      actionId,
      turnVersion: 7,
      unmatchedNote: null,
    }, persistedQuestion),
  ];
  for (const operation of operations) {
    const flow = journeyFlow();
    await assert.rejects(operation(flow.service), BirthTimeDynamicActionError);
    assert.equal(flow.memory.committedTurnWrites(), 0);
  }
});

test("explicit finish preserves the current range and cannot restart on resume", async () => {
  const initial = dynamicCase();
  const flow = journeyFlow(initial);
  const finished = await flow.service.finishDynamic(
    ownerId,
    initial.id,
    actionId,
    initial.turnVersion,
  );
  const resumed = await flow.service.resumeDynamic(ownerId, initial.id);

  assert.deepEqual(finished.nextAction, { kind: "present_low_result", resultId: null });
  assert.deepEqual(finished.progress.currentRange, initial.dynamicTurnState.progress.currentRange);
  assert.deepEqual(resumed.nextAction, finished.nextAction);
  assert.equal(flow.memory.committedTurnWrites(), 1);
});
