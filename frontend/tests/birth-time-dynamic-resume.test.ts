import assert from "node:assert/strict";
import test from "node:test";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import {
  caseId,
  dynamicCase,
  legacyCase,
  ownerId,
} from "./birth-time-dynamic-persistence-fixture.ts";
import { memoryStore } from "./birth-time-journey-memory-store.ts";
import { unusedJourneyEngine } from "./birth-time-journey-test-support.ts";

test("v2 resume returns the stored dynamic turn without legacy scoring writes", async () => {
  const stored = {
    ...dynamicCase(),
    scoring: {
      answeredCount: 5,
      candidateClusterRankings: [],
      nextRound: null,
      nextRoundQuestions: [],
      raw: {},
    },
  };
  const memory = memoryStore(stored);
  const service = createBirthTimeJourneyService({ store: memory.store, engine: unusedJourneyEngine });

  const resumed = await service.resume(ownerId, caseId);

  assert.equal(resumed.journeyProtocol, "dynamic-choice-v2");
  assert.deepEqual({
    journeyProtocol: resumed.journeyProtocol,
    turnVersion: resumed.turnVersion,
    nextAction: resumed.nextAction,
    progress: resumed.progress,
    permissions: resumed.permissions,
  }, stored.dynamicTurnState);
  assert.equal(memory.legacyWrites(), 0);
});

test("resume upgrades an unfinished legacy case into the dynamic click-first flow", async () => {
  const stored = legacyCase(true);
  const memory = memoryStore(stored);
  const service = createBirthTimeJourneyService({ store: memory.store, engine: unusedJourneyEngine });

  const resumed = await service.resume(ownerId, caseId);

  assert.equal(resumed.journeyProtocol, "dynamic-choice-v2");
  assert.equal(resumed.nextAction.kind, "generate_dynamic_question");
  assert.equal(resumed.turnVersion, stored.turnVersion);
  assert.deepEqual(memory.savedCase()?.lifeEvents, stored.lifeEvents);
  assert.deepEqual(resumed.lifeEvents, []);
  assert.equal(memory.savedCase()?.journeyProtocol, "dynamic-choice-v2");
  assert.equal(memory.legacyWrites(), 0);
});
