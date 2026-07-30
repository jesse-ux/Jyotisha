import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";

import { createRectificationV4CaseService } from "../src/lib/rectification-v4/case-service.ts";
import type { CalculationSpec, CandidateMinute } from "../src/lib/rectification-v4/contracts.ts";
import { createRectificationV4MemoryStore } from "../src/lib/rectification-v4/memory-store.ts";
import { createRectificationV4Worker } from "../src/lib/rectification-v4/worker.ts";
import { passingVedAstroValidation, v5EngineResult, withV5Mode } from "./rectification-v5-test-support.ts";

const now = () => new Date("2026-07-26T08:00:00.000Z");
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

async function answerAndRun(
  service: ReturnType<typeof createRectificationV4CaseService>,
  worker: ReturnType<typeof createRectificationV4Worker>,
  userId: string,
  caseId: string,
  version: number,
  answer: string,
) {
  const queued = await service.answer({ userId, caseId, actionId: randomUUID(), expectedCaseVersion: version, answer });
  assert.ok(queued?.job);
  assert.equal(await worker.runOnce(), true);
  const loaded = await service.loadCase(userId, caseId);
  assert.ok(loaded);
  return loaded;
}

test("V5 golden replay persists the full artifact chain, returns ranges only, and never mutates the profile minute", async () => withV5Mode("v5_agent", async () => {
  const profile = { active_birth_time: "05:00:00" };
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now });
  const candidates: readonly CandidateMinute[] = [
    { time: "05:13", score: 100, supportingEventIds: [], conflictingEventIds: [] },
    { time: "05:14", score: 99, supportingEventIds: [], conflictingEventIds: [] },
    { time: "05:15", score: 98, supportingEventIds: [], conflictingEventIds: [] },
    { time: "05:16", score: 60, supportingEventIds: [], conflictingEventIds: [] },
    { time: "05:17", score: 97.8, supportingEventIds: [], conflictingEventIds: [] },
    { time: "05:18", score: 97.7, supportingEventIds: [], conflictingEventIds: [] },
    { time: "05:19", score: 97.6, supportingEventIds: [], conflictingEventIds: [] },
  ];
  const worker = createRectificationV4Worker({
    store,
    now,
    engine: {
      async score({ calculationSpec, events }) {
        const ids = events.map((event) => event.eventId);
        return v5EngineResult(calculationSpec, events, candidates.map((candidate) => ({
          ...candidate,
          supportingEventIds: candidate.score >= 97 ? ids : [],
          conflictingEventIds: candidate.score < 97 ? ids : [],
        })));
      },
      async validateWithVedAstro({ candidateTimes }) {
        return passingVedAstroValidation(candidateTimes);
      },
    },
  });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  assert.equal(created.case.deploymentMode, "v5_agent");

  let loaded = await answerAndRun(service, worker, userId, created.case.id, created.case.version, "2015年7月高中毕业后复读一年，2016年6月再次高中毕业");
  assert.deepEqual(loaded.events.map((event) => [event.dateRange.start, event.dateRange.end]), [
    ["2015-07-01", "2015-07-31"],
    ["2016-06-01", "2016-06-30"],
  ]);
  assert.equal(loaded.case.currentQuestion?.targetEventId, null, "month precision should move to a new dated event");
  loaded = await answerAndRun(
    service,
    worker,
    userId,
    created.case.id,
    loaded.case.version,
    "2018年8月搬家到北京；2019年3月入职新公司；2020年5月开始一段恋爱关系",
  );

  const snapshot = loaded.case.latestSnapshot;
  assert.ok(snapshot);
  assert.equal(snapshot.canConfirmExactMinute, false);
  assert.equal(snapshot.canAcceptRange, true);
  assert.deepEqual(snapshot.clusters.map((cluster) => [cluster.startTime, cluster.endTime]), [["05:13", "05:15"], ["05:17", "05:19"]]);
  assert.equal(snapshot.clusters[0]?.representativeTime, "05:13");
  assert.equal(loaded.case.acceptedRange, null);
  assert.ok(loaded.case.featureSnapshotId);
  assert.ok(loaded.case.latestDiagnosticsId);
  assert.equal(store.featureSnapshots.size, 1);
  assert.equal(store.diagnostics.size, 1);
  assert.equal(store.agentRuns.size, 2);
  assert.equal(store.publicMessages.size, 2);
  assert.equal(store.validatedDecisions.size, 2);
  const finalRun = [...store.agentRuns.values()].at(-1);
  assert.equal(finalRun?.validatedDecision.decision.action, "offer_candidate_range");
  assert.equal(finalRun?.inputTokenCount, null);
  assert.equal(finalRun?.outputTokenCount, null);

  const accepted = await service.acceptRange({
    userId,
    caseId: created.case.id,
    actionId: randomUUID(),
    expectedCaseVersion: loaded.case.version,
    startTime: "05:13",
    endTime: "05:15",
  });
  assert.deepEqual(accepted?.case.acceptedRange, { start: "05:13", end: "05:15" });
  assert.equal(accepted?.case.latestSnapshot?.canConfirmExactMinute, false);
  assert.equal(profile.active_birth_time, "05:00:00");
}));
