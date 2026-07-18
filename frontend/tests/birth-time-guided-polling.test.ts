import assert from "node:assert/strict";
import test from "node:test";
import { runBirthTimeScoringPoll } from "../src/lib/birth-time-guided-polling.ts";
import { parseJourneyResponse } from "../src/lib/birth-time-journey-client.ts";
import { highConfirmationTurn } from "./birth-time-journey-client-test-support.ts";

const completedTurn = parseJourneyResponse(highConfirmationTurn);
const pendingTurn = parseJourneyResponse({
  ...highConfirmationTurn,
  snapshot: {
    ...highConfirmationTurn.snapshot,
    state: "rectifying",
    assistantIntent: "collect_dated_life_events",
    input: "life_events",
    confidence: null,
    canApply: false,
  },
  candidateResult: null,
  nextAction: { kind: "score_pending", jobId: "c70ea014-f8b4-41f2-9305-e4ae60c0d4d1" },
  progress: { ...highConfirmationTurn.progress, phase: "scoring" },
  permissions: { canConfirmCandidate: false },
});

test("polling is sequential and returns the first completed turn", async () => {
  let active = 0;
  let peak = 0;
  let calls = 0;
  const entered = Array.from({ length: 3 }, () => Promise.withResolvers<void>());
  const gates = Array.from(
    { length: 3 },
    () => Promise.withResolvers<typeof pendingTurn | typeof completedTurn>(),
  );
  const running = runBirthTimeScoringPoll({
    initial: pendingTurn,
    maxAttempts: 4,
    signal: new AbortController().signal,
    delay: async () => undefined,
    poll: async () => {
      const call = calls;
      calls += 1;
      active += 1;
      peak = Math.max(peak, active);
      entered[call]?.resolve();
      const turn = await gates[call].promise;
      active -= 1;
      return turn;
    },
  });

  await entered[0].promise;
  assert.equal(calls, 1, "a second poll must not start while the first is unresolved");
  gates[0].resolve(pendingTurn);

  await entered[1].promise;
  assert.equal(active, 1);
  assert.equal(calls, 2, "only one deferred poll may be active at a time");
  gates[1].resolve(pendingTurn);

  await entered[2].promise;
  assert.equal(active, 1);
  assert.equal(calls, 3);
  gates[2].resolve(completedTurn);
  const result = await running;

  assert.equal(calls, 3);
  assert.equal(peak, 1);
  assert.equal(result.kind, "completed");
});

test("polling stops on cancellation and ignores later work", async () => {
  const controller = new AbortController();
  let calls = 0;
  const result = await runBirthTimeScoringPoll({
    initial: pendingTurn,
    maxAttempts: 5,
    signal: controller.signal,
    delay: async () => { controller.abort(); },
    poll: async () => { calls += 1; return pendingTurn; },
  });

  assert.equal(calls, 1);
  assert.equal(result.kind, "cancelled");
});

test("bounded polling preserves the pending turn instead of inventing completion", async () => {
  const result = await runBirthTimeScoringPoll({
    initial: pendingTurn,
    maxAttempts: 2,
    signal: new AbortController().signal,
    delay: async () => undefined,
    poll: async () => pendingTurn,
  });

  assert.equal(result.kind, "exhausted");
  assert.equal(result.turn.nextAction.kind, "score_pending");
});
