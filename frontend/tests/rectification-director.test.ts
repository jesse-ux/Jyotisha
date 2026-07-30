import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";

import { diagnosticsSummarySchema, type RectificationTurnPlan } from "../src/lib/rectification-agent/contracts.ts";
import { buildRectificationCaseDossier, regenerateDirectorQuestion, runRectificationDirector, validateRectificationTurnPlan } from "../src/lib/rectification-agent/director-agent.ts";
import type { CalculationSpec, LifeEventRevision, PendingEvidence, RectificationV4Case, RectificationV4Turn } from "../src/lib/rectification-v4/contracts.ts";
import { stageAgentEvidenceProposals } from "../src/lib/rectification-v4/extraction.ts";
import { calculationSpecHash } from "../src/lib/rectification-v4/fingerprints.ts";

const now = "2026-07-30T00:00:00.000Z";
const caseId = "00000000-0000-4000-8000-000000000701";
const spec: CalculationSpec = {
  version: "rectification-calculation-spec-v4",
  birthDate: "1993-04-17",
  candidateRange: { start: "05:00", end: "06:00" },
  latitude: 36.683333,
  longitude: 114.35,
  timezoneId: "Asia/Shanghai",
  timezoneOffsetHours: 8,
  birthTimeSource: "approximate",
  ayanamsa: "lahiri",
  nodeMode: "mean",
  minuteStep: 1,
};
const caseValue: RectificationV4Case = {
  id: caseId,
  userId: "00000000-0000-4000-8000-000000000702",
  protocol: "rectification-evidence-v5",
  version: 3,
  status: "processing",
  phase: "reasoning",
  calculationSpec: spec,
  calculationSpecHash: calculationSpecHash(spec),
  evidenceSetHash: "e".repeat(64),
  currentQuestion: null,
  latestSnapshot: null,
  orchestrationModelId: null,
  narrationModelId: null,
  skillVersion: "birth-time-rectification-v6",
  promptVersion: "rectification-director-v1",
  algorithmVersion: "rectification-v5-matrix-scoring-1",
  deploymentMode: "v5_agent",
  agentMode: "agent",
  featureSnapshotId: null,
  latestDiagnosticsId: null,
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
    summary: "2016年9月大学入学",
    rawText: "2016年9月大学入学",
    dateRange: { start: "2016-09-01", end: "2016-09-30", precision: "month", label: "2016年9月" },
    scoreability: "scoreable",
    supersedesRevisionId: null,
    createdAt: now,
    ...overrides,
  };
}

function turn(index: number, overrides: Partial<RectificationV4Turn> = {}): RectificationV4Turn {
  return {
    id: randomUUID(),
    caseId,
    caseVersion: index + 1,
    questionId: null,
    questionDomain: null,
    questionTargetEventId: null,
    question: `问题${index}`,
    answer: `回答${index}`,
    modelId: null,
    actionId: randomUUID(),
    createdAt: now,
    ...overrides,
  };
}

function plan(overrides: Partial<RectificationTurnPlan> = {}): RectificationTurnPlan {
  return {
    contractVersion: "rectification-turn-plan-v1",
    targetDisposition: "not_applicable",
    evidenceProposals: [],
    action: {
      type: "ask_question",
      focus: {
        mode: "collect_independent_event",
        targetEventId: null,
        domain: null,
        requestedFacts: ["independent_event"],
        rationaleCodes: ["need_independent_event"],
      },
      question: "接下来想从哪段变化继续聊？",
      optionalQuickReplies: [],
    },
    publicReply: {
      acknowledgement: "我已按你的描述整理这轮线索。",
      candidateCommentary: null,
      limitation: "目前仍不足以确认具体出生分钟。",
    },
    ...overrides,
  };
}

