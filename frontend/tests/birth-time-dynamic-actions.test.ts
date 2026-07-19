import assert from "node:assert/strict";
import test from "node:test";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import { dynamicCase, ownerId, persistedQuestion } from "./birth-time-dynamic-persistence-fixture.ts";
import { memoryStore } from "./birth-time-journey-memory-store.ts";
import { dynamicJobStore } from "./birth-time-dynamic-job-memory-store.ts";
import { differenceBuild } from "./fixtures/birth-time-dynamic-question-fixture.ts";
import { createInitialDynamicState } from "../src/lib/birth-time-journey-dynamic-state.ts";
import { approximateAssessment, scanWithSigns } from "./birth-time-journey-test-support.ts";

const actionId = "9a921af8-ddcc-4d20-b4c8-fbbb3e6a814d";
const secondActionId = "700406ad-1ca6-437d-9f77-61354ba8e36a";

function dynamicFlow(initial = dynamicCase()) {
  const memory = memoryStore(initial);
  const jobs = dynamicJobStore(memory.store, () => {
    const value = memory.savedCase();
    return value?.journeyProtocol === "dynamic-choice-v2" ? value : null;
  });
  const service = createBirthTimeJourneyService({
    store: jobs.store,
    engine: {
      async scan() { throw new Error("unexpected scan"); },
      async score() { throw new Error("unexpected score"); },
      async scoreEvents() { throw new Error("unexpected event score"); },
      async buildDifferencePacket() { return differenceBuild; },
      async scoreChoices() { throw new Error("unexpected choice score"); },
    },
  });
  return { memory, service, jobs };
}

test("a primary click resolves private evidence and enters score_pending", async () => {
  const flow = dynamicFlow();
  const result = await flow.service.answerDynamicChoice(ownerId, {
    caseId: dynamicCase().id,
    actionId,
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: persistedQuestion.options[0].optionId,
  });

  assert.equal(result.nextAction.kind, "score_pending");
  const saved = flow.memory.savedCase();
  assert.equal(saved?.journeyProtocol, "dynamic-choice-v2");
  assert.equal(saved?.choiceAnswers.length, 1);
  assert.equal(saved?.choiceEvidence[0]?.partitionId, "window-a");
  assert.equal(saved?.dynamicControl.effectiveAnswerCount, 2);
  assert.equal(flow.jobs.count(), 1);
});

test("new assessments return the persisted v2 generation turn", async () => {
  const memory = memoryStore();
  const service = createBirthTimeJourneyService({
    store: {
      ...memory.store,
      async saveAssessment(value) {
        const initial = createInitialDynamicState(value.snapshot, "2026-07-18");
        const fixture = dynamicCase();
        memory.replaceCase({
          ...fixture,
          userId: value.userId,
          snapshot: value.snapshot,
          questionnaire: value.questionnaire,
          dynamicTurnState: initial.turn,
          ...initial.privateState,
        });
        return fixture.id;
      },
    },
    engine: {
      async scan() { return scanWithSigns(["Cancer", "Leo"]); },
      async score() { throw new Error("unexpected score"); },
      async scoreEvents() { throw new Error("unexpected event score"); },
      async buildDifferencePacket() { throw new Error("unexpected packet"); },
      async scoreChoices() { throw new Error("unexpected choice score"); },
    },
  });

  const result = await service.assess(ownerId, approximateAssessment);

  assert.equal(result.journeyProtocol, "dynamic-choice-v2");
  assert.equal(result.nextAction.kind, "generate_dynamic_question");
  assert.equal(result.turnVersion, 0);
});

