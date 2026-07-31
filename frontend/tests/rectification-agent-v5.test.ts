import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";

import {
  agentRunSchema,
  diagnosticsSummarySchema,
  type DiagnosticsSummary,
  type QuestionOpportunity,
} from "../src/lib/rectification-agent/contracts.ts";
import { rectificationCanaryBucket, selectRectificationDeploymentMode } from "../src/lib/rectification-agent/feature-policy.ts";
import { buildQuestionOpportunities } from "../src/lib/rectification-agent/opportunity-builder.ts";
import { runBoundedReasoner } from "../src/lib/rectification-agent/reasoner-agent.ts";
import { generateOpeningQuestion, realizePublicMessage, validateQuestionRealization } from "../src/lib/rectification-agent/renderer-agent.ts";
import { createRectificationV4CaseService } from "../src/lib/rectification-v4/case-service.ts";
import type {
  CalculationSpec,
  CandidateSnapshot,
  LifeEventRevision,
  RectificationV4Case,
} from "../src/lib/rectification-v4/contracts.ts";
import { reconcileV4Evidence } from "../src/lib/rectification-v4/extraction.ts";
import { calculationSpecHash, rectificationFingerprint } from "../src/lib/rectification-v4/fingerprints.ts";
import { createRectificationV4MemoryStore } from "../src/lib/rectification-v4/memory-store.ts";
import { createRectificationV4Worker } from "../src/lib/rectification-v4/worker.ts";
import { v5EngineResult, withV5Mode } from "./rectification-v5-test-support.ts";

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

const caseId = "00000000-0000-4000-8000-000000000901";
const snapshotId = "00000000-0000-4000-8000-000000000902";
const opportunityId = "00000000-0000-4000-8000-000000000903";
const now = "2026-07-28T00:00:00.000Z";

test("opening Agent generates and validates the first rectification message", async () => {
  const phases: string[] = [];
  const message = await generateOpeningQuestion({
    caseId,
    candidateRange: { start: "00:00", end: "23:59" },
    modelId: "test-model",
    generate: async (_prompt, phase) => {
      phases.push(phase);
      return phase === "generate"
        ? { object: { message: "目前核对的是 00:00–23:59 候选范围，尚未确认出生分钟。请从学习、工作或感情中选一段经历来说。" } }
        : { object: { message: "目前核对的是 00:00–23:59 候选范围，并不是已确认的出生分钟。请讲一段你最清楚的经历，也可以连续讲几件相关的事；记不清或想换方向都可以。" } };
    },
  });
  assert.deepEqual(phases, ["generate", "repair"]);
  assert.match(message, /00:00–23:59/);
  assert.match(message, /并不是已确认的出生分钟/);
});

