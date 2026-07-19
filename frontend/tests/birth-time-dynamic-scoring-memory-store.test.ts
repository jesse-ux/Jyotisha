import assert from "node:assert/strict";
import test from "node:test";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import { dynamicCase } from "./birth-time-dynamic-persistence-fixture.ts";
import { memoryStore } from "./birth-time-journey-memory-store.ts";
import { lowCandidate } from "./birth-time-journey-test-support.ts";

const jobA = "8c9d09e8-91b6-4335-b891-122f205a050c";
const jobB = "dc6f3fdc-b679-4878-a3f4-1037fd1ababb";
const baseCommand = {
  expectedVersion: 7,
  jobId: jobA,
  evidenceFingerprint: "evidence-fingerprint",
  algorithmVersion: "birth-time-event-scoring-v1",
};

function completingCase() {
  const stored = dynamicCase();
  return { ...stored, candidateResult: lowCandidate };
}

test("shared memory store replays only the identical scoring completion", async () => {
  const value = completingCase();
  const memory = memoryStore(dynamicCase());
  const first = await memory.store.completeDynamicScoringJob(value, baseCommand);

  assert.equal(await memory.store.completeDynamicScoringJob(value, baseCommand), first);
  for (const command of [
    { ...baseCommand, evidenceFingerprint: "changed" },
    { ...baseCommand, algorithmVersion: "birth-time-event-scoring-v2" },
  ]) {
    await assert.rejects(
      memory.store.completeDynamicScoringJob(value, command),
      StaleJourneyTurnError,
    );
  }
  await assert.rejects(
    memory.store.completeDynamicScoringJob({
      ...value,
      candidateResult: { ...lowCandidate, topScore: 9 },
    }, baseCommand),
    StaleJourneyTurnError,
  );
  await assert.rejects(
    memory.store.failDynamicScoringJob(dynamicCase(), {
      ...baseCommand,
      jobId: jobB,
      failureCode: "engine_unavailable",
    }),
    StaleJourneyTurnError,
  );
});

test("shared memory store replays only the identical scoring failure", async () => {
  const value = dynamicCase();
  const memory = memoryStore(dynamicCase());
  const command = { ...baseCommand, failureCode: "engine_unavailable" };
  const first = await memory.store.failDynamicScoringJob(value, command);

  assert.equal(await memory.store.failDynamicScoringJob(value, command), first);
  await assert.rejects(
    memory.store.failDynamicScoringJob(value, { ...command, failureCode: "timeout" }),
    StaleJourneyTurnError,
  );
});