function dossier(events: readonly LifeEventRevision[] = [], turns: readonly RectificationV4Turn[] = [], pendingEvidence: readonly PendingEvidence[] = []) {
  return buildRectificationCaseDossier({
    caseValue,
    turns,
    events,
    pendingEvidence,
    snapshot: null,
    diagnostics: null,
    targetDisposition: "not_applicable",
    currentTargetEventId: null,
  });
}

const diagnostics = diagnosticsSummarySchema.parse({
  id: "00000000-0000-4000-8000-000000000703",
  caseId,
  snapshotId: "00000000-0000-4000-8000-000000000704",
  primaryClusterRetentionRate: 0.8,
  leaveOneEventOutRetentionRate: 0.8,
  leaveOneDomainOutRetentionRate: 0.8,
  dateSensitivityRetentionRate: 0.8,
  neighborSupportMinutes: 3,
  primarySecondaryMarginPercent: 8,
  clusterMassRatio: 0.6,
  unstableEventIds: [],
  mostDiscriminatingLayers: ["D9"],
  eventDateSensitivity: [],
  candidateSplits: [],
  calculationHash: "d".repeat(64),
  createdAt: now,
});

test("dossier keeps recent raw turns, useful earlier context, refusals, pending evidence, and the complete revision ledger", () => {
  const sharedEventId = randomUUID();
  const events = Array.from({ length: 15 }, (_, index) => event({
    eventId: index < 2 ? sharedEventId : randomUUID(),
    revision: index < 2 ? index + 1 : 1,
    supersedesRevisionId: index === 1 ? randomUUID() : null,
    summary: `事件${index}`,
    rawText: `事件${index}`,
  }));
  const targetEventId = events.at(-1)!.eventId;
  const turns = Array.from({ length: 14 }, (_, index) => turn(index));
  turns[1] = turn(1, { questionDomain: "relationship", questionTargetEventId: targetEventId, answer: "这件事不方便说，换个方向。" });
  const pending: PendingEvidence = {
    id: randomUUID(), caseId, turnId: turns[0]!.id, rawText: "后来搬过一次家", reasonCode: "date_unresolved",
    targetEventId, resolvedEventId: null, createdAt: now, resolvedAt: null,
  };
  const value = dossier(events, turns, [pending]);
  assert.equal(value.conversation.recentRawTurns.length, 12);
  assert.equal(value.conversation.recentRawTurns[0]?.question, "问题2");
  assert.match(value.conversation.earlierConversationSummary ?? "", /问题0/);
  assert.match(value.conversation.earlierConversationSummary ?? "", /不方便说/);
  assert.deepEqual(value.interviewState.declinedDomains, ["relationship"]);
  assert.equal(value.interviewState.pendingEvidence[0]?.reasonCode, "date_unresolved");
  assert.equal(value.interviewState.pendingEvidence[0]?.targetEventId, targetEventId);
  assert.equal(value.eventLedger.length, 15);
  assert.equal(value.eventLedger[0]?.status, "superseded");
  assert.equal(value.eventLedger[1]?.status, "active");
  assert.equal(value.case.location.timezoneId, "Asia/Shanghai");
});

test("a natural question and multiple grounded event proposals pass without domain keywords or anchors", () => {
  const latestAnswer = "2018年9月搬到北京，2020年4月开始第一份工作。";
  const value = plan({
    evidenceProposals: [
      { operation: "create", targetEventId: null, sourceSpan: "2018年9月搬到北京", dateText: "2018年9月", proposedSummary: "搬到北京", proposedDomain: "relocation", proposedEventKind: "relocation", proposedSubject: "self", proposedRelatedPerson: null, confidence: "high" },
      { operation: "create", targetEventId: null, sourceSpan: "2020年4月开始第一份工作", dateText: "2020年4月", proposedSummary: "开始第一份工作", proposedDomain: "career", proposedEventKind: "career_change", proposedSubject: "self", proposedRelatedPerson: null, confidence: "high" },
    ],
  });
  assert.deepEqual(validateRectificationTurnPlan({ plan: value, dossier: dossier(), latestAnswer, phase: "evidence" }).issues, []);
  const staged = stageAgentEvidenceProposals({ caseId, rawText: latestAnswer, sourceTurnId: randomUUID(), asOfDate: "2026-07-30", existing: [], proposals: value.evidenceProposals, now: new Date(now) });
  assert.equal(staged.revisions.length, 2);
  assert.deepEqual(new Set(staged.revisions.map((item) => item.domain)), new Set(["relocation", "career"]));
});