test("completion artifact fingerprints are canonical and payload-sensitive", () => {
  const left = rectificationFingerprint({ status: "complete", artifact: { b: 2, a: 1 } });
  const reordered = rectificationFingerprint({ artifact: { a: 1, b: 2 }, status: "complete" });
  const changed = rectificationFingerprint({ artifact: { a: 1, b: 3 }, status: "complete" });
  assert.equal(left, reordered);
  assert.notEqual(left, changed);
});
const spec: CalculationSpec = {
  version: "rectification-calculation-spec-v4",
  birthDate: "1997-08-08",
  candidateRange: { start: "05:00", end: "06:00" },
  latitude: 36.419,
  longitude: 114.213,
  timezoneOffsetHours: 8,
  ayanamsa: "lahiri",
  nodeMode: "mean",
  minuteStep: 1,
};
const snapshot: CandidateSnapshot = {
  id: snapshotId,
  caseId,
  caseVersion: 2,
  evidenceSetHash: "e".repeat(64),
  calculationSpecHash: calculationSpecHash(spec),
  algorithmVersion: "rectification-v5-matrix-scoring-1",
  candidates: [{ time: "05:13", score: 10, supportingEventIds: [], conflictingEventIds: [] }],
  clusters: [{ rank: 1, startTime: "05:13", endTime: "05:15", representativeTime: "05:13", widthMinutes: 3, peakScore: 10, scoreMass: 1 }],
  robustness: { neighborSupportMinutes: 3, leaveOneOutRetentionRate: 1, leaveOneDomainOutRetentionRate: 1, dateSensitivityRetentionRate: 1, calculationSpecHashMatched: true },
  canConfirmExactMinute: false,
  canAcceptRange: false,
  gateReasons: ["insufficient_scoreable_events"],
  createdAt: now,
};
const diagnostics: DiagnosticsSummary = diagnosticsSummarySchema.parse({
  id: "00000000-0000-4000-8000-000000000904",
  caseId,
  snapshotId,
  primaryClusterRetentionRate: 1,
  leaveOneEventOutRetentionRate: .8,
  leaveOneDomainOutRetentionRate: .7,
  dateSensitivityRetentionRate: .9,
  neighborSupportMinutes: 3,
  primarySecondaryMarginPercent: 12,
  clusterMassRatio: .8,
  unstableEventIds: [],
  mostDiscriminatingLayers: ["D9"],
  eventDateSensitivity: [],
  candidateSplits: [],
  calculationHash: "d".repeat(64),
  createdAt: now,
});
const opportunity: QuestionOpportunity = {
  contractVersion: "semantic-question-v2",
  opportunityId,
  kind: "ask_new_event",
  domain: "career",
  targetEventId: null,
  goal: "收集一件有大致日期的职业变化。",
  requestedFields: ["new_dated_event"],
  anchors: [],
  contextFacts: ["职业领域尚未覆盖。"],
  forbiddenMoves: ["switch_target_event", "ask_multiple_questions", "claim_exact_birth_minute", "invent_event", "invent_date", "expose_private_score", "expose_internal_id", "expose_technique_trace"],
  fallbackPrompt: "请说一件时间比较明确的职业变化经历。",
  reason: "领域覆盖不足。",
  expectedInformationGain: .8,
  dateSensitivity: .5,
  candidateSplitRelevance: .5,
  domainCoverageGain: 1,
  recallEase: .8,
  novelty: 1,
  repetitionPenalty: 0,
  privacyCost: 0,
  utility: .85,
  active: true,
};
const caseValue: RectificationV4Case = {
  id: caseId,
  userId: "00000000-0000-4000-8000-000000000905",
  protocol: "rectification-evidence-v5",
  version: 2,
  status: "processing",
  phase: "reasoning",
  calculationSpec: spec,
  calculationSpecHash: calculationSpecHash(spec),
  evidenceSetHash: "e".repeat(64),
  currentQuestion: null,
  latestSnapshot: snapshot,
  orchestrationModelId: null,
  narrationModelId: null,
  skillVersion: "birth-time-rectification-v5",
  promptVersion: "rectification-agent-v5-1",
  algorithmVersion: "rectification-v5-matrix-scoring-1",
  deploymentMode: "v5_agent",
  agentMode: "deterministic_fallback",
  featureSnapshotId: null,
  latestDiagnosticsId: diagnostics.id,
  acceptedRange: null,
  createdAt: now,
  updatedAt: now,
};

function event(overrides: Partial<LifeEventRevision> = {}): LifeEventRevision {
  return {
    id: randomUUID(),
    eventId: randomUUID(),
    revision: 1,
    domain: "education",
    eventKind: "education_milestone",
    subject: "self",
    relatedPerson: null,
    summary: "2016年大学入学",
    rawText: "2016年9月大学入学",
    dateRange: { start: "2016-09-01", end: "2016-09-30", precision: "month", label: "2016年9月" },
    scoreability: "scoreable",
    supersedesRevisionId: null,
    createdAt: now,
    ...overrides,
  };
}

test("SHA-256 canary assignment is stable and deployment modes are explicit", () => {
  assert.equal(rectificationCanaryBucket("user-a"), 98.66510317660868);
  assert.equal(selectRectificationDeploymentMode("user-a", { RECTIFICATION_AGENT_V5_ENABLED: "0" }), "v4_legacy");
  assert.equal(selectRectificationDeploymentMode("user-a", {
    RECTIFICATION_AGENT_V5_ENABLED: "1", RECTIFICATION_AGENT_V5_CANARY_PERCENT: "100", RECTIFICATION_AGENT_V5_SHADOW: "1",
  }), "v5_shadow");
  assert.equal(selectRectificationDeploymentMode("user-a", {
    RECTIFICATION_AGENT_V5_ENABLED: "1", RECTIFICATION_AGENT_V5_CANARY_PERCENT: "100", RECTIFICATION_AGENT_V5_SHADOW: "0",
  }), "v5_agent");
  assert.equal(selectRectificationDeploymentMode("user-a", {
    RECTIFICATION_AGENT_V5_ENABLED: "1", RECTIFICATION_AGENT_V5_CANARY_PERCENT: "10",
  }), "v4_legacy");
});

