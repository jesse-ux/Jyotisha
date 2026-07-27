import assert from "node:assert/strict";
import test from "node:test";
import { randomUUID } from "node:crypto";
import { createRectificationV4CaseService } from "../src/lib/rectification-v4/case-service.ts";
import type { CalculationSpec } from "../src/lib/rectification-v4/contracts.ts";
import { calculationSpecHash } from "../src/lib/rectification-v4/fingerprints.ts";
import { createRectificationV4MemoryStore } from "../src/lib/rectification-v4/memory-store.ts";
import { createRectificationV4Worker } from "../src/lib/rectification-v4/worker.ts";

const fixedNow = () => new Date("2026-07-26T12:00:00.000Z");
const spec: CalculationSpec = {
  version: "rectification-calculation-spec-v4",
  birthDate: "1997-08-08",
  candidateRange: { start: "04:30", end: "05:30" },
  latitude: 36.419,
  longitude: 114.213,
  timezoneOffsetHours: 8,
  ayanamsa: "lahiri",
  nodeMode: "mean",
  minuteStep: 1,
};



test("same calculation spec resumes the unfinished case", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const first = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const resumed = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: { ...spec } });

  assert.equal(resumed.case.id, first.case.id);
  assert.equal(store.cases.size, 1);
});

test("changed calculation spec atomically abandons the old case and stales its job", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const first = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const queued = await service.answer({
    userId, caseId: first.case.id, actionId: randomUUID(), expectedCaseVersion: 0, answer: "2016年9月上大学",
  });
  assert.ok(queued?.job);

  const replacement = await service.createCase({
    userId,
    actionId: randomUUID(),
    calculationSpec: { ...spec, candidateRange: { start: "04:45", end: "05:30" } },
  });

  assert.notEqual(replacement.case.id, first.case.id);
  assert.equal(store.cases.get(first.case.id)?.status, "abandoned");
  assert.equal(store.cases.get(first.case.id)?.currentQuestion, null);
  assert.equal(store.jobs.get(queued.job.id)?.status, "stale");
  assert.equal((await service.loadActive(userId))?.case.id, replacement.case.id);
});

test("an accepted range closes the active lifecycle and allows a new case", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const first = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  await store.transitionCase({
    userId,
    caseId: first.case.id,
    actionId: randomUUID(),
    expectedCaseVersion: first.case.version,
    status: "range_ready",
    phase: "complete",
    acceptedRange: { start: "05:13", end: "05:15" },
    now: fixedNow().toISOString(),
  });

  assert.equal(await service.loadActive(userId), null);
  const next = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  assert.notEqual(next.case.id, first.case.id);
  assert.equal(store.cases.size, 2);
});

test("answer is durably queued and poll remains read only", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  assert.equal(created.case.status, "awaiting_answer");
  assert.equal(created.case.currentQuestion?.domain, "education");
  const queued = await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2015年7月高中毕业后复读一年，2016年6月再次毕业",
  });
  assert.equal(queued?.case.status, "processing");
  assert.equal(queued?.job?.status, "pending");
  const before = JSON.stringify([...store.jobs.values()]);
  const polled = await service.loadCase(userId, created.case.id);
  assert.equal(polled?.job, null);
  assert.equal(JSON.stringify([...store.jobs.values()]), before);
});

test("worker extracts dated events, keeps one question and never confirms an exact minute", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const queued = await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2015年7月高中毕业后复读一年，2016年6月再次毕业",
  });
  const worker = createRectificationV4Worker({
    store,
    now: fixedNow,
    engine: { async score() { throw new Error("engine must not run before enough events"); } },
  });
  assert.equal(await worker.runOnce(), true);
  const done = await service.loadCase(userId, created.case.id);
  assert.equal(done?.case.status, "awaiting_answer");
  assert.equal(done?.events.length, 2);
  assert.equal(done?.case.currentQuestion?.domain, "relocation");
  assert.equal(done?.case.latestSnapshot, null);
  assert.equal(queued?.job?.status, "pending");
});

test("completed job rejects stale case or calculation hashes", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  await service.answer({ userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0, answer: "2016年9月上大学" });
  const claimed = await store.claimNextJob("worker", fixedNow().toISOString());
  assert.ok(claimed);
  await assert.rejects(() => store.completeJob({
    workerId: "worker", jobId: claimed.job.id, expectedCaseVersion: claimed.case.version,
    inputEvidenceSetHash: "0".repeat(64), outputEvidenceSetHash: claimed.case.evidenceSetHash,
    calculationSpecHash: claimed.case.calculationSpecHash, newEventRevisions: [], snapshot: null,
    nextQuestion: claimed.case.currentQuestion, status: "awaiting_answer", phase: "collecting_evidence",
  }, fixedNow().toISOString()), /stale_job/);
});

test("worker moves from domain coverage to targeted date refinement without a null-question dead state", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const scoreableCounts: number[] = [];
  const worker = createRectificationV4Worker({
    store,
    now: fixedNow,
    engine: {
      async score({ calculationSpec, events }) {
        scoreableCounts.push(events.length);
        const ids = events.map((event) => event.eventId);
        return {
          resultId: randomUUID(),
          calculationSpecHash: calculationSpecHash(calculationSpec),
          candidates: [
            { time: "05:13", score: 100, supportingEventIds: ids, conflictingEventIds: [] },
            { time: "05:14", score: 99, supportingEventIds: ids, conflictingEventIds: [] },
            { time: "05:15", score: 98, supportingEventIds: ids, conflictingEventIds: [] },
          ],
          robustness: {
            neighborSupportMinutes: 3,
            leaveOneOutRetentionRate: 1,
            dateSensitivityRetentionRate: 0.5,
          },
          missingLayers: [],
        };
      },
    },
  });

  let current = created;
  for (const answer of [
    "2016年高中毕业",
    "2018年8月搬家到北京",
    "2020年5月开始恋爱",
    "2021年3月入职公司",
    "2022年4月收入明显变化",
    "2023年5月住院",
    "2024年6月家庭发生变化",
  ]) {
    const queued = await service.answer({
      userId,
      caseId: created.case.id,
      actionId: randomUUID(),
      expectedCaseVersion: current.case.version,
      answer,
    });
    assert.ok(queued?.job);
    assert.equal(await worker.runOnce(), true);
    current = (await service.loadCase(userId, created.case.id))!;
    assert.equal(current.case.status === "awaiting_answer" && current.case.currentQuestion === null, false);
  }

  const targetEventId = current.case.currentQuestion?.targetEventId;
  assert.ok(targetEventId);
  assert.equal(current.case.status, "awaiting_answer");
  assert.equal(current.case.currentQuestion?.prompt.includes("更具体的日期"), true);

  const queued = await service.answer({
    userId,
    caseId: created.case.id,
    actionId: randomUUID(),
    expectedCaseVersion: current.case.version,
    answer: "2016年6月8日",
  });
  assert.ok(queued?.job);
  assert.equal(await worker.runOnce(), true);
  current = (await service.loadCase(userId, created.case.id))!;

  const targetedRevisions = current.events.filter((event) => event.eventId === targetEventId);
  assert.deepEqual(targetedRevisions.map((event) => event.revision), [1, 2]);
  assert.equal(targetedRevisions[1]?.dateRange.precision, "day");
  assert.equal(scoreableCounts.at(-1), 6);
  assert.equal(current.case.status === "awaiting_answer" && current.case.currentQuestion === null, false);
  assert.notEqual(current.case.currentQuestion?.targetEventId, targetEventId);
});
