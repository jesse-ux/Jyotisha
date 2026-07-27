import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";

import { createRectificationV4CaseService } from "../src/lib/rectification-v4/case-service.ts";
import type { CalculationSpec } from "../src/lib/rectification-v4/contracts.ts";
import { calculationSpecHash } from "../src/lib/rectification-v4/fingerprints.ts";
import { createRectificationV4MemoryStore } from "../src/lib/rectification-v4/memory-store.ts";
import { createRectificationV4Worker } from "../src/lib/rectification-v4/worker.ts";

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
  const queued = await service.answer({
    userId,
    caseId,
    actionId: randomUUID(),
    expectedCaseVersion: version,
    answer,
  });
  assert.ok(queued?.job);
  assert.equal(await worker.runOnce(), true);
  const loaded = await service.loadCase(userId, caseId);
  assert.ok(loaded);
  return loaded;
}

test("fixture replay returns ranges only and never mutates the profile birth minute", async () => {
  const profile = { active_birth_time: "05:00:00" };
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now });
  const worker = createRectificationV4Worker({
    store,
    now,
    questionAuthor: async () => ({
      id: randomUUID(),
      domain: "other",
      targetEventId: null,
      prompt: "请继续讲另一件时间比较清楚的人生变化。",
      recallCost: "low",
      reason: "Replay keeps narration open instead of depending on a fixed domain order.",
    }),
    engine: {
      async score({ calculationSpec, events }) {
        const ids = events.map((event) => event.eventId);
        return {
          resultId: randomUUID(),
          calculationSpecHash: calculationSpecHash(calculationSpec),
          candidates: [
            { time: "05:13", score: 100, supportingEventIds: ids, conflictingEventIds: [] },
            { time: "05:14", score: 99, supportingEventIds: ids, conflictingEventIds: [] },
            { time: "05:15", score: 98, supportingEventIds: ids, conflictingEventIds: [] },
            { time: "05:16", score: 60, supportingEventIds: [], conflictingEventIds: ids },
            { time: "05:17", score: 97.8, supportingEventIds: ids, conflictingEventIds: [] },
            { time: "05:18", score: 97.7, supportingEventIds: ids, conflictingEventIds: [] },
            { time: "05:19", score: 97.6, supportingEventIds: ids, conflictingEventIds: [] },
          ],
          robustness: {
            neighborSupportMinutes: 3,
            leaveOneOutRetentionRate: 1,
            dateSensitivityRetentionRate: 0.9,
          },
          missingLayers: [],
        };
      },
    },
  });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  let loaded = await answerAndRun(
    service,
    worker,
    userId,
    created.case.id,
    created.case.version,
    "2015年高中毕业后复读一年，2016年再次高中毕业",
  );
  assert.deepEqual(loaded.events.map((event) => [event.dateRange.start, event.dateRange.end]), [
    ["2015-01-01", "2015-12-31"],
    ["2016-01-01", "2016-12-31"],
  ]);
  loaded = await answerAndRun(service, worker, userId, created.case.id, loaded.case.version, "2018年8月搬家到北京");
  loaded = await answerAndRun(
    service,
    worker,
    userId,
    created.case.id,
    loaded.case.version,
    "2020年5月开始恋爱，2022年3月分手",
  );
  const snapshot = loaded.case.latestSnapshot;
  assert.ok(snapshot);
  assert.equal(snapshot.canConfirmExactMinute, false);
  assert.equal(snapshot.canAcceptRange, true);
  assert.deepEqual(snapshot.clusters.map((cluster) => [cluster.startTime, cluster.endTime]), [
    ["05:13", "05:15"],
    ["05:17", "05:19"],
  ]);
  assert.equal(snapshot.clusters[0]?.representativeTime, "05:13");
  assert.equal(loaded.case.acceptedRange, null);

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
});
