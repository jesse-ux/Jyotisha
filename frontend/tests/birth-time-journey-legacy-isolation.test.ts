import assert from "node:assert/strict";
import test from "node:test";
import { candidateResultSchema } from "../src/lib/birth-time-journey.ts";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import {
  existingCareerEvent,
  guidedCase,
  journeyCaseId,
  memoryStore,
  unusedJourneyEngine,
} from "./birth-time-journey-test-support.ts";

const highCandidate = candidateResultSchema.parse({
  resultId: "f8eb3bc5-80eb-40fc-b937-e62ea37c3236",
  confidence: "high",
  canApply: true,
  winningSegment: {
    startTime: "14:22",
    endTime: "14:26",
    representativeTime: "14:24",
    widthMinutes: 5,
  },
  eventCount: 4,
  domainCount: 3,
  topScore: 18,
  secondScore: 8,
  marginPercent: 55,
  reasons: ["One segment has consistent evidence."],
  evidence: [],
  algorithmVersion: "birth-time-event-scoring-v1",
});

function rejectsLegacyMutation(error: unknown): boolean {
  return error instanceof Error && error.name === "GuidedJourneyLegacyMutationError";
}

test("guided turns reject legacy answer mutation before scoring or writing", async () => {
  const memory = memoryStore(guidedCase());
  let scoreCalls = 0;
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: {
      ...unusedJourneyEngine,
      async score() {
        scoreCalls += 1;
        throw new Error("must not score");
      },
    },
  });

  await assert.rejects(
    service.answerQuestion("user-1", journeyCaseId, "legacy-question", "A"),
    rejectsLegacyMutation,
  );

  assert.equal(scoreCalls, 0);
  assert.equal(memory.legacyWrites(), 0);
});

test("guided turns reject legacy event submission before scoring or writing", async () => {
  const memory = memoryStore(guidedCase());
  let scoreCalls = 0;
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: {
      ...unusedJourneyEngine,
      async scoreEvents() {
        scoreCalls += 1;
        throw new Error("must not score");
      },
    },
  });

  await assert.rejects(
    service.submitLifeEvents("user-1", journeyCaseId, [existingCareerEvent]),
    rejectsLegacyMutation,
  );

  assert.equal(scoreCalls, 0);
  assert.equal(memory.legacyWrites(), 0);
});

test("guided turns reject legacy candidate saves without writing", async () => {
  const memory = memoryStore(guidedCase({ candidateResult: highCandidate }));
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: unusedJourneyEngine,
  });

  await assert.rejects(
    service.saveCandidate("user-1", journeyCaseId, highCandidate.resultId),
    rejectsLegacyMutation,
  );

  assert.equal(memory.legacyWrites(), 0);
});

test("guided turns reject legacy candidate confirmation without writing", async () => {
  const stored = guidedCase({ candidateResult: highCandidate });
  const confirming = {
    ...stored,
    snapshot: {
      ...stored.snapshot,
      state: "confirming",
      assistantIntent: "confirm_candidate_time",
      input: "candidate_confirmation",
      confidence: "high",
      canApply: true,
    },
  } as const;
  const memory = memoryStore(confirming);
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: unusedJourneyEngine,
  });

  await assert.rejects(
    service.confirmCandidate(
      "user-1",
      journeyCaseId,
      highCandidate.resultId,
      highCandidate.winningSegment?.representativeTime ?? "",
    ),
    rejectsLegacyMutation,
  );

  assert.equal(memory.legacyWrites(), 0);
});
