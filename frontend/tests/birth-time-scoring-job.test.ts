import assert from "node:assert/strict";
import test from "node:test";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import { evidenceFingerprint } from "../src/lib/birth-time-scoring-job.ts";
import {
  existingCareerEvent,
  existingEducationEvent,
  guidedCase,
  journeyCaseId,
  lowCandidate,
  memoryStore,
  unusedJourneyEngine,
} from "./birth-time-journey-test-support.ts";
import {
  pendingScoringFlow,
  scoringTestUserId as userId,
} from "./birth-time-scoring-test-support.ts";

test("polling a pending job scores exactly once and replays completion", async () => {
  const flow = await pendingScoringFlow({ score: async () => lowCandidate });

  const first = await flow.service.pollScoringJob(
    userId,
    journeyCaseId,
    flow.jobId,
  );
  const replay = await flow.service.pollScoringJob(
    userId,
    journeyCaseId,
    flow.jobId,
  );

  assert.equal(flow.calls(), 1);
  assert.deepEqual(replay.nextAction, first.nextAction);
  assert.equal(flow.memory.scoringJobStatus(flow.jobId), "completed");
});

test("evidence fingerprint is canonical but changes with confirmed evidence", () => {
  const forward = evidenceFingerprint([existingEducationEvent, existingCareerEvent]);
  const reverse = evidenceFingerprint([existingCareerEvent, existingEducationEvent]);
  const changed = evidenceFingerprint([
    existingEducationEvent,
    { ...existingCareerEvent, date: "2020-07" },
  ]);

  assert.equal(reverse, forward);
  assert.notEqual(changed, forward);
});

test("concurrent polls allow only one engine call", async () => {
  const flow = await pendingScoringFlow({
    score: async () => {
      await Promise.resolve();
      return lowCandidate;
    },
  });

  const results = await Promise.all([
    flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId),
    flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId),
  ]);

  assert.equal(flow.calls(), 1);
  assert.equal(results.every((result) => result.nextAction.kind === "score_pending"
    || result.nextAction.kind === "ask_adaptive_evidence"), true);
});

test("owner, case, and evidence fingerprint are checked before scoring", async () => {
  const now = new Date("2026-07-18T00:00:00.000Z");
  const flow = await pendingScoringFlow({ score: async () => lowCandidate, now: () => now });
  const jobId = flow.jobId;

  await assert.rejects(flow.service.pollScoringJob("other-user", journeyCaseId, jobId));
  await assert.rejects(flow.service.pollScoringJob(userId, "2299894c-10a8-4b45-91d1-339007282c50", jobId));
  assert.equal(flow.calls(), 0);

  const createdScoringCase = flow.memory.createdScoringCase();
  flow.memory.replaceCase({
    ...createdScoringCase,
    lifeEvents: [existingEducationEvent, existingCareerEvent],
  });
  await assert.rejects(flow.service.pollScoringJob(userId, journeyCaseId, jobId));
  assert.equal(flow.calls(), 0);
});

test("a compatibility case-id projection is not accepted as a real job", async () => {
  const memory = memoryStore(guidedCase());
  let calls = 0;
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: {
      ...unusedJourneyEngine,
      async scoreEvents() {
        calls += 1;
        return lowCandidate;
      },
    },
  });

  await assert.rejects(service.pollScoringJob(userId, journeyCaseId, journeyCaseId));
  assert.equal(calls, 0);
});

test("failed scoring preserves evidence and retries the same job", async () => {
  let fail = true;
  const flow = await pendingScoringFlow({
    score: async () => {
      if (fail) throw new TypeError("offline");
      return lowCandidate;
    },
  });
  const jobId = flow.jobId;

  const failed = await flow.service.pollScoringJob(userId, journeyCaseId, jobId);
  assert.deepEqual(failed.nextAction, { kind: "retry_scoring", jobId });
  assert.equal(failed.lifeEvents.length, 3);
  assert.equal(failed.progress.adaptiveRound, 0);

  fail = false;
  const completed = await flow.service.pollScoringJob(userId, journeyCaseId, jobId);
  assert.equal(completed.nextAction.kind, "ask_adaptive_evidence");
  assert.equal(completed.progress.adaptiveRound, 1);
  assert.equal(completed.lifeEvents.length, 3);
  assert.equal(flow.calls(), 2);

  const replay = await flow.service.pollScoringJob(userId, journeyCaseId, jobId);
  assert.equal(replay.progress.adaptiveRound, 1);
  assert.equal(replay.turnVersion, 8);
  assert.equal(flow.memory.savedCase()?.persistedProgress?.adaptiveRound, 1);
  assert.equal(flow.memory.savedCase()?.turnVersion, 8);
  assert.equal(flow.calls(), 2);
});
