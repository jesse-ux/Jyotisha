import assert from "node:assert/strict";
import test from "node:test";
import { BirthTimeDynamicStateMissingError, createDynamicTurnPersistence } from "../src/lib/birth-time-journey-dynamic-persistence.ts";
import { saveDynamicAssessment } from "../src/lib/birth-time-journey-dynamic-case.ts";
import { BirthTimeJourneyStoreError, loadStoredRectificationCase, StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import type { StoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";
import { assessBirthTime } from "../src/lib/birth-time-journey.ts";
import { dynamicJourneyTurnStateSchema } from "../src/lib/birth-time-journey-turn-protocol.ts";
import { assertLegacyJourneyMutation } from "../src/lib/birth-time-evidence-service.ts";
import { createInitialDynamicState, dynamicPrivateStateSchema } from "../src/lib/birth-time-journey-dynamic-state.ts";
import {
  actionId,
  caseId,
  dynamicCase,
  legacyCase,
  loadClient,
  ownerId,
  persistedQuestion,
  privateRow,
  rpcPersistence,
  snapshot,
} from "./birth-time-dynamic-persistence-fixture.ts";
import { memoryStore } from "./birth-time-journey-memory-store.ts";
import { savedPauseReceipt, withPauseReceipt } from "./birth-time-dynamic-receipt-test-support.ts";

test("v2 load restores the exact private question and candidate model", async () => {
  const loaded = await loadStoredRectificationCase(loadClient(privateRow), ownerId, caseId);

  assert.equal(loaded?.journeyProtocol, "dynamic-choice-v2");
  assert.deepEqual(loaded?.currentChoiceQuestion, persistedQuestion);
  assert.deepEqual(loaded?.candidateModel, privateRow.candidate_model);
  assert.deepEqual(loaded?.dynamicControl?.questionFingerprints, [persistedQuestion.questionFingerprint]);
  assert.deepEqual(loaded?.agentContext, privateRow.agent_context);
  assert.deepEqual(loaded?.choiceAnswers, privateRow.choice_answers);
  assert.deepEqual(loaded?.choiceEvidence, privateRow.choice_evidence);
});

test("new v2 cases initialize a dated private control state and public generation turn", () => {
  const initial = createInitialDynamicState(snapshot, "2026-07-18");

  assert.equal(initial.turn.journeyProtocol, "dynamic-choice-v2");
  assert.equal(initial.turn.nextAction.kind, "generate_dynamic_question");
  assert.equal(initial.privateState.dynamicControl.asOfDate, "2026-07-18");
  assert.deepEqual(initial.privateState.choiceAnswers, []);
  assert.deepEqual(initial.privateState.choiceEvidence, []);
  assert.equal(JSON.stringify(initial.turn).includes("candidateModel"), false);
  assert.equal(JSON.stringify(initial.turn).includes("agentContext"), false);
});

test("unknown birth time initializes the full-day dynamic range", () => {
  const unknown = assessBirthTime({
    date: "1990-01-01",
    source: "unknown",
    clue: "",
    location: { lat: 31.23, lon: 121.47, tz: 8 },
  }, { kind: "not_required" });

  const initial = createInitialDynamicState(unknown, "2026-07-18");

  assert.deepEqual(initial.turn.progress.currentRange, {
    startTime: "00:00",
    endTime: "23:59",
  });
  assert.deepEqual(initial.privateState.dynamicControl.recentRanges, [
    { startTime: "00:00", endTime: "23:59" },
  ]);
});

test("mixed-null reported ranges fail instead of inventing one boundary", () => {
  const mixedRange = {
    ...snapshot,
    reportedRange: {
      label: "04:00—未知",
      startTime: "04:00",
      endTime: null,
    },
  };

  assert.throws(() => createInitialDynamicState(mixedRange, "2026-07-18"));
});

test("new v2 case creation crosses one atomic RPC boundary", async () => {
  const calls: { readonly name: string; readonly args: Readonly<Record<string, unknown>> }[] = [];
  const savedId = await saveDynamicAssessment({
    async rpc(name, args) {
      calls.push({ name, args });
      return { data: caseId, error: null };
    },
  }, {
    userId: ownerId,
    assessment: {
      date: "1993-04-17",
      source: "period_only",
      period: "early_morning",
      location: { lat: 31.23, lon: 121.47, tz: 8 },
    },
    snapshot,
    questionnaire: null,
    candidateScan: null,
  }, new Date("2026-07-18T08:00:00.000Z"));

  assert.equal(savedId, caseId);
  assert.equal(calls.length, 1);
  assert.equal(calls[0]?.name, "create_birth_time_dynamic_case");
  assert.equal(calls[0]?.args.p_user_id, ownerId);
  assert.equal(JSON.stringify(calls[0]?.args.p_public_case).includes("candidateModel"), false);
  assert.deepEqual(calls[0]?.args.p_profile, {
    reportedBirthTime: null,
    birthTimeSource: "period_only",
    birthTimePeriod: "early_morning",
    birthTimeClue: null,
    uncertaintyBeforeMinutes: null,
    uncertaintyAfterMinutes: null,
    birthTimeStatus: "rectifying",
  });
  assert.deepEqual(calls[0]?.args.p_private_state, createInitialDynamicState(
    snapshot,
    "2026-07-18",
  ).privateState);
});

test("v2 load rejects a missing private row instead of regenerating", async () => {
  await assert.rejects(
    loadStoredRectificationCase(loadClient(null), ownerId, caseId),
    BirthTimeDynamicStateMissingError,
  );
});

test("v2 load rejects missing required public persistence fields", async () => {
  await assert.rejects(
    loadStoredRectificationCase(loadClient(privateRow, true), ownerId, caseId),
    BirthTimeJourneyStoreError,
  );
});

test("v2 load rejects incoherent public row and JSON turn versions", async () => {
  await assert.rejects(
    loadStoredRectificationCase(loadClient(privateRow, false, 8), ownerId, caseId),
    BirthTimeJourneyStoreError,
  );
});

test("v2 cases cannot fall through to legacy mutation paths", () => {
  assert.throws(() => assertLegacyJourneyMutation(dynamicCase()), {
    name: "GuidedJourneyLegacyMutationError",
  });
});

test("saveDynamicTurn persists a private snapshot and a privacy-safe public turn once", async () => {
  const fake = rpcPersistence();
  const updated = withPauseReceipt(dynamicCase(), actionId);

  const first = await fake.persistence.saveDynamicTurn(updated, 7, actionId);
  const replay = await fake.persistence.saveDynamicTurn(updated, 7, actionId);

  assert.equal(first.turnVersion, 8);
  assert.equal(replay.turnVersion, 8);
  assert.equal(replay.processedActionIds.filter((value) => value === actionId).length, 1);
  assert.equal(fake.calls[0]?.name, "save_birth_time_dynamic_turn");
  const publicTurn = JSON.stringify(fake.calls[0]?.args.p_public_turn_state);
  assert.equal(publicTurn.includes("partitionId"), false);
  assert.equal(publicTurn.includes("candidateScores"), false);
  assert.equal(publicTurn.includes("agentContext"), false);
  assert.deepEqual(fake.calls[0]?.args.p_private_state, {
    candidateModel: updated.candidateModel,
    currentChoiceQuestion: updated.currentChoiceQuestion,
    choiceAnswers: updated.choiceAnswers,
    choiceEvidence: updated.choiceEvidence,
    dynamicControl: updated.dynamicControl,
    agentContext: updated.agentContext,
  });
});

test("saveDynamicTurn reports a stale version for an unprocessed action", async () => {
  const fake = rpcPersistence();

  await assert.rejects(
    fake.persistence.saveDynamicTurn(dynamicCase(), 6, actionId),
    StaleJourneyTurnError,
  );
});

test("memory replay returns the stored advanced dynamic turn", async () => {
  const initial = dynamicCase();
  const memory = memoryStore(initial);
  const changed = withPauseReceipt({
    ...initial,
    agentContext: ["persisted context"],
  }, actionId);

  const saved = await memory.store.saveDynamicTurn(changed, 7, actionId);
  const replay = await memory.store.saveDynamicTurn(changed, 7, actionId.toUpperCase());

  assert.deepEqual(replay, saved);
  assert.equal(replay.turnVersion, 8);
  assert.deepEqual(replay.agentContext, ["persisted context"]);
  assert.deepEqual(replay.processedActionIds, [actionId]);
  assert.equal(memory.committedTurnWrites(), 1);
});

test("memory store replays seeded v2 receipts and executes legacy upgrades", async () => {
  const initial = dynamicCase();
  const seeded = savedPauseReceipt(initial, actionId);
  const dynamicMemory = memoryStore(seeded);
  const replay = await dynamicMemory.store.saveDynamicTurn(
    withPauseReceipt(initial, actionId), 7, actionId,
  );
  assert.equal(replay, seeded);

  const legacyMemory = memoryStore(legacyCase(true));
  const upgraded = await legacyMemory.store.upgradeLegacyActiveCase(legacyCase(true));
  assert.equal(upgraded.journeyProtocol, "dynamic-choice-v2");
  assert.equal(upgraded.dynamicTurnState.nextAction.kind, "generate_dynamic_question");
  assert.deepEqual(upgraded.answers, { q1: "A" });
});

test("legacy active upgrade preserves evidence and starts v2 without legacy fingerprints", async () => {
  let loaded: StoredRectificationCase = legacyCase(true);
  const rpcCalls: string[] = [];
  const persistence = createDynamicTurnPersistence({
    async rpc(name: string, args: Readonly<Record<string, unknown>>) {
      rpcCalls.push(name);
      const parsedPrivate = dynamicPrivateStateSchema.parse(args.p_private_state);
      const parsedTurn = dynamicJourneyTurnStateSchema.parse(args.p_public_turn_state);
      if (loaded.journeyProtocol === "dynamic-choice-v2") {
        throw new Error("legacy upgrade replayed through the RPC fake");
      }
      loaded = {
        ...loaded,
        journeyProtocol: "dynamic-choice-v2",
        turnVersion: loaded.turnVersion ?? 0,
        processedActionIds: loaded.processedActionIds ?? [],
        persistedProgress: loaded.persistedProgress ?? { adaptiveRound: 0, askedDomains: [] },
        dynamicTurnState: parsedTurn,
        turnState: null,
        evidenceDraft: null,
        ...parsedPrivate,
      };
      return { data: loaded.turnVersion, error: null };
    },
  }, async () => loaded, () => "2026-07-18");

  const upgraded = await persistence.upgradeLegacyActiveCase(loaded);

  assert.equal(upgraded.journeyProtocol, "dynamic-choice-v2");
  assert.deepEqual(upgraded.answers, { q1: "A" });
  assert.equal(upgraded.dynamicTurnState?.nextAction.kind, "generate_dynamic_question");
  assert.deepEqual(upgraded.dynamicControl?.questionFingerprints, []);
  assert.equal(upgraded.dynamicControl?.effectiveAnswerCount, 1);
  assert.deepEqual(rpcCalls, ["upgrade_birth_time_legacy_case"]);
});

test("terminal legacy cases remain byte-for-byte unchanged", async () => {
  const terminal = legacyCase(false);
  let rpcCalled = false;
  const persistence = createDynamicTurnPersistence({
    async rpc() {
      rpcCalled = true;
      return { data: null, error: null };
    },
  }, async () => terminal, () => "2026-07-18");

  const result = await persistence.upgradeLegacyActiveCase(terminal);

  assert.equal(result, terminal);
  assert.equal(rpcCalled, false);
});

test("dynamic persistence maps unknown RPC errors to a typed store error", async () => {
  const persistence = createDynamicTurnPersistence({
    async rpc() { return { data: null, error: { message: "database unavailable" } }; },
  }, async () => dynamicCase(), () => "2026-07-18");

  await assert.rejects(
    persistence.saveDynamicTurn(dynamicCase(), 7, actionId),
    BirthTimeJourneyStoreError,
  );
});
