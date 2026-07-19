import assert from "node:assert/strict";
import test from "node:test";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import {
  dynamicChoiceScoringAlgorithmVersion,
  dynamicEvidenceFingerprint,
} from "../src/lib/birth-time-scoring-job.ts";
import { dynamicCase, ownerId, persistedQuestion } from "./birth-time-dynamic-persistence-fixture.ts";
import { dynamicJobStore } from "./birth-time-dynamic-job-memory-store.ts";
import { memoryStore } from "./birth-time-journey-memory-store.ts";

test("dynamic processing claims are reclaimed only after the lease", async () => {
  const memory = memoryStore(dynamicCase());
  const jobs = dynamicJobStore(memory.store, () => {
    const current = memory.savedCase();
    return current?.journeyProtocol === "dynamic-choice-v2" ? current : null;
  });
  const service = createBirthTimeJourneyService({
    store: jobs.store,
    now: () => new Date("2026-07-18T08:00:00.000Z"),
    engine: {
      async scan() { throw new Error("unexpected scan"); },
      async score() { throw new Error("unexpected score"); },
      async scoreEvents() { throw new Error("unexpected event score"); },
    },
  });
  const pending = await service.answerDynamicChoice(ownerId, {
    caseId: dynamicCase().id,
    actionId: "9a921af8-ddcc-4d20-b4c8-fbbb3e6a814d",
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: persistedQuestion.options[0].optionId,
  });
  if (pending.nextAction.kind !== "score_pending") throw new Error("expected pending score");
  const stored = memory.savedCase();
  if (!stored || stored.journeyProtocol !== "dynamic-choice-v2") throw new Error("missing v2 case");
  const claim = jobs.store.claimDynamicScoringJob;
  if (!claim) throw new Error("missing dynamic claim");
  const identity = {
    userId: ownerId,
    caseId: stored.id,
    jobId: pending.nextAction.jobId,
    evidenceFingerprint: dynamicEvidenceFingerprint(stored.choiceEvidence),
    algorithmVersion: dynamicChoiceScoringAlgorithmVersion,
  } as const;

  assert.equal((await claim({ ...identity, now: "2026-07-18T08:00:00.000Z" })).kind, "claimed");
  assert.equal((await claim({ ...identity, now: "2026-07-18T08:00:59.999Z" })).kind, "processing");
  assert.equal((await claim({ ...identity, now: "2026-07-18T08:01:00.000Z" })).kind, "claimed");
});
