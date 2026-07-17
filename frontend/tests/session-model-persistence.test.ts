import assert from "node:assert/strict";
import test from "node:test";
import {
  SessionModelPersistenceQueue,
  persistSessionModelSelection,
} from "../src/lib/session-model-persistence.ts";

test("persists only model_id for the owned session", async () => {
  const writes: unknown[] = [];

  await persistSessionModelSelection(async (write) => {
    writes.push(write);
    return { found: true, error: null };
  }, "user-1", "session-1", "gpt-mini");

  assert.deepEqual(writes, [{
    values: { model_id: "gpt-mini" },
    sessionId: "session-1",
    userId: "user-1",
  }]);
});

test("serializes model writes for the same session", async () => {
  const queue = new SessionModelPersistenceQueue();
  const calls: string[] = [];
  let releaseFirst = () => {};
  const firstGate = new Promise<void>((resolve) => { releaseFirst = resolve; });

  const first = queue.enqueue("session-1", async () => {
    calls.push("first");
    await firstGate;
  });
  const second = queue.enqueue("session-1", async () => {
    calls.push("second");
  });

  await new Promise<void>((resolve) => setImmediate(resolve));
  assert.deepEqual(calls, ["first"]);
  releaseFirst();
  await Promise.all([first, second]);
  assert.deepEqual(calls, ["first", "second"]);
});

test("continues with the latest model write after an earlier sync fails", async () => {
  const queue = new SessionModelPersistenceQueue();
  const calls: string[] = [];

  const failed = queue.enqueue("session-1", async () => {
    calls.push("failed");
    throw new Error("offline");
  });
  const latest = queue.enqueue("session-1", async () => {
    calls.push("latest");
  });

  const results = await Promise.allSettled([failed, latest]);
  assert.equal(results[0]?.status, "rejected");
  assert.equal(results[1]?.status, "fulfilled");
  assert.deepEqual(calls, ["failed", "latest"]);
});
