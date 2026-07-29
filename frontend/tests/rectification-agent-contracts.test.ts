import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  validateRectificationDecision,
  type DiagnosticsSummary,
  type QuestionOpportunity,
} from "../src/lib/rectification-agent/contracts.ts";
import { recordRectificationAgentTelemetry } from "../src/lib/rectification-agent/telemetry.ts";

const caseId = "00000000-0000-4000-8000-000000000800";
const opportunityId = "00000000-0000-4000-8000-000000000801";
const snapshotId = "00000000-0000-4000-8000-000000000802";
const diagnostics: DiagnosticsSummary = {
  id: "00000000-0000-4000-8000-000000000803",
  caseId,
  snapshotId,
  primaryClusterRetentionRate: 0.8,
  leaveOneEventOutRetentionRate: 0.75,
  leaveOneDomainOutRetentionRate: 0.7,
  dateSensitivityRetentionRate: 0.72,
  neighborSupportMinutes: 8,
  primarySecondaryMarginPercent: 12,
  clusterMassRatio: 0.65,
  unstableEventIds: [],
  mostDiscriminatingLayers: ["D9"],
  eventDateSensitivity: [],
  candidateSplits: [],
  calculationHash: "c".repeat(64),
  createdAt: "2026-07-28T00:00:00.000Z",
};
const opportunity: QuestionOpportunity = {
  contractVersion: "semantic-question-v2",
  opportunityId,
  kind: "ask_new_event",
  domain: "career",
  targetEventId: null,
  goal: "收集一件有大致日期的职业转折。",
  requestedFields: ["new_dated_event"],
  anchors: [],
  contextFacts: ["职业领域尚未覆盖。"],
  forbiddenMoves: ["switch_target_event", "ask_multiple_questions", "claim_exact_birth_minute", "invent_event", "invent_date", "expose_private_score", "expose_internal_id", "expose_technique_trace"],
  fallbackPrompt: "请说一件时间比较明确的职业变化经历。",
  reason: "当前证据领域覆盖不足。",
  expectedInformationGain: 0.8,
  dateSensitivity: 0.5,
  candidateSplitRelevance: 0.7,
  domainCoverageGain: 0.6,
  recallEase: 0.8,
  novelty: 1,
  repetitionPenalty: 0,
  privacyCost: 0.1,
  utility: 0.69,
  active: true,
};

function validate(decision: unknown, overrides: Partial<Parameters<typeof validateRectificationDecision>[0]> = {}) {
  return validateRectificationDecision({
    decision,
    caseId,
    snapshotId,
    opportunities: [opportunity],
    diagnostics,
    candidateRangeOfferAllowed: true,
    ...overrides,
  });
}

test("only an active server-owned opportunity can be selected", () => {
  assert.deepEqual(validate({
    action: "ask_question", opportunityId, narrativeFocus: ["latest_event"],
  }, { opportunities: [{ ...opportunity, active: false }] }).issues, ["opportunity_not_active"]);
  assert.deepEqual(validate({
    action: "ask_question", opportunityId: "00000000-0000-4000-8000-000000000899", narrativeFocus: [],
  }).issues, ["opportunity_not_active"]);
});

test("candidate ranges require both the policy gate and the current snapshot", () => {
  assert.deepEqual(validate({ action: "offer_candidate_range", snapshotId }, {
    candidateRangeOfferAllowed: false,
  }).issues, ["candidate_range_gate_failed"]);
  assert.deepEqual(validate({ action: "offer_candidate_range", snapshotId }, {
    snapshotId: "00000000-0000-4000-8000-000000000898",
  }).issues, ["snapshot_not_current"]);
});

test("diagnostic reads are bounded and cannot target another case", () => {
  assert.deepEqual(validate({ action: "run_diagnostic", diagnostic: "neighbor_stability" }, {
    usedDiagnostics: ["neighbor_stability"],
  }).issues, ["diagnostic_already_run"]);
  assert.deepEqual(validate({ action: "ask_question", opportunityId, narrativeFocus: [] }, {
    caseId: "00000000-0000-4000-8000-000000000897",
    toolCallCount: 2,
    maxToolCalls: 1,
  }).issues, ["diagnostics_case_mismatch", "tool_call_budget_exceeded"]);
});

test("model output cannot inject a minute, question, event, or score", () => {
  for (const extra of [
    { birthMinute: "06:21" },
    { prompt: "模型自己写的问题" },
    { eventId: "00000000-0000-4000-8000-000000000896" },
    { score: 99 },
  ]) {
    assert.deepEqual(validate({ action: "offer_candidate_range", snapshotId, ...extra }).issues, ["decision_schema_invalid"]);
  }
});

test("agent telemetry rejects malformed events and warns on failures", () => {
  const info: string[] = [];
  const warnings: string[] = [];
  const originalInfo = console.info;
  const originalWarn = console.warn;
  console.info = (message) => info.push(String(message));
  console.warn = (message) => warnings.push(String(message));
  try {
    recordRectificationAgentTelemetry({
      caseId, phase: "reasoner", outcome: "failed", modelId: "test-model", toolName: null,
      decisionAction: null, durationMs: 12, errorCode: "model_unavailable", deploymentSha: "test-sha",
    });
    recordRectificationAgentTelemetry({
      caseId, phase: "reasoner", outcome: "failed", modelId: "", toolName: null,
      decisionAction: null, durationMs: 12, errorCode: "model_unavailable", deploymentSha: "test-sha",
    });
  } finally {
    console.info = originalInfo;
    console.warn = originalWarn;
  }
  assert.equal(info.length, 0);
  assert.equal(warnings.length, 1);
  assert.match(warnings[0] ?? "", /\[rectification-agent\].*"outcome":"failed"/);
});

test("durable event semantics migration validates and persists subject fields", () => {
  const migration = readFileSync(new URL(
    "../supabase/migrations/20260728010000_conversational_event_semantics.sql",
    import.meta.url,
  ), "utf8");
  assert.match(migration, /subject in \('self', 'family', 'partner', 'other'\)/);
  assert.match(migration, /related_person/);
  assert.match(migration, /save_conversational_rectification_turn/);
  assert.match(migration, /import_legacy_conversational_rectification_case/);
  assert.match(migration, /event_kind/);
  assert.match(migration, /scoreability/);
});