test("new-event fallback is a single domain-neutral contract", () => {
  const values = buildQuestionOpportunities({
    caseId,
    events: [event()],
    turns: [],
    snapshot: null,
    diagnostics: null,
  }).filter((value) => value.kind === "ask_new_event");
  assert.equal(values.length, 1);
  assert.equal(values[0]?.domain, "other");
  assert.doesNotMatch(values[0]?.fallbackPrompt ?? "", /教育|迁居|关系|职业|财务|健康/);
});

test("a previously asked unresolved target does not monopolize the next-question route", () => {
  const target = event();
  const values = buildQuestionOpportunities({
    caseId,
    events: [target, event({ eventId: randomUUID(), domain: "relocation", eventKind: "relocation", summary: "搬家到北京" })],
    turns: [],
    snapshot: null,
    diagnostics: null,
    targetDisposition: "unresolved",
    retryTargetEventIds: [target.eventId],
  });
  assert.ok(values.length > 0);
  assert.ok(values.every((value) => value.targetEventId !== target.eventId));
});

test("reasoner falls back when unavailable", async () => {
  const result = await runBoundedReasoner({ caseValue, snapshot, diagnostics, opportunities: [opportunity] });
  assert.equal(result.mode, "deterministic_fallback");
  assert.equal(result.fallbackReason, "reasoner_model_unavailable");
  assert.equal(result.decision.action, "ask_question");
});

test("reasoner permits one diagnostic, then requires a final action and accumulates usage", async () => {
  const phases: string[] = [];
  const result = await runBoundedReasoner({
    caseValue,
    snapshot,
    diagnostics,
    opportunities: [opportunity],
    generateDecision: async (_prompt, phase) => {
      phases.push(phase);
      return phase === "initial"
        ? { object: { action: "run_diagnostic", diagnostic: "neighbor_stability" }, totalUsage: { inputTokens: 11, outputTokens: 3 } }
        : { object: { action: "ask_question", opportunityId, narrativeFocus: ["candidate_change"] }, totalUsage: Promise.resolve({ inputTokens: 7, outputTokens: 2 }) };
    },
  });
  assert.deepEqual(phases, ["initial", "after_diagnostic"]);
  assert.equal(result.mode, "agent");
  assert.equal(result.decision.action, "ask_question");
  assert.equal(result.toolCalls.length, 1);
  assert.equal(result.toolCalls[0]?.outcome, "succeeded");
  assert.equal(result.inputTokenCount, 18);
  assert.equal(result.outputTokenCount, 5);
});

test("reasoner rejects a second diagnostic and enforces the tool budget", async () => {
  const nonfinal = await runBoundedReasoner({
    caseValue,
    snapshot,
    diagnostics,
    opportunities: [opportunity],
    generateDecision: async () => ({ object: { action: "run_diagnostic", diagnostic: "neighbor_stability" } }),
  });
  assert.equal(nonfinal.mode, "deterministic_fallback");
  assert.equal(nonfinal.fallbackReason, "reasoner_returned_nonfinal_diagnostic");
  assert.equal(nonfinal.toolCalls.length, 1);

  const exhausted = await runBoundedReasoner({
    caseValue,
    snapshot,
    diagnostics,
    opportunities: [opportunity],
    maxToolCalls: 0,
    generateDecision: async () => ({ object: { action: "run_diagnostic", diagnostic: "neighbor_stability" } }),
  });
  assert.equal(exhausted.fallbackReason, "diagnostic_budget_exhausted");
  assert.equal(exhausted.toolCalls[0]?.outcome, "rejected");
});

test("renderer rejects an unrelated question and falls back to the semantic contract", () => {
  const target = event({ summary: "2020年4月研究院实习" });
  const targeted: QuestionOpportunity = {
    ...opportunity,
    kind: "refine_event_date",
    domain: "career",
    targetEventId: target.eventId,
    goal: "细化研究院实习日期。",
    requestedFields: ["event_day"],
    anchors: [target.summary],
    contextFacts: ["日期敏感。"],
    fallbackPrompt: "关于“2020年4月研究院实习”，你还记得大概哪一天吗？",
  };
  assert.equal(validateQuestionRealization("你后来有没有搬家？", targeted).valid, false);
  const message = realizePublicMessage({
    acknowledgement: "你提到的是2020年4月研究院实习。",
    candidateUpdate: null,
    limitation: null,
    question: "你后来有没有搬家？",
  }, {
    latestAnswer: "2020年4月研究院实习",
    acceptedEvents: [target],
    pendingEvidence: [],
    snapshot: null,
    previousSnapshot: null,
    validated: {
      decision: { action: "ask_question", opportunityId: targeted.opportunityId, narrativeFocus: [] },
      mode: "agent",
      validationIssues: [],
      selectedOpportunity: targeted,
    },
  });
  assert.equal(message.question, targeted.fallbackPrompt);
});

