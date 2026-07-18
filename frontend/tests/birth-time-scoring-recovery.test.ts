import assert from "node:assert/strict";
import test from "node:test";
import { candidateResultSchema } from "../src/lib/birth-time-evidence.ts";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import {
  confirmActionId,
  draftActionId,
  existingCareerEvent,
  existingEducationEvent,
  guidedCase,
  journeyCaseId,
  lowCandidate,
  memoryStore,
  secondActionId,
  thirdActionId,
  unusedJourneyEngine,
} from "./birth-time-journey-test-support.ts";
import {
  pendingScoringFlow,
  scoringTestUserId as userId,
} from "./birth-time-scoring-test-support.ts";

const mediumCandidate = candidateResultSchema.parse({
  ...lowCandidate,
  resultId: "345087cc-7e7f-4b37-90e5-f0c0a6e5b7a7",
  confidence: "medium",
  winningSegment: {
    startTime: "05:18",
    endTime: "05:24",
    representativeTime: "05:21",
    widthMinutes: 7,
  },
});

test("a completion write failure is reclaimed only after the processing lease", async () => {
  let now = new Date("2026-07-18T00:00:00.000Z");
  let failCompletion = true;
  const flow = await pendingScoringFlow({
    score: async () => lowCandidate,
    now: () => now,
    transformStore: (store) => ({
      ...store,
      async completeScoringJob(...args) {
        if (failCompletion) throw new TypeError("database unavailable");
        return store.completeScoringJob(...args);
      },
    }),
  });

  await assert.rejects(flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId));
  const freshLease = await flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId);
  assert.equal(freshLease.nextAction.kind, "score_pending");
  assert.equal(flow.calls(), 1);

  failCompletion = false;
  now = new Date("2026-07-18T00:01:01.000Z");
  const recovered = await flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId);
  assert.equal(recovered.nextAction.kind, "ask_adaptive_evidence");
  assert.equal(flow.calls(), 2);
});

test("expired pending and failed jobs renew while completed jobs replay", async () => {
  let now = new Date("2026-07-18T00:00:00.000Z");
  let fail = false;
  const pending = await pendingScoringFlow({
    now: () => now,
    score: async () => {
      if (fail) throw new TypeError("offline");
      return lowCandidate;
    },
  });
  now = new Date("2026-07-18T01:00:00.000Z");
  const completed = await pending.service.pollScoringJob(userId, journeyCaseId, pending.jobId);
  const replay = await pending.service.pollScoringJob(userId, journeyCaseId, pending.jobId);
  assert.deepEqual(replay.nextAction, completed.nextAction);
  assert.equal(pending.calls(), 1);

  now = new Date("2026-07-18T00:00:00.000Z");
  fail = true;
  const failed = await pendingScoringFlow({
    now: () => now,
    score: async () => {
      if (fail) throw new TypeError("offline");
      return lowCandidate;
    },
  });
  await failed.service.pollScoringJob(userId, journeyCaseId, failed.jobId);
  fail = false;
  now = new Date("2026-07-18T01:00:00.000Z");
  const retried = await failed.service.pollScoringJob(userId, journeyCaseId, failed.jobId);
  assert.equal(retried.nextAction.kind, "ask_adaptive_evidence");
  assert.equal(retried.lifeEvents.length, 3);
  assert.equal(failed.calls(), 2);
});

test("a completed medium job replays after its candidate range is saved", async () => {
  const flow = await pendingScoringFlow({ score: async () => mediumCandidate });
  const completed = await flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId);
  if (completed.nextAction.kind !== "present_medium_result") {
    throw new TypeError("test setup did not produce a medium result");
  }
  const saved = await flow.service.saveGuidedCandidate({
    userId,
    caseId: journeyCaseId,
    actionId: secondActionId,
    expectedVersion: completed.turnVersion,
    resultId: mediumCandidate.resultId,
  });

  assert.equal(saved.nextAction.kind, "candidate_saved");
  const replay = await flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId);
  assert.deepEqual(replay.nextAction, saved.nextAction);
  assert.equal(flow.calls(), 1);
});

