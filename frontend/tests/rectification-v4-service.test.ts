import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";
import { composeRectificationPublicTurn } from "../src/lib/rectification-agent/orchestrator.ts";
import { createRectificationV4CaseService } from "../src/lib/rectification-v4/case-service.ts";
import type { CalculationSpec, CandidateSnapshot, LifeEventRevision, PendingEvidence } from "../src/lib/rectification-v4/contracts.ts";
import { createRectificationV4MemoryStore } from "../src/lib/rectification-v4/memory-store.ts";
import { createRectificationV4Worker, resolvedPendingEvidence } from "../src/lib/rectification-v4/worker.ts";

function createTestCaseService(
  store: Parameters<typeof createRectificationV4CaseService>[0],
  options: Parameters<typeof createRectificationV4CaseService>[1] = {},
) {
  return createRectificationV4CaseService(store, {
    generateOpeningQuestion: async ({ candidateRange }) =>
      `Agent 将在 ${candidateRange.start}–${candidateRange.end} 的待核对范围内陪你梳理；这并不是已确认的出生分钟。你愿意先说一段自己记得比较清楚的人生经历吗？`,
    ...options,
  });
}

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

test("new cases use the Agent-generated opening and do not regenerate it when resuming", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  let calls = 0;
  const service = createTestCaseService(store, {
    now: fixedNow,
    generateOpeningQuestion: async ({ candidateRange }) => {
      calls += 1;
      return `这是 Agent 为 ${candidateRange.start}–${candidateRange.end} 生成的首轮引导。`;
    },
  });
  const userId = randomUUID();
  const first = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const resumed = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  assert.equal(first.case.currentQuestion?.prompt, "这是 Agent 为 04:30–05:30 生成的首轮引导。");
  assert.equal(first.case.agentMode, "deterministic_fallback");
  assert.equal(resumed.case.id, first.case.id);
  assert.equal(calls, 1);
}));

test("same calculation spec resumes while a changed spec abandons the old case and stales its job", async () => withMode("v4_legacy", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
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

test("new case replaces paused or orphaned processing state and can be answered immediately", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
  const userId = randomUUID();

  const first = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  await service.transition({ userId, caseId: first.case.id, actionId: randomUUID(), expectedCaseVersion: 0, kind: "pause" });
  const afterPause = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  assert.notEqual(afterPause.case.id, first.case.id);
  assert.equal(store.cases.get(first.case.id)?.status, "abandoned");
  assert.ok(afterPause.case.currentQuestion);

  store.cases.set(afterPause.case.id, { ...afterPause.case, status: "processing", phase: "reasoning", currentQuestion: null });
  const replacement = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  assert.notEqual(replacement.case.id, afterPause.case.id);
  assert.equal(store.cases.get(afterPause.case.id)?.status, "abandoned");
  assert.ok(replacement.case.currentQuestion);

  const queued = await service.answer({
    userId,
    caseId: replacement.case.id,
    actionId: randomUUID(),
    expectedCaseVersion: replacement.case.version,
    answer: "2016 年离家去外地上大学",
  });
  assert.ok(queued?.job);
}));

test("new scoring version replaces a resumable Case created by an older algorithm", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const first = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  store.cases.set(first.case.id, { ...first.case, algorithmVersion: "rectification-v5-matrix-scoring-1" });

  const second = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });

  assert.notEqual(second.case.id, first.case.id);
  assert.equal(second.case.algorithmVersion, "rectification-v5-matrix-scoring-2");
  assert.equal(store.cases.get(first.case.id)?.status, "abandoned");
}));

test("answer is durably queued and a processing case reload restores its active job", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
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
  const queuedJob = queued?.job;
  assert.ok(queuedJob);
  const before = JSON.stringify([...store.jobs.values()]);
  const restored = await service.loadCase(userId, created.case.id);
  assert.equal(restored?.job?.id, queuedJob.id);
  assert.equal(restored?.job?.status, "pending");
  assert.equal(JSON.stringify([...store.jobs.values()]), before);
}));

test("V5 agent fallback persists the Director decision, Public Message and next question", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const queued = await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2016年9月离家去外地上大学",
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
  assert.equal(run.validatedDecision.decision.action, "ask_question");
  assert.equal(run.validatedDecision.selectedOpportunity, null);
  assert.equal(done?.case.currentQuestion?.targetEventId, null);
  assert.ok((done?.case.currentQuestion?.prompt ?? "").length > 0);
  assert.doesNotMatch(done?.case.currentQuestion?.prompt ?? "", /具体哪一天|几号/);
  assert.equal(done?.case.currentQuestion?.prompt, composeRectificationPublicTurn(message));
  assert.match(done?.case.currentQuestion?.prompt ?? "", /离家去外地上大学/);
  assert.match(done?.case.currentQuestion?.prompt ?? "", /交叉核对/);
  assert.ok(message.question && done?.case.currentQuestion?.prompt.includes(message.question));
  assert.equal(done?.case.latestSnapshot, null);
}));