test("agent-run persistence contract carries deployment, tool, token, and latency facts", () => {
  const parsed = agentRunSchema.parse({
    id: randomUUID(), caseId, jobId: randomUUID(), caseVersion: 2, modelId: "test-model",
    skillVersion: "birth-time-rectification-v5", promptVersion: "rectification-agent-v5-1",
    deploymentMode: "v5_agent", deploymentSha: "abc123",
    decision: { action: "ask_question", opportunityId, narrativeFocus: [] },
    validatedDecision: {
      decision: { action: "ask_question", opportunityId, narrativeFocus: [] }, mode: "agent", validationIssues: [], selectedOpportunity: opportunity,
    },
    toolCalls: [{ tool: "run_rectification_diagnostics", diagnostic: "neighbor_stability", outcome: "succeeded", durationMs: 4, errorCode: null }],
    fallbackReason: null, inputTokenCount: 18, outputTokenCount: 5, latencyMs: 20, createdAt: now,
  });
  assert.equal(parsed.toolCalls.length, 1);
  assert.equal(parsed.inputTokenCount, 18);
  assert.equal(parsed.latencyMs, 20);
});

test("an answer about another event never overwrites the current target and creates a conflict opportunity", () => {
  const target = event();
  const reconciled = reconcileV4Evidence({
    caseId,
    answer: "2018年8月搬家到北京",
    sourceTurnId: randomUUID(),
    asOfDate: "2026-07-28",
    existing: [target],
    targetEventId: target.eventId,
    now: new Date(now),
  });
  assert.equal(reconciled.unansweredTargetEventId, target.eventId);
  assert.equal(reconciled.revisions.some((value) => value.eventId === target.eventId), false);
  assert.equal(reconciled.revisions[0]?.eventKind, "relocation");
  const opportunities = buildQuestionOpportunities({
    caseId,
    events: [target, ...reconciled.revisions],
    turns: [],
    snapshot: null,
    diagnostics: null,
    targetDisposition: reconciled.targetDisposition,
    retryTargetEventIds: [target.eventId],
  });
  const conflict = opportunities.filter((item) => item.kind === "resolve_event_conflict");
  assert.equal(conflict.length, 1);
  assert.equal(conflict[0]?.targetEventId, target.eventId);
});

test("unknown target answers are kept in the turn without pending evidence", () => {
  const target = event();
  const turnId = randomUUID();
  const reconciled = reconcileV4Evidence({
    caseId,
    answer: "我记不清了，可能是那几年之间",
    sourceTurnId: turnId,
    asOfDate: "2026-07-28",
    existing: [target],
    targetEventId: target.eventId,
    now: new Date(now),
  });
  assert.equal(reconciled.revisions.length, 0);
  assert.equal(reconciled.targetDisposition, "unknown");
  assert.equal(reconciled.pending.length, 0);
});

test("shadow mode persists V5 artifacts while preserving the legacy visible reply", async () => {
  async function run(mode: "v4_legacy" | "v5_shadow") {
    return withV5Mode(mode, async () => {
      const store = createRectificationV4MemoryStore();
      const service = createTestCaseService(store, { now: () => new Date(now) });
      const worker = createRectificationV4Worker({
        store,
        now: () => new Date(now),
        engine: { score: async ({ calculationSpec, events }) => v5EngineResult(calculationSpec, events) },
      });
      const userId = randomUUID();
      const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
      const queued = await service.answer({
        userId, caseId: created.case.id, actionId: randomUUID(), expectedCaseVersion: created.case.version,
        answer: "2016年9月大学入学",
      });
      assert.ok(queued?.job);
      await worker.runOnce();
      const loaded = await service.loadCase(userId, created.case.id);
      return {
        message: [...store.publicMessages.values()][0],
        question: loaded?.case.currentQuestion,
        analysis: loaded?.analysis ?? [],
        agentRuns: store.agentRuns.size,
      };
    });
  }
  const legacy = await run("v4_legacy");
  const shadow = await run("v5_shadow");
  const visibleMessage = (message: NonNullable<typeof legacy.message>) => ({
    acknowledgement: message.acknowledgement,
    candidateUpdate: message.candidateUpdate,
    limitation: message.limitation,
    question: message.question,
  });
  assert.deepEqual(visibleMessage(shadow.message!), visibleMessage(legacy.message!));
  assert.equal(shadow.question?.prompt, legacy.question?.prompt);
  assert.deepEqual(legacy.analysis, []);
  assert.deepEqual(shadow.analysis, []);
  assert.equal(shadow.agentRuns, 1);
});