test("concurrent duplicate confirmation replays one job and one evidence event", async () => {
  const memory = memoryStore(guidedCase({
    version: 4,
    domain: "relationship",
    askedDomains: ["education", "career"],
    lifeEvents: [existingEducationEvent, existingCareerEvent],
  }));
  const service = createBirthTimeJourneyService({ store: memory.store, engine: unusedJourneyEngine });
  const proposed = await service.proposeEvidenceDraft(
    userId, journeyCaseId, draftActionId, 4,
    { domain: "relationship", precision: "year", date: "2021" },
  );
  const confirm = () => service.confirmEvidenceDraft(
    userId, journeyCaseId, confirmActionId, proposed.turnVersion,
    proposed.evidenceDraft?.draftId ?? "",
  );

  const [first, duplicate] = await Promise.all([confirm(), confirm()]);

  assert.deepEqual(duplicate.nextAction, first.nextAction);
  assert.equal(duplicate.lifeEvents.length, 3);
  assert.equal(memory.scoringJobCount(), 1);
});

test("algorithm mismatches never mutate pending, processing, or completed jobs", async () => {
  const pending = await pendingScoringFlow({ score: async () => lowCandidate });
  pending.memory.setScoringJobAlgorithm(pending.jobId, "wrong-version");
  await assert.rejects(pending.service.pollScoringJob(userId, journeyCaseId, pending.jobId));
  assert.equal(pending.memory.scoringJobStatus(pending.jobId), "pending");
  assert.equal(pending.calls(), 0);

  const processing = await pendingScoringFlow({
    score: async () => lowCandidate,
    transformStore: (store) => ({
      ...store,
      async completeScoringJob() { throw new TypeError("offline"); },
    }),
  });
  await assert.rejects(processing.service.pollScoringJob(userId, journeyCaseId, processing.jobId));
  processing.memory.setScoringJobAlgorithm(processing.jobId, "wrong-version");
  await assert.rejects(processing.service.pollScoringJob(userId, journeyCaseId, processing.jobId));
  assert.equal(processing.memory.scoringJobStatus(processing.jobId), "processing");
  assert.equal(processing.calls(), 1);

  const completed = await pendingScoringFlow({ score: async () => lowCandidate });
  await completed.service.pollScoringJob(userId, journeyCaseId, completed.jobId);
  completed.memory.setScoringJobAlgorithm(completed.jobId, "wrong-version");
  await assert.rejects(completed.service.pollScoringJob(userId, journeyCaseId, completed.jobId));
  assert.equal(completed.memory.scoringJobStatus(completed.jobId), "completed");
  assert.equal(completed.calls(), 1);
});

test("completed replay rejects inconsistent persisted candidate state", async () => {
  const flow = await pendingScoringFlow({ score: async () => lowCandidate });
  await flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId);
  const stored = flow.memory.savedCase();
  if (!stored) throw new TypeError("missing completed test case");
  flow.memory.replaceCase({ ...stored, candidateResult: null });

  await assert.rejects(flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId));
  assert.equal(flow.memory.scoringJobStatus(flow.jobId), "completed");
  assert.equal(flow.calls(), 1);
});

test("old completed polls replay review but cannot replace the next active job", async () => {
  let scoreCall = 0;
  const flow = await pendingScoringFlow({
    score: async () => {
      scoreCall += 1;
      return scoreCall === 1
        ? lowCandidate
        : { ...lowCandidate, eventCount: 4, domainCount: 4 };
    },
  });
  const scored = await flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId);
  if (scored.nextAction.kind !== "ask_adaptive_evidence") {
    throw new TypeError("missing adaptive question");
  }
  const draft = await flow.service.proposeEvidenceDraft(
    userId,
    journeyCaseId,
    secondActionId,
    scored.turnVersion,
    { domain: scored.nextAction.question.domain, precision: "year", date: "2022" },
  );

  const oldReplay = await flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId);
  assert.equal(oldReplay.nextAction.kind, "review_evidence_draft");

  const next = await flow.service.confirmEvidenceDraft(
    userId,
    journeyCaseId,
    thirdActionId,
    draft.turnVersion,
    draft.evidenceDraft?.draftId ?? "",
  );
  if (next.nextAction.kind !== "score_pending") throw new TypeError("missing next job");
  await assert.rejects(flow.service.pollScoringJob(userId, journeyCaseId, flow.jobId));
  const nextResult = await flow.service.pollScoringJob(
    userId,
    journeyCaseId,
    next.nextAction.jobId,
  );

  assert.equal(nextResult.progress.adaptiveRound, 2);
  assert.equal(flow.calls(), 2);
});
