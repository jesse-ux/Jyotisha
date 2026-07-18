import assert from "node:assert/strict";
import test from "node:test";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import {
  caseId,
  dynamicCase,
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