test("server rejects invented sources, private details, exact minutes, and ungated ranges", () => {
  const latestAnswer = "2018年9月搬到北京。";
  const invented = plan({ evidenceProposals: [{ operation: "create", targetEventId: null, sourceSpan: "2020年工作", dateText: "2020年", proposedSummary: "开始工作", proposedDomain: "career", proposedEventKind: "career_change", proposedSubject: "self", proposedRelatedPerson: null, confidence: "low" }] });
  assert.ok(validateRectificationTurnPlan({ plan: invented, dossier: dossier(), latestAnswer, phase: "evidence" }).issues.includes("evidence_source_not_in_latest_answer"));

  const unsafe = plan({ publicReply: { acknowledgement: "内部 eventId 是 00000000-0000-4000-8000-000000000799。", candidateCommentary: "出生时间是05:13。", limitation: null } });
  const unsafeIssues = validateRectificationTurnPlan({ plan: unsafe, dossier: dossier(), latestAnswer, phase: "final" }).issues;
  assert.ok(unsafeIssues.includes("private_detail_exposed"));
  assert.ok(unsafeIssues.includes("exact_minute_claimed"));

  const range = plan({ action: { type: "offer_candidate_range", snapshotId: "00000000-0000-4000-8000-000000000704" } });
  assert.ok(validateRectificationTurnPlan({ plan: range, dossier: dossier(), latestAnswer, phase: "final" }).issues.includes("candidate_range_gate_failed"));
});

test("revisions keep the server-owned event id and append revision history", () => {
  const target = event({ eventId: "00000000-0000-4000-8000-000000000705" });
  const rawText = "其实是2016年10月大学入学。";
  const staged = stageAgentEvidenceProposals({
    caseId,
    rawText,
    sourceTurnId: randomUUID(),
    asOfDate: "2026-07-30",
    existing: [target],
    proposals: [{ operation: "revise", targetEventId: target.eventId, sourceSpan: "2016年10月大学入学", dateText: "2016年10月", proposedSummary: "2016年10月大学入学", proposedDomain: "education", proposedEventKind: "education_milestone", proposedSubject: "self", proposedRelatedPerson: null, confidence: "high" }],
    now: new Date(now),
  });
  assert.equal(staged.revisions.length, 1);
  assert.equal(staged.revisions[0]?.eventId, target.eventId);
  assert.equal(staged.revisions[0]?.revision, 2);
  assert.equal(staged.revisions[0]?.dateRange.start, "2016-10-01");
  assert.equal(staged.revisions[0]?.dateRange.end, "2016-10-31");
  assert.equal(staged.revisions[0]?.summary, "大学入学");
});

test("revisions cannot replace an existing event with unrelated model content", () => {
  const target = event({ eventId: "00000000-0000-4000-8000-000000000708" });
  const rawText = "2018年9月搬到北京。";
  const staged = stageAgentEvidenceProposals({
    caseId,
    rawText,
    sourceTurnId: randomUUID(),
    asOfDate: "2026-07-30",
    existing: [target],
    proposals: [{ operation: "revise", targetEventId: target.eventId, sourceSpan: "2018年9月搬到北京", dateText: "2018年9月", proposedSummary: "2018年9月创办公司", proposedDomain: "relocation", proposedEventKind: "relocation", proposedSubject: "self", proposedRelatedPerson: null, confidence: "high" }],
    now: new Date(now),
  });
  assert.equal(staged.revisions.length, 0);
  assert.equal(staged.pending.length, 1);
  assert.equal(staged.pending[0]?.targetEventId, target.eventId);
});

