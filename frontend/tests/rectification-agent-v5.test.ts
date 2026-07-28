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
import { enforceServerQuestion } from "../src/lib/rectification-agent/renderer-agent.ts";
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

const caseId = "00000000-0000-4000-8000-000000000901";
const snapshotId = "00000000-0000-4000-8000-000000000902";
const opportunityId = "00000000-0000-4000-8000-000000000903";
const now = "2026-07-28T00:00:00.000Z";

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
  robustness: { neighborSupportMinutes: 3, leaveOneOutRetentionRate: 1, dateSensitivityRetentionRate: 1, calculationSpecHashMatched: true },
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
  opportunityId,
  kind: "ask_new_event",
  domain: "career",
  targetEventId: null,
  prompt: "请补充一次职业变化。",
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

test("opportunities are ordered only by their published utility", () => {
  const target = event();
  const values = buildQuestionOpportunities({
    caseId,
    events: [target],
    turns: [],
    snapshot: null,
    diagnostics: null,
  });
  assert.ok(values.length >= 2);
  assert.deepEqual(values.map((value) => value.utility), [...values].map((value) => value.utility).sort((a, b) => b - a));
});

test("an unresolved current target exclusively owns the next-question route", () => {
  const target = event();
  const values = buildQuestionOpportunities({
    caseId,
    events: [target, event({ eventId: randomUUID(), domain: "relocation", eventKind: "relocation", summary: "搬家到北京" })],
    turns: [],
    snapshot: null,
    diagnostics: null,
    retryTargetEventIds: [target.eventId],
  });
  assert.deepEqual(values.map((value) => [value.kind, value.targetEventId]), [["resolve_event_conflict", target.eventId]]);
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

test("renderer cannot replace the server-owned question", () => {
  assert.deepEqual(enforceServerQuestion({
    acknowledgement: "已记录。",
    candidateUpdate: null,
    limitation: null,
    question: "模型注入的问题",
  }, "服务器选定的问题"), {
    acknowledgement: "已记录。",
    candidateUpdate: null,
    limitation: null,
    question: "服务器选定的问题",
  });
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
    retryTargetEventIds: [target.eventId],
  });
  assert.equal(opportunities[0]?.kind, "resolve_event_conflict");
  assert.equal(opportunities[0]?.targetEventId, target.eventId);
});

test("unparsed answers are retained as pending evidence", () => {
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
  assert.equal(reconciled.pending.length, 1);
  assert.equal(reconciled.pending[0]?.turnId, turnId);
  assert.equal(reconciled.pending[0]?.targetEventId, target.eventId);
});

test("shadow mode persists V5 artifacts while preserving the legacy visible reply", async () => {
  async function run(mode: "v4_legacy" | "v5_shadow") {
    return withV5Mode(mode, async () => {
      const store = createRectificationV4MemoryStore();
      const service = createRectificationV4CaseService(store, { now: () => new Date(now) });
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
      return {
        message: [...store.publicMessages.values()][0],
        question: (await service.loadCase(userId, created.case.id))?.case.currentQuestion,
        agentRuns: store.agentRuns.size,
      };
    });
  }
  const legacy = await run("v4_legacy");
  const shadow = await run("v5_shadow");
  assert.deepEqual(shadow.message, legacy.message);
  assert.equal(shadow.question?.prompt, legacy.question?.prompt);
  assert.equal(shadow.agentRuns, 1);
});