test("V5 shadow runs and persists V5 artifacts but keeps the legacy visible projection", async () => withMode("v5_shadow", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const queued = await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2016年9月离家去外地上大学",
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
  assert.equal(run.validatedDecision.decision.action, "ask_question");
  assert.equal(run.validatedDecision.selectedOpportunity, null);
  assert.equal(done.case.currentQuestion?.targetEventId, null);
  assert.match(done.case.currentQuestion?.reason ?? "", /V4 legacy projector/);
  assert.match(store.publicMessages.get(queued.job.id)?.acknowledgement ?? "", /我记下了/);
}));

test("V5 shadow keeps legacy year-precision refinement targeted to the original event", async () => withMode("v5_shadow", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
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
  assert.ok(queued?.job && event);
  assert.equal(done.case.currentQuestion?.targetEventId, event.eventId);
  assert.match(done.case.currentQuestion?.reason ?? "", /V4 legacy projector/);
  assert.ok([...store.agentRuns.values()].length > 0);
  assert.ok(store.publicMessages.has(queued.job.id));
}));

test("legacy cases are not hard-switched to V5 even when flags change later", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
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

test("V5 Agent regenerate rewrites only the current semantic question and replays the same action once", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  let realizationCalls = 0;
  const service = createTestCaseService(store, {
    now: fixedNow,
    regenerateDirectorQuestion: async ({ currentQuestion }) => {
      realizationCalls += 1;
      await new Promise((resolve) => setTimeout(resolve, 5));
      return `${currentQuestion}（换一种问法）`;
    },
  });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const queued = await service.answer({
    userId,
    caseId: created.case.id,
    actionId: randomUUID(),
    expectedCaseVersion: created.case.version,
    answer: "2020年4月去石油化工研究院实习做研究员",
  });
  assert.ok(queued?.job);
  const worker = createRectificationV4Worker({
    store,
    now: fixedNow,
    engine: { async score() { throw new Error("engine must not run before enough events"); } },
  });
  assert.equal(await worker.runOnce(), true);

  const before = await service.loadCase(userId, created.case.id);
  assert.ok(before?.case.currentQuestion);
  const actionId = randomUUID();
  const regenerationInput = {
    userId,
    caseId: created.case.id,
    actionId,
    expectedCaseVersion: before.case.version,
  };
  const [regenerated, concurrentReplay] = await Promise.all([
    service.regenerateQuestion(regenerationInput),
    service.regenerateQuestion(regenerationInput),
  ]);
  assert.ok(regenerated?.case.currentQuestion);
  assert.equal(concurrentReplay?.case.currentQuestion?.id, regenerated.case.currentQuestion.id);
  assert.equal(realizationCalls, 1);
  assert.equal(regenerated.case.version, before.case.version + 1);
  assert.notEqual(regenerated.case.currentQuestion.id, before.case.currentQuestion.id);
  assert.equal(regenerated.case.currentQuestion.domain, before.case.currentQuestion.domain);
  assert.equal(regenerated.case.currentQuestion.targetEventId, before.case.currentQuestion.targetEventId);
  assert.equal(regenerated.case.evidenceSetHash, before.case.evidenceSetHash);
  assert.deepEqual(regenerated.events, before.events);
  assert.deepEqual(regenerated.turns, before.turns);
  assert.deepEqual(regenerated.case.latestSnapshot, before.case.latestSnapshot);
  assert.equal(store.jobs.size, 1);

  const replayed = await service.regenerateQuestion({
    userId,
    caseId: created.case.id,
    actionId,
    expectedCaseVersion: before.case.version,
  });
  assert.equal(replayed?.case.version, regenerated.case.version);
  assert.equal(replayed?.case.currentQuestion?.id, regenerated.case.currentQuestion.id);
  assert.equal(realizationCalls, 1);
  assert.equal(store.jobs.size, 1);
  assert.equal(regenerated.case.latestSnapshot?.canConfirmExactMinute ?? false, false);
}));