test("declined targets cannot be reopened and diagnostics stay in a bounded tool loop", async () => {
  const target = event({ eventId: "00000000-0000-4000-8000-000000000706" });
  const targetDossier = buildRectificationCaseDossier({ caseValue, turns: [], events: [target], snapshot: null, diagnostics: null, targetDisposition: "declined", currentTargetEventId: target.eventId });
  const reopened = plan({ targetDisposition: "declined", action: { type: "ask_question", focus: { mode: "clarify_existing_event", targetEventId: target.eventId, domain: target.domain, requestedFacts: ["month"], rationaleCodes: ["retry"] }, question: "再说说那件事？", optionalQuickReplies: [] } });
  assert.ok(validateRectificationTurnPlan({ plan: reopened, dossier: targetDossier, latestAnswer: "不想说", phase: "final" }).issues.includes("declined_target_reopened"));

  const phases: string[] = [];
  const prompts: string[] = [];
  const result = await runRectificationDirector({
    caseValue,
    dossier: dossier(),
    latestAnswer: "",
    phase: "final",
    diagnostics,
    generatePlan: async (prompt, phase) => {
      phases.push(phase);
      prompts.push(prompt);
      return { object: phases.length <= 2 ? plan({ action: { type: "request_diagnostic", diagnostic: phases.length === 1 ? "candidate_split" : "date_sensitivity" } }) : plan() };
    },
  });
  assert.equal(result.mode, "agent");
  assert.deepEqual(phases, ["final", "after_diagnostic", "after_diagnostic"]);
  assert.equal(result.toolCalls.length, 2);
  assert.deepEqual(JSON.parse(prompts[2]!).diagnosticResults.map((item: { diagnostic: string }) => item.diagnostic), ["candidate_split", "date_sensitivity"]);
  assert.equal(result.plan.action.type, "ask_question");
});

test("the same Director gets one repair attempt before deterministic fallback", async () => {
  const phases: string[] = [];
  const result = await runRectificationDirector({
    caseValue,
    dossier: dossier(),
    latestAnswer: "2018年9月搬到北京。",
    phase: "evidence",
    diagnostics,
    generatePlan: async (_prompt, phase) => {
      phases.push(phase);
      return { object: phase === "repair" ? plan() : plan({ evidenceProposals: [{ operation: "create", targetEventId: null, sourceSpan: "不存在的内容", dateText: "2020年", proposedSummary: "开始工作", proposedDomain: "career", proposedEventKind: "career_change", proposedSubject: "self", proposedRelatedPerson: null, confidence: "low" }] }) };
    },
  });
  assert.equal(result.mode, "agent");
  assert.deepEqual(phases, ["evidence", "repair"]);
  assert.equal(result.fallbackReason, null);
});


test("manual question regeneration preserves focus and repairs unsafe text once", async () => {
  const phases: string[] = [];
  const question = await regenerateDirectorQuestion({
    caseValue,
    currentQuestion: "除了这段经历，你还想从哪件事继续？",
    latestAnswer: "2016年9月大学入学",
    acceptedEvents: [event()],
    focus: {
      mode: "collect_independent_event",
      targetEventId: null,
      domain: null,
      requestedFacts: ["independent_event"],
      rationaleCodes: ["need_independent_event"],
    },
    generateQuestion: async (_prompt, phase) => {
      phases.push(phase);
      return { object: { question: phase === "regenerate" ? "请确认出生时间05:13？" : "除了这段经历，你还想从哪件事继续？" } };
    },
  });
  assert.equal(question, "除了这段经历，你还想从哪件事继续？");
  assert.deepEqual(phases, ["regenerate", "repair"]);
});