test("V6 agent conversation follows dated events, respects direction change, and runs the existing V5 engine", async () => {
  await withV5Mode("v5_agent", async () => {
    const store = createRectificationV4MemoryStore();
    const service = createTestCaseService(store, { now: () => new Date("2026-07-29T00:00:00.000Z") });
    let scoreCalls = 0;
    const worker = createRectificationV4Worker({
      store,
      now: () => new Date("2026-07-29T00:00:00.000Z"),
      engine: { score: async ({ calculationSpec, events }) => {
        scoreCalls += 1;
        return v5EngineResult(calculationSpec, events);
      } },
    });
    const userId = randomUUID();
    const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });

    async function answer(value: string) {
      const current = await service.loadCase(userId, created.case.id);
      assert.ok(current?.case.currentQuestion);
      const queued = await service.answer({
        userId,
        caseId: created.case.id,
        actionId: randomUUID(),
        expectedCaseVersion: current.case.version,
        answer: value,
      });
      assert.ok(queued?.job);
      assert.equal(await worker.runOnce(), true);
      const loaded = await service.loadCase(userId, created.case.id);
      assert.ok(loaded);
      return loaded;
    }

    const first = await answer("2020 年 4 月去石油化工研究院实习做研究员。");
    const firstEvent = first.events.find((event) => event.summary.includes("石油化工研究院实习做研究员"));
    assert.deepEqual(
      firstEvent && [firstEvent.domain, firstEvent.subject, firstEvent.dateRange.precision, firstEvent.scoreability],
      ["career", "self", "month", "scoreable"],
    );
    assert.doesNotMatch(first.case.currentQuestion?.prompt ?? "", /哪一天|几号|具体日期/);
    const firstMessage = [...store.publicMessages.values()].at(-1);
    assert.doesNotMatch(firstMessage?.acknowledgement ?? "", /已记录|我记下了|职业方向正式落地/);
    assert.match(firstMessage?.acknowledgement ?? "", /研究院实习/);

    const second = await answer("2016 年 9 月离家去外地上大学。");
    assert.ok(second.events.some((event) => event.domain === "education" && event.dateRange.precision === "month"));
    assert.doesNotMatch(second.case.currentQuestion?.prompt ?? "", /^请说一次搬家/);
    assert.ok(!second.case.currentQuestion?.targetEventId || /离家去外地上大学/.test(second.case.currentQuestion.prompt));

    const pendingBefore = store.pendingEvidence.size;
    const third = await answer("后来有一次搬家，但我记不清时间了，换一个吧。");
    assert.equal(store.pendingEvidence.size, pendingBefore);
    assert.equal(third.events.filter((event) => event.domain === "relocation").length, 0);
    assert.doesNotMatch(third.case.currentQuestion?.prompt ?? "", /搬家.*(?:时间|日期|月份)|(?:时间|日期|月份).*搬家/);

    const fourth = await answer("2023 年 9 月开始负责一家商业巡演经纪公司。");
    assert.ok(fourth.events.some((event) => event.domain === "career" && event.summary.includes("商业巡演经纪公司")));
    assert.equal(scoreCalls, 1);
    assert.ok(store.diagnostics.size > 0);
    assert.equal(fourth.case.latestSnapshot?.robustness.leaveOneDomainOutRetentionRate, 1);
    assert.equal(fourth.case.latestSnapshot?.canConfirmExactMinute, false);
    assert.equal(fourth.case.algorithmVersion, "rectification-v5-matrix-scoring-2");
    const finalMessage = [...store.publicMessages.values()].at(-1);
    assert.doesNotMatch(`${finalMessage?.candidateUpdate ?? ""}${finalMessage?.limitation ?? ""}`, /唯一分钟|准确分钟|代表分钟|05:13/);
  });
});