test("V5 Agent regenerate converts historical selected opportunities into server-rendered questions", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const queued = await service.answer({
    userId,
    caseId: created.case.id,
    actionId: randomUUID(),
    expectedCaseVersion: created.case.version,
    answer: "2020年4月去石油化工研究院实习做研究员",
  });
  assert.ok(queued?.job);
  const worker = createRectificationV4Worker({
    store,
    now: fixedNow,
    engine: { async score() { throw new Error("engine must not run before enough events"); } },
  });
  assert.equal(await worker.runOnce(), true);

  const current = await service.loadCase(userId, created.case.id);
  const event = current?.events.find((item) => item.domain === "career");
  const run = [...store.agentRuns.values()][0];
  assert.ok(current?.case.currentQuestion && event && run && queued.job);

  const opportunityId = randomUUID();
  store.validatedDecisions.set(queued.job.id, {
    decision: { action: "ask_question", opportunityId, narrativeFocus: ["date_precision"] },
    mode: "agent",
    validationIssues: [],
    selectedOpportunity: {
      contractVersion: "semantic-question-v2",
      opportunityId,
      kind: "refine_event_date",
      domain: "career",
      targetEventId: event.eventId,
      goal: "核对这段实习经历的月份",
      requestedFields: ["event_month"],
      anchors: [event.summary],
      contextFacts: [],
      forbiddenMoves: ["expose_technique_trace"],
      fallbackPrompt: "分盘已表明甲组更有把握，请确认 D10 的结论。",
      reason: "历史问题机会兼容测试",
      expectedInformationGain: .5,
      dateSensitivity: .5,
      candidateSplitRelevance: .5,
      domainCoverageGain: 0,
      recallEase: .8,
      novelty: .5,
      repetitionPenalty: 0,
      privacyCost: 0,
      utility: .5,
      active: true,
    },
  });
  store.cases.set(created.case.id, {
    ...current.case,
    currentQuestion: {
      ...current.case.currentQuestion,
      domain: "career",
      targetEventId: event.eventId,
      prompt: "分盘已表明甲组更有把握，请确认 D10 的结论。",
    },
  });

  const regenerated = await service.regenerateQuestion({
    userId,
    caseId: created.case.id,
    actionId: randomUUID(),
    expectedCaseVersion: current.case.version,
  });
  assert.ok(regenerated?.case.currentQuestion);
  assert.equal(regenerated.case.currentQuestion.domain, "career");
  assert.equal(regenerated.case.currentQuestion.targetEventId, event.eventId);
  assert.match(regenerated.case.currentQuestion.prompt, /2020年4月|石油化工研究院|实习|研究员/);
  assert.doesNotMatch(regenerated.case.currentQuestion.prompt, /D10|分盘|测算|推演|甲组|头一组|前者占优/);
}));

test("legacy and shadow cases cannot call the V5 Agent question renderer", async () => {
  for (const mode of ["v4_legacy", "v5_shadow"] as const) {
    await withMode(mode, async () => {
      const store = createRectificationV4MemoryStore();
      const service = createTestCaseService(store, { now: fixedNow });
      const userId = randomUUID();
      const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
      assert.equal(await service.regenerateQuestion({
        userId,
        caseId: created.case.id,
        actionId: randomUUID(),
        expectedCaseVersion: created.case.version,
      }), null);
    });
  }
});


test("worker closes only the uniquely matched historical pending evidence", async () => withMode("v4_legacy", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const pending: PendingEvidence = {
    id: randomUUID(),
    caseId: created.case.id,
    turnId: randomUUID(),
    rawText: "后来搬家一次，但记不清时间了",
    reasonCode: "date_unresolved",
    targetEventId: null,
    resolvedEventId: null,
    createdAt: "2026-07-27T12:00:00.000Z",
    resolvedAt: null,
  };
  store.pendingEvidence.set(pending.id, pending);

  const queued = await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2018年9月搬家到北京",
  });
  assert.ok(queued?.job);
  const worker = createRectificationV4Worker({
    store, now: fixedNow,
    engine: { async score() { throw new Error("engine must not run before enough events"); } },
  });
  assert.equal(await worker.runOnce(), true);

  const resolved = store.pendingEvidence.get(pending.id);
  assert.ok(resolved?.resolvedEventId);
  assert.equal(resolved.resolvedAt, fixedNow().toISOString());
  const events = await store.loadEvents(userId, created.case.id);
  assert.ok(events.some((event) => event.eventId === resolved.resolvedEventId && event.domain === "relocation"));
}));

