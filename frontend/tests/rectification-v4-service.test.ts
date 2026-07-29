import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";
import { createRectificationV4CaseService } from "../src/lib/rectification-v4/case-service.ts";
import type { CalculationSpec } from "../src/lib/rectification-v4/contracts.ts";
import { createRectificationV4MemoryStore } from "../src/lib/rectification-v4/memory-store.ts";
import { createRectificationV4Worker } from "../src/lib/rectification-v4/worker.ts";

const fixedNow = () => new Date("2026-07-28T12:00:00.000Z");
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

async function withMode<T>(mode: "v4_legacy" | "v5_shadow" | "v5_agent", run: () => Promise<T>): Promise<T> {
  const keys = ["RECTIFICATION_AGENT_V5_ENABLED", "RECTIFICATION_AGENT_V5_SHADOW", "RECTIFICATION_AGENT_V5_CANARY_PERCENT"] as const;
  const before = Object.fromEntries(keys.map((key) => [key, process.env[key]]));
  process.env.RECTIFICATION_AGENT_V5_ENABLED = mode === "v4_legacy" ? "0" : "1";
  process.env.RECTIFICATION_AGENT_V5_SHADOW = mode === "v5_shadow" ? "1" : "0";
  process.env.RECTIFICATION_AGENT_V5_CANARY_PERCENT = "100";
  try { return await run(); } finally {
    for (const key of keys) {
      if (before[key] === undefined) delete process.env[key];
      else process.env[key] = before[key];
    }
  }
}

test("same calculation spec resumes while a changed spec abandons the old case and stales its job", async () => withMode("v4_legacy", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const first = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const resumed = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: { ...spec } });
  assert.equal(resumed.case.id, first.case.id);

  const queued = await service.answer({
    userId, caseId: first.case.id, actionId: randomUUID(), expectedCaseVersion: 0, answer: "2016年9月上大学",
  });
  assert.ok(queued?.job);
  const replacement = await service.createCase({
    userId, actionId: randomUUID(), calculationSpec: { ...spec, candidateRange: { start: "04:45", end: "05:30" } },
  });
  assert.notEqual(replacement.case.id, first.case.id);
  assert.equal(store.cases.get(first.case.id)?.status, "abandoned");
  assert.equal(store.jobs.get(queued.job.id)?.status, "stale");
}));

test("answer is durably queued and polling does not mutate the job", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  assert.equal(created.case.protocol, "rectification-evidence-v5");
  assert.equal(created.case.deploymentMode, "v5_agent");
  const queued = await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2015年7月高中毕业后复读一年，2016年6月再次毕业", modelId: "gpt-5.5",
  });
  assert.equal(queued?.case.status, "processing");
  assert.equal(queued?.turns.at(-1)?.modelId, "gpt-5.5");
  const before = JSON.stringify([...store.jobs.values()]);
  assert.equal((await service.loadCase(userId, created.case.id))?.job, null);
  assert.equal(JSON.stringify([...store.jobs.values()]), before);
}));

test("V5 agent fallback persists Agent Run, Public Message and a server-owned opportunity", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const queued = await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2016年离家去外地上大学",
  });
  assert.ok(queued?.job);
  const worker = createRectificationV4Worker({
    store, now: fixedNow,
    engine: { async score() { throw new Error("engine must not run before enough events"); } },
  });
  assert.equal(await worker.runOnce(), true);
  const done = await service.loadCase(userId, created.case.id);
  const event = done?.events.find((item) => item.summary === "离家去外地上大学");
  const run = [...store.agentRuns.values()][0];
  const message = store.publicMessages.get(queued.job.id);
  assert.ok(event && run && message);
  assert.equal(run.deploymentMode, "v5_agent");
  assert.equal(run.validatedDecision.mode, "deterministic_fallback");
  assert.equal(run.validatedDecision.selectedOpportunity?.kind, "ask_new_event");
  assert.equal(run.validatedDecision.selectedOpportunity?.targetEventId, null);
  assert.equal(done?.case.currentQuestion?.targetEventId, null);
  assert.match(done?.case.currentQuestion?.prompt ?? "", /离家去外地上大学/);
  assert.doesNotMatch(done?.case.currentQuestion?.prompt ?? "", /具体哪一天|几号/);
  assert.equal(message.question, done?.case.currentQuestion?.prompt);
  assert.equal(done?.case.latestSnapshot, null);
}));

test("V5 shadow runs and persists V5 artifacts but keeps the legacy visible projection", async () => withMode("v5_shadow", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const queued = await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2016年离家去外地上大学",
  });
  const worker = createRectificationV4Worker({
    store, now: fixedNow,
    engine: { async score() { throw new Error("engine must not run before enough events"); } },
  });
  assert.equal(await worker.runOnce(), true);
  const done = await service.loadCase(userId, created.case.id);
  const event = done?.events[0];
  const run = [...store.agentRuns.values()][0];
  assert.ok(queued?.job && event && run);
  assert.equal(run.deploymentMode, "v5_shadow");
  assert.equal(run.validatedDecision.selectedOpportunity?.kind, "ask_new_event");
  assert.equal(run.validatedDecision.selectedOpportunity?.targetEventId, null);
  assert.equal(done.case.currentQuestion?.targetEventId, event.eventId);
  assert.match(done.case.currentQuestion?.reason ?? "", /V4 legacy projector/);
  assert.match(store.publicMessages.get(queued.job.id)?.acknowledgement ?? "", /我记下了/);
}));

test("legacy cases are not hard-switched to V5 even when flags change later", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await withMode("v4_legacy", () => service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec }));
  await withMode("v5_agent", async () => {
    const queued = await service.answer({
      userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0, answer: "2016年9月上大学",
    });
    const worker = createRectificationV4Worker({
      store, now: fixedNow,
      engine: { async score() { throw new Error("engine must not run before enough events"); } },
    });
    assert.equal(await worker.runOnce(), true);
    const run = [...store.agentRuns.values()][0];
    assert.ok(queued?.job && run);
    assert.equal(run.deploymentMode, "v4_legacy");
    assert.equal(run.fallbackReason, "deployment_mode_legacy");
  });
});
