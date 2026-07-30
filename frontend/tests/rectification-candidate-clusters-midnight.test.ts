import assert from "node:assert/strict";
import test from "node:test";
import { buildCandidateClusters } from "../src/lib/rectification-v4/candidate-clusters.ts";

const candidate = (time: string, score: number) => ({
  time,
  score,
  supportingEventIds: [],
  conflictingEventIds: [],
});

test("candidate clusters join midnight neighbors without treating representativeTime as a confirmed minute", () => {
  const clusters = buildCandidateClusters([
    candidate("23:59", 100),
    candidate("12:00", 98),
    candidate("00:00", 99),
  ]);

  assert.deepEqual(clusters, [
    {
      rank: 1,
      startTime: "23:59",
      endTime: "00:00",
      representativeTime: "23:59",
      widthMinutes: 2,
      peakScore: 100,
      scoreMass: 199,
    },
    {
      rank: 2,
      startTime: "12:00",
      endTime: "12:00",
      representativeTime: "12:00",
      widthMinutes: 1,
      peakScore: 98,
      scoreMass: 98,
    },
  ]);
});

test("candidate clusters keep ordinary daytime gaps separate", () => {
  assert.deepEqual(
    buildCandidateClusters([
      candidate("05:13", 100),
      candidate("05:14", 99),
      candidate("05:16", 98),
    ]).map(({ startTime, endTime, widthMinutes }) => ({ startTime, endTime, widthMinutes })),
    [
      { startTime: "05:13", endTime: "05:14", widthMinutes: 2 },
      { startTime: "05:16", endTime: "05:16", widthMinutes: 1 },
    ],
  );
});
