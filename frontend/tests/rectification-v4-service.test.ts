import assert from "node:assert/strict";
import test from "node:test";
import { randomUUID } from "node:crypto";
import { createRectificationV4CaseService } from "../src/lib/rectification-v4/case-service.ts";
import type { CalculationSpec } from "../src/lib/rectification-v4/contracts.ts";
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
  assert.equal(created.case.currentQuestion?.domain, "other");
  assert.match(created.case.currentQuestion?.prompt ?? "", /不需要按固定领域回答/);
  const queued = await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2015年7月高中毕业后复读一年，2016年6月再次毕业",
    modelId: "gpt-5.5",
  });
  assert.equal(queued?.case.status, "processing");
  assert.equal(queued?.job?.status, "pending");
  assert.equal(queued?.turns.at(-1)?.modelId, "gpt-5.5");
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
  assert.equal(done?.case.currentQuestion?.domain, "other");
  assert.equal(done?.case.currentQuestion?.targetEventId, null);
  assert.match(done?.case.currentQuestion?.prompt ?? "", /继续讲另一件/);
  assert.equal(done?.case.latestSnapshot, null);
  assert.equal(queued?.job?.status, "pending");
});

test("worker rejects a model-authored domain jump while the latest event still needs a month", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  await service.answer({
    userId,
    caseId: created.case.id,
    actionId: randomUUID(),
    expectedCaseVersion: created.case.version,
    answer: "2016年离家去外地上大学",
    modelId: "gpt-5.5",
  });
  const worker = createRectificationV4Worker({
    store,
    now: fixedNow,
    engine: { async score() { throw new Error("engine must not run before enough events"); } },
    questionAuthor: async () => ({
      id: randomUUID(),
      domain: "relocation",
      targetEventId: null,
      prompt: "请说一次影响较大的搬家或长期迁居，并给出尽可能准确的年月。",
      recallCost: "low",
      reason: "模型错误地跳到了另一个领域。",
    }),
  });

  assert.equal(await worker.runOnce(), true);
  const done = await service.loadCase(userId, created.case.id);
  const event = done?.events.find((item) => item.summary === "离家去外地上大学");

  assert.ok(event);
  assert.equal(done?.case.currentQuestion?.targetEventId, event.eventId);
  assert.equal(done?.case.currentQuestion?.domain, "education");
  assert.match(done?.case.currentQuestion?.prompt ?? "", /离家去外地上大学/);
  assert.match(done?.case.currentQuestion?.prompt ?? "", /月份或日期/);
  assert.doesNotMatch(done?.case.currentQuestion?.prompt ?? "", /搬家或长期迁居/);
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

test("worker gives the selected model full conversation context for the next question", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createRectificationV4CaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const contexts: Array<{
    modelId: string | null;
    turnAnswers: string[];
    eventSummaries: string[];
  }> = [];
  const worker = createRectificationV4Worker({
    store,
    now: fixedNow,
    engine: { async score() { throw new Error("engine must not run before enough events"); } },
    questionAuthor: async (context) => {
      contexts.push({
        modelId: context.modelId,
        turnAnswers: context.turns.map((turn) => turn.answer),
        eventSummaries: context.events.map((event) => event.summary),
      });
      return {
        id: randomUUID(),
        domain: "other",
        targetEventId: null,
        prompt: context.turns.length === 1
          ? "你提到复读后再次毕业，这段连续变化很清楚。后来还有哪一次环境变化让你印象很深？"
          : "你提到毕业和搬家是连续发生的。那次搬家前后，生活节奏还有什么明显变化？",
        recallCost: "low",
        reason: "根据完整对话选择下一条高信息量追问。",
      };
    },
  });

  let current = created;
  for (const [answer, modelId] of [
    ["2015年7月高中毕业后复读一年，2016年6月再次毕业", "gpt-5.5"],
    ["2018年8月搬到北京，之后开始独立生活", "deepseek-chat"],
  ] as const) {
    const queued = await service.answer({
      userId,
      caseId: created.case.id,
      actionId: randomUUID(),
      expectedCaseVersion: current.case.version,
      answer,
      modelId,
    });
    assert.ok(queued?.job);
    assert.equal(await worker.runOnce(), true);
    current = (await service.loadCase(userId, created.case.id))!;
  }

  assert.equal(contexts.length, 2);
  assert.equal(contexts[0]?.modelId, "gpt-5.5");
  assert.deepEqual(contexts[1]?.turnAnswers, [
    "2015年7月高中毕业后复读一年，2016年6月再次毕业",
    "2018年8月搬到北京，之后开始独立生活",
  ]);
  assert.equal(contexts[1]?.modelId, "deepseek-chat");
  assert.equal(contexts[1]?.eventSummaries.length, 3);
  assert.match(current.case.currentQuestion?.prompt ?? "", /毕业和搬家/);
  assert.equal(current.case.status === "awaiting_answer" && current.case.currentQuestion === null, false);
});