test("generation returns an engine packet and commits one persisted question", async () => {
  const initial = {
    ...dynamicCase(),
    eventContext: { birthDate: "1993-04-17", lat: 31.23, lon: 121.47, tz: 8 },
    currentChoiceQuestion: null,
    dynamicTurnState: {
      ...dynamicCase().dynamicTurnState,
      nextAction: { kind: "generate_dynamic_question" as const },
    },
  };
  const flow = dynamicFlow(initial);
  const command = {
    caseId: initial.id,
    actionId,
    turnVersion: 7,
    unmatchedNote: null,
  };
  const build = await flow.service.generateDynamicQuestion(ownerId, command);
  const nextQuestion = {
    ...persistedQuestion,
    questionId: "af34edbf-b4b0-4ebf-9a07-5c177bc73add",
    opportunityId: "next-opportunity",
    questionFingerprint: "next-question-fingerprint",
    candidatePartitionFingerprint: "next-partition-fingerprint",
  };
  const committed = await flow.service.commitDynamicQuestion(
    ownerId,
    command,
    nextQuestion,
  );

  assert.equal(build.packet.caseId, differenceBuild.packet.caseId);
  assert.equal(committed.nextAction.kind, "ask_dynamic_choice");
  assert.equal(flow.memory.savedCase()?.currentChoiceQuestion?.questionId, nextQuestion.questionId);
  assert.deepEqual(flow.memory.savedCase()?.dynamicControl?.questionFingerprints, [
    persistedQuestion.questionFingerprint,
    nextQuestion.questionFingerprint,
  ]);
});

test("unmatched context is trimmed separately and generates without scoring", async () => {
  const flow = dynamicFlow();
  const unmatched = persistedQuestion.options.find((option) => option.kind === "unmatched");
  if (!unmatched) throw new Error("missing unmatched option");
  const clarification = await flow.service.answerDynamicChoice(ownerId, {
    caseId: dynamicCase().id,
    actionId,
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: unmatched.optionId,
  });
  const reframed = await flow.service.submitUnmatchedContext(ownerId, {
    caseId: dynamicCase().id,
    actionId: secondActionId,
    turnVersion: clarification.turnVersion,
    questionId: persistedQuestion.questionId,
    note: "  更像是 2017 年  ",
  });

  assert.equal(reframed.nextAction.kind, "generate_dynamic_question");
  assert.deepEqual(flow.memory.savedCase()?.agentContext, ["用户只记得大概阶段", "更像是 2017 年"]);
  assert.equal(flow.memory.savedCase()?.currentChoiceQuestion, null);
  assert.deepEqual(flow.memory.savedCase()?.choiceEvidence, []);
  assert.equal(flow.jobs.count(), 0);
});

test("pause and resume restore the exact persisted question", async () => {
  const flow = dynamicFlow();
  const paused = await flow.service.pauseDynamic(ownerId, dynamicCase().id, actionId, 7);
  const resumed = await flow.service.resumeDynamic(ownerId, dynamicCase().id);

  assert.equal(paused.nextAction.kind, "paused");
  assert.deepEqual(resumed.nextAction, dynamicCase().dynamicTurnState.nextAction);
  assert.equal(flow.memory.savedCase()?.dynamicControl?.pausedAction, null);
  assert.equal(resumed.turnVersion, 9);
});

test("a stale or forged option cannot affect private evidence", async () => {
  const primary = persistedQuestion.options.find((option) => option.kind === "primary");
  if (!primary) throw new Error("missing primary option");
  for (const command of [
    { turnVersion: 6, optionId: primary.optionId },
    { turnVersion: 7, optionId: "forged-option" },
  ]) {
    const flow = dynamicFlow();
    await assert.rejects(
      flow.service.answerDynamicChoice(ownerId, {
        caseId: dynamicCase().id,
        actionId,
        questionId: persistedQuestion.questionId,
        ...command,
      }),
      StaleJourneyTurnError,
    );
    assert.deepEqual(flow.memory.savedCase()?.choiceEvidence, []);
  }
});

test("unknown and unmatched increment only answered count and never score", async () => {
  for (const kind of ["unknown", "unmatched"] as const) {
    const flow = dynamicFlow();
    const option = persistedQuestion.options.find((candidate) => candidate.kind === kind);
    if (!option) throw new Error("missing special option");
    const result = await flow.service.answerDynamicChoice(ownerId, {
      caseId: dynamicCase().id,
      actionId,
      turnVersion: 7,
      questionId: persistedQuestion.questionId,
      optionId: option.optionId,
    });

    assert.equal(result.progress.answeredCount, 2);
    assert.equal(result.progress.effectiveAnswerCount, 1);
    assert.deepEqual(flow.memory.savedCase()?.choiceEvidence, []);
    assert.equal(flow.jobs.count(), 0);
    assert.equal(result.nextAction.kind, kind === "unknown"
      ? "generate_dynamic_question"
      : "clarify_unmatched_answer");
  }
});