test("worker leaves ambiguous historical pending evidence unresolved", async () => withMode("v4_legacy", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const pending = ["后来搬家一次，但记不清时间了", "以前也搬家，时间忘了"].map((rawText): PendingEvidence => ({
    id: randomUUID(), caseId: created.case.id, turnId: randomUUID(), rawText,
    reasonCode: "date_unresolved", targetEventId: null, resolvedEventId: null,
    createdAt: "2026-07-27T12:00:00.000Z", resolvedAt: null,
  }));
  for (const item of pending) store.pendingEvidence.set(item.id, item);

  await service.answer({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: 0,
    answer: "2018年9月搬家到北京",
  });
  const worker = createRectificationV4Worker({
    store, now: fixedNow,
    engine: { async score() { throw new Error("engine must not run before enough events"); } },
  });
  assert.equal(await worker.runOnce(), true);
  assert.ok(pending.every((item) => store.pendingEvidence.get(item.id)?.resolvedAt === null));
}));

test("date pending evidence closes only after the event date changes", () => {
  const eventId = randomUUID();
  const original: LifeEventRevision = {
    id: randomUUID(), eventId, revision: 1, domain: "relationship", eventKind: "relationship_start",
    subject: "self", relatedPerson: "partner", summary: "关系开始", rawText: "2020年关系开始",
    dateRange: { start: "2020-01-01", end: "2020-12-31", precision: "year", label: "2020年" },
    scoreability: "scoreable", supersedesRevisionId: null, createdAt: "2026-07-27T12:00:00.000Z",
  };
  const pending: PendingEvidence = {
    id: randomUUID(), caseId: randomUUID(), turnId: randomUUID(), rawText: "时间还不确定",
    reasonCode: "date_unresolved", targetEventId: eventId, resolvedEventId: null,
    createdAt: "2026-07-27T12:00:00.000Z", resolvedAt: null,
  };
  const reclassified: LifeEventRevision = {
    ...original, id: randomUUID(), revision: 2, eventKind: "relationship_end", summary: "关系结束",
    scoreability: "pending_review", supersedesRevisionId: original.id, createdAt: "2026-07-28T12:00:00.000Z",
  };
  assert.deepEqual(resolvedPendingEvidence([pending], [reclassified], [original], "2026-07-30"), []);

  const dated: LifeEventRevision = {
    ...reclassified, id: randomUUID(), revision: 3,
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
    supersedesRevisionId: reclassified.id,
  };
  assert.deepEqual(resolvedPendingEvidence([pending], [dated], [original, reclassified], "2026-07-30"), [{
    pendingEvidenceId: pending.id,
    resolvedEventId: eventId,
  }]);
});

test("legacy scoreable relationship-end snapshots cannot be accepted", async () => withMode("v5_agent", async () => {
  const store = createRectificationV4MemoryStore();
  const service = createTestCaseService(store, { now: fixedNow });
  const userId = randomUUID();
  const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
  const revision: LifeEventRevision = {
    id: randomUUID(), eventId: randomUUID(), revision: 1, domain: "relationship", eventKind: "relationship_end",
    subject: "self", relatedPerson: "partner", summary: "关系结束", rawText: "2020年关系结束",
    dateRange: { start: "2020-01-01", end: "2020-12-31", precision: "year", label: "2020年" },
    scoreability: "scoreable", supersedesRevisionId: null, createdAt: fixedNow().toISOString(),
  };
  const revised = await store.reviseEvent({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: created.case.version,
    revision, jobId: randomUUID(), now: fixedNow().toISOString(),
  });
  const snapshot: CandidateSnapshot = {
    id: randomUUID(), caseId: created.case.id, caseVersion: revised.case.version,
    evidenceSetHash: revised.case.evidenceSetHash, calculationSpecHash: revised.case.calculationSpecHash,
    algorithmVersion: "rectification-v5-matrix-scoring-1",
    candidates: [{ time: "05:12", score: 10, supportingEventIds: [revision.eventId], conflictingEventIds: [] }],
    clusters: [{ rank: 1, startTime: "05:12", endTime: "05:18", representativeTime: "05:13", widthMinutes: 7, peakScore: 10, scoreMass: 1 }],
    robustness: { neighborSupportMinutes: 7, leaveOneOutRetentionRate: .8, leaveOneDomainOutRetentionRate: .8, dateSensitivityRetentionRate: .8, calculationSpecHashMatched: true },
    canConfirmExactMinute: false, canAcceptRange: true, gateReasons: [], createdAt: fixedNow().toISOString(),
  };
  store.cases.set(created.case.id, { ...revised.case, latestSnapshot: snapshot });
  assert.equal(await service.acceptRange({
    userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: revised.case.version,
    startTime: "05:12", endTime: "05:18",
  }), null);
}));
