import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";

import { diagnosticsSummarySchema, type RectificationTurnPlan } from "../src/lib/rectification-agent/contracts.ts";
import { buildRectificationCaseDossier, regenerateDirectorQuestion, runRectificationDirector, validateRectificationTurnPlan } from "../src/lib/rectification-agent/director-agent.ts";
import { composeRectificationPublicTurn, mergeDirectorReconciliation } from "../src/lib/rectification-agent/orchestrator.ts";
import type { CalculationSpec, CandidateSnapshot, LifeEventRevision, PendingEvidence, RectificationV4Case, RectificationV4Turn } from "../src/lib/rectification-v4/contracts.ts";
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
  skillVersion: "birth-time-rectification-v8",
  promptVersion: "rectification-director-v4",
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
      question: "你愿意从哪段变化继续聊？",
      optionalQuickReplies: [],
    },
    publicReply: {
      acknowledgement: "我已按你的描述整理这轮线索。",
      evidenceExplanation: null,
      candidateCommentary: null,
      limitation: "目前仍不足以确认具体出生分钟。",
    },
    publicExplanationGrounding: [],
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

test("a declined domain is a server-owned boundary, not a keyword rule", () => {
  const turns = [turn(0, {
    questionDomain: "relationship",
    question: "如果你愿意，可以聊聊一段关系变化吗？",
    answer: "不想回答，换个方向。",
  })];
  const value = dossier([], turns);
  assert.deepEqual(value.interviewState.declinedDomains, ["relationship"]);

  const reopened = plan({
    action: {
      type: "ask_question",
      focus: {
        mode: "collect_independent_event",
        targetEventId: null,
        domain: "relationship",
        requestedFacts: ["independent_event"],
        rationaleCodes: ["agent_selected_direction"],
      },
      question: "有没有一段关系状态变化的经历？",
      optionalQuickReplies: [],
    },
  });
  assert.ok(validateRectificationTurnPlan({
    plan: reopened,
    dossier: value,
    latestAnswer: turns[0]!.answer,
    phase: "final",
  }).issues.includes("declined_domain_reopened"));

  const changedDirection = plan({
    action: {
      type: "ask_question",
      focus: {
        mode: "collect_independent_event",
        targetEventId: null,
        domain: null,
        requestedFacts: ["independent_event"],
        rationaleCodes: ["agent_selected_direction"],
      },
      question: "你愿意从另一段时间大致明确的经历继续吗？",
      optionalQuickReplies: [],
    },
  });
  assert.deepEqual(validateRectificationTurnPlan({
    plan: changedDirection,
    dossier: value,
    latestAnswer: turns[0]!.answer,
    phase: "final",
  }).issues, []);
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

  const unsafe = plan({
    action: { type: "ask_question", focus: { mode: "collect_independent_event", targetEventId: null, domain: null, requestedFacts: ["independent_event"], rationaleCodes: ["test"] }, question: "内部 eventId 是 00000000-0000-4000-8000-000000000799，出生时间是05:13吗？", optionalQuickReplies: [] },
  });
  const unsafeResult = validateRectificationTurnPlan({ plan: unsafe, dossier: dossier(), latestAnswer, phase: "final" });
  assert.deepEqual(unsafeResult.issues, []);
  assert.doesNotMatch(unsafeResult.plan?.action.type === "ask_question" ? unsafeResult.plan.action.question : "", /eventId|05:13|出生时间/);

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
    proposals: [{ operation: "revise_date", targetEventId: target.eventId, sourceSpan: "2016年10月", dateText: "2016年10月", proposedSummary: "2016年10月大学入学", proposedDomain: "education", proposedEventKind: "education_milestone", proposedSubject: "self", proposedRelatedPerson: null, confidence: "high" }],
    now: new Date(now),
  });
  assert.equal(staged.revisions.length, 1);
  assert.equal(staged.revisions[0]?.eventId, target.eventId);
  assert.equal(staged.revisions[0]?.revision, 2);
  assert.equal(staged.revisions[0]?.dateRange.start, "2016-10-01");
  assert.equal(staged.revisions[0]?.dateRange.end, "2016-10-31");
  assert.equal(staged.revisions[0]?.summary, target.summary);
});

test("date revisions ignore model attempts to replace event identity", () => {
  const target = event({ eventId: "00000000-0000-4000-8000-000000000708" });
  const rawText = "2018年9月搬到北京。";
  const staged = stageAgentEvidenceProposals({
    caseId,
    rawText,
    sourceTurnId: randomUUID(),
    asOfDate: "2026-07-30",
    existing: [target],
    proposals: [{ operation: "revise_date", targetEventId: target.eventId, sourceSpan: "2018年9月", dateText: "2018年9月", proposedSummary: "2018年9月创办公司", proposedDomain: "relocation", proposedEventKind: "relocation", proposedSubject: "self", proposedRelatedPerson: null, confidence: "high" }],
    now: new Date(now),
  });
  assert.equal(staged.revisions.length, 1);
  assert.equal(staged.pending.length, 0);
  assert.equal(staged.revisions[0]?.eventId, target.eventId);
  assert.equal(staged.revisions[0]?.domain, target.domain);
  assert.equal(staged.revisions[0]?.eventKind, target.eventKind);
  assert.equal(staged.revisions[0]?.subject, target.subject);
  assert.equal(staged.revisions[0]?.summary, target.summary);
});


test("server-closed target dispositions cannot be overwritten by the Director", () => {
  const target = event();
  const pending: PendingEvidence = {
    id: randomUUID(), caseId, turnId: randomUUID(), rawText: "不想说了，换一个。", reasonCode: "event_unparsed",
    targetEventId: target.eventId, resolvedEventId: null, createdAt: now, resolvedAt: null,
  };
  for (const targetDisposition of ["unknown", "declined", "direction_change"] as const) {
    const merged = mergeDirectorReconciliation({
      server: { revisions: [], pending: [], unansweredTargetEventId: null, targetDisposition },
      staged: { revisions: [], pending: [pending], unansweredTargetEventId: target.eventId, targetDisposition: "unresolved" },
      proposedDisposition: "unresolved",
      currentTargetEventId: target.eventId,
    });
    assert.equal(merged.targetDisposition, targetDisposition);
    assert.equal(merged.unansweredTargetEventId, null);
    assert.deepEqual(merged.pending, []);
  }
});

test("target date-only replies inherit identity and missing year", () => {
  const target = event();
  const cases = [
    ["2020年4月", "2020-04-01", "2020-04-30"],
    ["4月", "2016-04-01", "2016-04-30"],
    ["8月8号", "2016-08-08", "2016-08-08"],
    ["上半年", "2016-01-01", "2016-06-30"],
    ["10月至12月", "2016-10-01", "2016-12-31"],
  ] as const;
  for (const [rawText, start, end] of cases) {
    const staged = stageAgentEvidenceProposals({
      caseId, rawText, sourceTurnId: randomUUID(), asOfDate: "2026-07-30", existing: [target],
      proposals: [{ operation: "revise_date", targetEventId: target.eventId, sourceSpan: rawText, dateText: rawText, proposedSummary: "模型不得改写", proposedDomain: "other", proposedEventKind: "other", proposedSubject: "family", proposedRelatedPerson: "mother", confidence: "high" }],
      now: new Date(now),
    });
    assert.equal(staged.pending.length, 0, rawText);
    assert.equal(staged.revisions.length, 1, rawText);
    assert.equal(staged.revisions[0]?.eventId, target.eventId, rawText);
    assert.equal(staged.revisions[0]?.domain, target.domain, rawText);
    assert.equal(staged.revisions[0]?.eventKind, target.eventKind, rawText);
    assert.equal(staged.revisions[0]?.subject, target.subject, rawText);
    assert.equal(staged.revisions[0]?.summary, target.summary, rawText);
    assert.equal(staged.revisions[0]?.dateRange.start, start, rawText);
    assert.equal(staged.revisions[0]?.dateRange.end, end, rawText);
  }
});

test("explicit event-kind correction appends a revision to the same event", () => {
  const target = event({ domain: "relationship", eventKind: "relationship_start", subject: "self", relatedPerson: "partner", summary: "关系开始", rawText: "2020年关系开始" });
  const rawText = "不是关系开始，是分手";
  const staged = stageAgentEvidenceProposals({
    caseId, rawText, sourceTurnId: randomUUID(), asOfDate: "2026-07-30", existing: [target],
    proposals: [{ operation: "reclassify", targetEventId: target.eventId, sourceSpan: rawText, dateText: null, proposedSummary: "分手", proposedDomain: "relationship", proposedEventKind: "relationship_end", proposedSubject: "self", proposedRelatedPerson: "partner", confidence: "high" }],
    now: new Date(now),
  });
  assert.equal(staged.pending.length, 0);
  assert.equal(staged.revisions[0]?.eventId, target.eventId);
  assert.equal(staged.revisions[0]?.revision, 2);
  assert.equal(staged.revisions[0]?.eventKind, "relationship_end");
});

test("explicit subject correction is grounded and enters pending review", () => {
  const target = event({ domain: "health_pressure", eventKind: "self_health_event", subject: "self", relatedPerson: null, summary: "手术", rawText: "2020年我做了手术" });
  const rawText = "这次是母亲手术，不是我";
  const staged = stageAgentEvidenceProposals({
    caseId, rawText, sourceTurnId: randomUUID(), asOfDate: "2026-07-30", existing: [target],
    proposals: [{ operation: "reclassify", targetEventId: target.eventId, sourceSpan: rawText, dateText: null, proposedSummary: "母亲手术", proposedDomain: "family", proposedEventKind: "family_health_event", proposedSubject: "family", proposedRelatedPerson: "mother", confidence: "high" }],
    now: new Date(now),
  });
  assert.equal(staged.pending.length, 0);
  assert.equal(staged.revisions[0]?.eventId, target.eventId);
  assert.equal(staged.revisions[0]?.subject, "family");
  assert.equal(staged.revisions[0]?.relatedPerson, "mother");
  assert.equal(staged.revisions[0]?.scoreability, "pending_review");
});

test("declined targets cannot be reopened and the Director adapts through server-owned observations", async () => {
  const target = event({ eventId: "00000000-0000-4000-8000-000000000706" });
  const targetDossier = buildRectificationCaseDossier({ caseValue, turns: [], events: [target], snapshot: null, diagnostics: null, targetDisposition: "declined", currentTargetEventId: target.eventId });
  const reopened = plan({ targetDisposition: "declined", action: { type: "ask_question", focus: { mode: "clarify_existing_event", targetEventId: target.eventId, domain: target.domain, requestedFacts: ["month"], rationaleCodes: ["retry"] }, question: "再说说那件事？", optionalQuickReplies: [] } });
  assert.ok(validateRectificationTurnPlan({ plan: reopened, dossier: targetDossier, latestAnswer: "不想说", phase: "final" }).issues.includes("declined_target_reopened"));
  const reopenedWithoutId = plan({ targetDisposition: "declined", action: { type: "ask_question", focus: { mode: "clarify_existing_event", targetEventId: null, domain: target.domain, requestedFacts: ["month"], rationaleCodes: ["retry"] }, question: "再说说那件事？", optionalQuickReplies: [] } });
  assert.ok(validateRectificationTurnPlan({ plan: reopenedWithoutId, dossier: targetDossier, latestAnswer: "不想说", phase: "final" }).issues.includes("declined_target_reopened"));

  const phases: string[] = [];
  const prompts: string[] = [];
  const requests = [
    { tool: "case_read", diagnostic: null },
    { tool: "candidate_scan", diagnostic: null },
    { tool: "evidence_gap", diagnostic: null },
    { tool: "diagnostic_read", diagnostic: "candidate_split" },
  ] as const;
  const result = await runRectificationDirector({
    caseValue,
    dossier: dossier(),
    latestAnswer: "",
    phase: "final",
    diagnostics,
    generatePlan: async (prompt, phase) => {
      phases.push(phase);
      prompts.push(prompt);
      const request = requests[phases.length - 1];
      return { object: request ? plan({ action: { type: "request_tool", ...request } }) : plan() };
    },
  });
  assert.equal(result.mode, "agent");
  assert.deepEqual(phases, ["final", "after_observation", "after_observation", "after_observation", "after_observation"]);
  assert.deepEqual(result.toolCalls.map(({ tool, diagnostic }) => [tool, diagnostic]), [
    ["case_read", null],
    ["candidate_scan", null],
    ["evidence_gap", null],
    ["diagnostic_read", "candidate_split"],
  ]);
  assert.equal(dossier().capabilities.maxToolRounds, 10);
  const firstPrompt = JSON.parse(prompts[0]!);
  assert.equal(firstPrompt.dossier.eventLedger, undefined);
  assert.equal(firstPrompt.dossier.candidateState, undefined);
  assert.equal(firstPrompt.dossier.runtime.hypotheses, undefined);
  assert.deepEqual(firstPrompt.dossier.interviewState.askedTopics, []);
  assert.deepEqual(firstPrompt.dossier.availableTools.readOnly, ["case_read", "candidate_scan", "evidence_gap"]);
  const caseObservationPrompt = JSON.parse(prompts[1]!);
  assert.ok(Array.isArray(caseObservationPrompt.latestObservation.result.eventLedger));
  assert.equal(caseObservationPrompt.dossier.runtime.observations[0].tool, "case_read");
  const candidateObservationPrompt = JSON.parse(prompts[2]!);
  assert.equal(candidateObservationPrompt.latestObservation.result.candidateState.hasSnapshot, false);
  assert.ok(Array.isArray(candidateObservationPrompt.latestObservation.result.hypotheses));
  const finalPrompt = JSON.parse(prompts[4]!);
  assert.equal(finalPrompt.dossier.runtime.revision, 4);
  assert.deepEqual(finalPrompt.dossier.runtime.observations.map((item: { tool: string }) => item.tool), requests.map(({ tool }) => tool));
  assert.equal(result.dossier.runtime.revision, 4);
  assert.equal(result.plan.action.type, "ask_question");
});

test("repeated immutable tools are not executed twice and force one convergence decision", async () => {
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
      return { object: phase === "converge" ? plan() : plan({ action: { type: "request_tool", tool: "candidate_scan", diagnostic: null } }) };
    },
  });
  assert.equal(result.mode, "agent");
  assert.deepEqual(phases, ["final", "after_observation", "converge"]);
  assert.equal(result.toolCalls.length, 1);
  assert.deepEqual(JSON.parse(prompts[2]!).loopState, {
    round: 1,
    maxRounds: 10,
    observedTools: ["candidate_scan:"],
    convergenceReason: "tool_repeated",
  });
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


test("final Director repairs a generic acknowledgement and missing evidence-value explanation", async () => {
  const internship = event({
    domain: "career",
    eventKind: "career_change",
    summary: "2020年4月去石油化工研究院实习做研究员",
    rawText: "2020年4月去石油化工研究院实习做研究员",
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
  });
  const phases: string[] = [];
  const prompts: string[] = [];
  const result = await runRectificationDirector({
    caseValue,
    dossier: dossier([internship]),
    latestAnswer: internship.rawText,
    phase: "final",
    diagnostics,
    generatePlan: async (prompt, phase) => {
      phases.push(phase);
      prompts.push(prompt);
      return {
        object: phase === "repair"
          ? plan({ publicReply: { acknowledgement: "你提到2020年4月去石油化工研究院实习做研究员。", evidenceExplanation: "这是一条职业状态变化线索，按能力矩阵可参考 D10 与 Vimshottari；目前只是方法映射，不是实际计算结果。", candidateCommentary: "这段经历的时间和工作状态变化都很明确，可以和其他独立事件交叉比较候选范围。", limitation: null }, publicExplanationGrounding: [{ source: "capability_matrix", factKey: "domain:career" }] })
          : plan(),
      };
    },
  });

  assert.equal(result.mode, "agent");
  assert.deepEqual(phases, ["final", "repair"]);
  assert.match(JSON.parse(prompts[0]!).publicReplyRequirement, /acknowledge the exact event/);
  assert.deepEqual(JSON.parse(prompts[1]!).validationIssues, ["event_explanation_grounding_missing", "event_acknowledgement_generic"]);
  assert.match(result.plan.publicReply.acknowledgement, /石油化工研究院/);
  assert.match(result.plan.publicReply.evidenceExplanation ?? "", /D10.*Vimshottari/);
  assert.equal(result.plan.publicReply.candidateCommentary, null);
});

test("manual question regeneration uses the server renderer and ignores model wording", async () => {
  const eventValue = event({
    summary: "2016年9月离家去外地上大学",
    rawText: "2016年9月离家去外地上大学",
    dateRange: { start: "2016-09-01", end: "2016-09-30", precision: "month", label: "2016年9月" },
  });
  const unsafeQuestions = [
    "D10 说明 A 方案更可信",
    "分盘已表明甲组更有把握",
    "测算已证明头一组",
    "推演已判定前者占优",
  ];
  for (const unsafeQuestion of unsafeQuestions) {
    let calls = 0;
    const question = await regenerateDirectorQuestion({
      caseValue,
      currentQuestion: `${unsafeQuestion}\n\n旧问题？`,
      latestAnswer: eventValue.rawText,
      acceptedEvents: [eventValue],
      focus: {
        mode: "collect_independent_event",
        targetEventId: null,
        domain: "career",
        requestedFacts: ["independent_event"],
        rationaleCodes: ["candidate_contrast"],
      },
      generateQuestion: async () => {
        calls += 1;
        return { object: { question: unsafeQuestion } };
      },
    });
    assert.equal(calls, 0);
    assert.match(question, /工作状态变化/);
    assert.doesNotMatch(question, /D10|分盘|测算|推演|甲组|头一组|前者占优/);
  }
});


test("public reply allows method names but rejects private internals", () => {
  const internship = event({
    domain: "career",
    eventKind: "career_change",
    summary: "2020年4月去研究院实习做研究员",
    rawText: "2020年4月去研究院实习做研究员",
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
  });
  const grounded = validateRectificationTurnPlan({
    plan: plan({
      publicReply: { acknowledgement: "你提到2020年4月去研究院实习做研究员。", evidenceExplanation: "模型任意解释。", candidateCommentary: null, limitation: null },
      publicExplanationGrounding: [{ source: "capability_matrix", factKey: "domain:career" }],
    }),
    dossier: dossier([internship]), latestAnswer: internship.rawText, phase: "final",
  });
  assert.deepEqual(grounded.issues, []);
  assert.match(grounded.plan?.publicReply.evidenceExplanation ?? "", /D10.*Vimshottari/);

  for (const privateDetail of ["原始评分 8.7", "权重 0.4", "贡献矩阵如下", "tool_call 原始输出", "我先调用 case_read，再调用 candidate_scan 和 diagnostic_read"]) {
    const result = validateRectificationTurnPlan({
      plan: plan({ action: { type: "ask_question", focus: { mode: "collect_independent_event", targetEventId: null, domain: null, requestedFacts: ["independent_event"], rationaleCodes: ["test"] }, question: `${privateDetail}，你还记得另一件经历吗？`, optionalQuickReplies: [] } }),
      dossier: dossier(), latestAnswer: "", phase: "final",
    });
    assert.deepEqual(result.issues, [], privateDetail);
    assert.doesNotMatch(result.plan?.action.type === "ask_question" ? result.plan.action.question : "", /评分|权重|贡献矩阵|tool_call|case_read|candidate_scan|diagnostic_read/);
  }
});

test("public explanations are server-rendered from current-event capability grounding", () => {
  const internship = event({
    domain: "career",
    eventKind: "career_change",
    summary: "2020年4月去研究院实习做研究员",
    rawText: "2020年4月去研究院实习做研究员",
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
  });
  const base = {
    acknowledgement: "你提到的是2020年4月去研究院实习做研究员。",
    candidateCommentary: "D10 已经显示较早候选更符合。",
    limitation: null,
  } as const;
  const madeUp = plan({
    publicReply: { ...base, evidenceExplanation: "这条职业变化可参考 D10。" },
    publicExplanationGrounding: [{ source: "capability_matrix", factKey: "made-up-key" }],
  });
  const madeUpIssues = validateRectificationTurnPlan({ plan: madeUp, dossier: dossier([internship]), latestAnswer: internship.rawText, phase: "final" }).issues;
  assert.ok(madeUpIssues.includes("public_grounding_invalid"));
  assert.ok(madeUpIssues.includes("event_explanation_grounding_missing"));

  const wrongDomain = plan({
    publicReply: { ...base, evidenceExplanation: "这条职业变化可参考 D24。" },
    publicExplanationGrounding: [{ source: "capability_matrix", factKey: "domain:education" }],
  });
  const wrongDomainIssues = validateRectificationTurnPlan({ plan: wrongDomain, dossier: dossier([internship]), latestAnswer: internship.rawText, phase: "final" }).issues;
  assert.ok(wrongDomainIssues.includes("public_grounding_invalid"));
  assert.ok(wrongDomainIssues.includes("event_explanation_grounding_missing"));

  for (const arbitraryExplanation of [
    "D10 已经显示这次职业变化支持较早的候选区间。",
    "这只是方法映射；D10 已经证明这次经历更符合较早出生。",
    "这只是方法映射；D10 说明该经历让 A 方案更可信。",
  ]) {
    const result = validateRectificationTurnPlan({
      plan: plan({
        publicReply: { ...base, evidenceExplanation: arbitraryExplanation },
        publicExplanationGrounding: [{ source: "capability_matrix", factKey: "domain:career" }],
      }),
      dossier: dossier([internship]), latestAnswer: internship.rawText, phase: "final",
    });
    assert.deepEqual(result.issues, []);
    assert.match(result.plan?.publicReply.evidenceExplanation ?? "", /方法层通常参考 D10、A10、Vimshottari/);
    assert.doesNotMatch(result.plan?.publicReply.evidenceExplanation ?? "", /较早|证明|A 方案/);
    assert.equal(result.plan?.publicReply.candidateCommentary, null);
  }

  const migratedClaim = validateRectificationTurnPlan({
    plan: plan({
      publicReply: { acknowledgement: "D10 说明该经历让 A 方案更可信。", evidenceExplanation: "任意模型解释", candidateCommentary: "较早候选更可信。", limitation: "较早候选已经领先。" },
      publicExplanationGrounding: [{ source: "capability_matrix", factKey: "domain:career" }],
    }),
    dossier: dossier([internship]), latestAnswer: internship.rawText, phase: "final",
  });
  assert.deepEqual(migratedClaim.issues, []);
  assert.equal(migratedClaim.plan?.publicReply.acknowledgement, "你提到的是“2020年4月去研究院实习做研究员”。");
  assert.equal(migratedClaim.plan?.publicReply.candidateCommentary, null);
  assert.equal(migratedClaim.plan?.publicReply.limitation, null);

  const unsafeQuestions = [
    "D10 说明 A 方案更可信，你还记得另一件经历吗？",
    "分盘已经表明甲组更有把握，你还记得另一件经历吗？",
    "测算已经证明头一组更合适。",
    "你还记得测算已经证明头一组更合适之后发生的另一件经历吗？",
    "你还记得推演已判定前者占优之后发生的另一件经历吗？",
  ];
  for (const unsafeQuestion of unsafeQuestions) {
    const result = validateRectificationTurnPlan({
      plan: plan({
        action: { type: "ask_question", focus: { mode: "collect_independent_event", targetEventId: null, domain: null, requestedFacts: ["independent_event"], rationaleCodes: ["test"] }, question: unsafeQuestion, optionalQuickReplies: [] },
        publicReply: { ...base, evidenceExplanation: "任意模型解释" },
        publicExplanationGrounding: [{ source: "capability_matrix", factKey: "domain:career" }],
      }),
      dossier: dossier([internship]), latestAnswer: internship.rawText, phase: "final",
    });
    assert.deepEqual(result.issues, []);
    const publicQuestion = result.plan?.action.type === "ask_question" ? result.plan.action.question : "";
    assert.match(publicQuestion, /在“2020年4月去研究院实习做研究员”之外/);
    assert.doesNotMatch(publicQuestion, /D10|分盘|测算|推演|甲组|头一组|前者占优/);
  }

  const directedDomain = validateRectificationTurnPlan({
    plan: plan({
      action: { type: "ask_question", focus: { mode: "collect_independent_event", targetEventId: null, domain: "career", requestedFacts: ["independent_event"], rationaleCodes: ["candidate_contrast"] }, question: "任意模型措辞", optionalQuickReplies: [] },
      publicReply: { ...base, evidenceExplanation: "任意模型解释" },
      publicExplanationGrounding: [{ source: "capability_matrix", factKey: "domain:career" }],
    }),
    dossier: dossier([internship]), latestAnswer: internship.rawText, phase: "final",
  });
  assert.match(directedDomain.plan?.action.type === "ask_question" ? directedDomain.plan.action.question : "", /工作状态变化/);
});

test("the final plan cannot repeat a previously asked question", () => {
  const previous = "你愿意再讲一件与已有记录不同、时间大致明确的经历吗？没有、记不清或不想回答也可以换个方向。";
  const repeated = plan({
    action: {
      type: "ask_question",
      focus: { mode: "collect_independent_event", targetEventId: null, domain: null, requestedFacts: ["independent_event"], rationaleCodes: ["test"] },
      question: "你还能想到一件时间大致确定的重要经历吗",
      optionalQuickReplies: [],
    },
  });
  assert.ok(validateRectificationTurnPlan({ plan: repeated, dossier: dossier([], [turn(0, { question: previous })]), latestAnswer: "", phase: "final" }).issues.includes("question_repeated"));
  const prefixedRepeat = plan({
    action: {
      type: "ask_question",
      focus: { mode: "collect_independent_event", targetEventId: null, domain: null, requestedFacts: ["independent_event"], rationaleCodes: ["test"] },
      question: `目前已有 0 条可继续核对的经历。${previous}`,
      optionalQuickReplies: [],
    },
  });
  assert.ok(validateRectificationTurnPlan({ plan: prefixedRepeat, dossier: dossier([], [turn(0, { question: previous })]), latestAnswer: "", phase: "final" }).issues.includes("question_repeated"));

  const storedPublicReply = composeRectificationPublicTurn({
    acknowledgement: "你提到的是2020年4月去研究院实习。",
    evidenceExplanation: "这条经历有明确月份，可以和其他经历交叉比较。",
    candidateUpdate: null,
    limitation: null,
    question: previous,
  });
  assert.ok(validateRectificationTurnPlan({ plan: repeated, dossier: dossier([], [turn(0, { question: storedPublicReply })]), latestAnswer: "", phase: "final" }).issues.includes("question_repeated"));
});

test("candidate range requires the current approved snapshot id", () => {
  const snapshot: CandidateSnapshot = {
    id: diagnostics.snapshotId, caseId, caseVersion: 3, evidenceSetHash: "e".repeat(64), calculationSpecHash: "c".repeat(64), algorithmVersion: "rectification-v5-matrix-scoring-1",
    candidates: [{ time: "05:12", score: 10, supportingEventIds: [], conflictingEventIds: [] }],
    clusters: [{ rank: 1, startTime: "05:12", endTime: "05:18", representativeTime: "05:13", widthMinutes: 7, peakScore: 10, scoreMass: 1 }],
    robustness: { neighborSupportMinutes: 7, leaveOneOutRetentionRate: .8, leaveOneDomainOutRetentionRate: .8, dateSensitivityRetentionRate: .8, calculationSpecHashMatched: true },
    canConfirmExactMinute: false, canAcceptRange: true, gateReasons: [], createdAt: now,
  };
  const approvedDossier = buildRectificationCaseDossier({ caseValue, turns: [], events: [], snapshot, diagnostics, targetDisposition: "not_applicable", currentTargetEventId: null });
  const accepted = plan({ action: { type: "offer_candidate_range", snapshotId: snapshot.id } });
  assert.deepEqual(validateRectificationTurnPlan({ plan: accepted, dossier: approvedDossier, latestAnswer: "", phase: "final" }).issues, []);
  const wrongSnapshot = plan({ action: { type: "offer_candidate_range", snapshotId: randomUUID() } });
  assert.ok(validateRectificationTurnPlan({ plan: wrongSnapshot, dossier: approvedDossier, latestAnswer: "", phase: "final" }).issues.includes("candidate_range_gate_failed"));
  const legacyRelationshipEnd = event({ domain: "relationship", eventKind: "relationship_end", scoreability: "scoreable" });
  const staleDossier = buildRectificationCaseDossier({ caseValue, turns: [], events: [legacyRelationshipEnd], snapshot, diagnostics, targetDisposition: "not_applicable", currentTargetEventId: null });
  assert.equal(staleDossier.candidateState.publicRangeAllowed, false);
  assert.ok(validateRectificationTurnPlan({ plan: accepted, dossier: staleDossier, latestAnswer: "", phase: "final" }).issues.includes("candidate_range_gate_failed"));
});

test("an unresolved broad-date target cannot be abandoned for a new event", () => {
  const target = event({
    dateRange: { start: "2016-01-01", end: "2016-12-31", precision: "year", label: "2016年" },
  });
  const targetDossier = buildRectificationCaseDossier({
    caseValue,
    turns: [],
    events: [target],
    snapshot: null,
    diagnostics: null,
    targetDisposition: "unresolved",
    currentTargetEventId: target.eventId,
  });
  const abandoned = plan({
    targetDisposition: "unresolved",
    action: {
      type: "ask_question",
      focus: {
        mode: "collect_independent_event",
        targetEventId: null,
        domain: null,
        requestedFacts: ["independent_event"],
        rationaleCodes: ["need_independent_event"],
      },
      question: "你还能想到另一件时间大致确定的重要经历吗？",
      optionalQuickReplies: [],
    },
  });

  assert.ok(validateRectificationTurnPlan({
    plan: abandoned,
    dossier: targetDossier,
    latestAnswer: target.rawText,
    phase: "final",
  }).issues.includes("unresolved_target_abandoned"));
});

test("deterministic fallback refines the known year before collecting another event", async () => {
  const target = event({
    summary: "2016年离家去外地上大学",
    rawText: "2016 年离家去外地上大学",
    dateRange: { start: "2016-01-01", end: "2016-12-31", precision: "year", label: "2016年" },
  });
  const result = await runRectificationDirector({
    caseValue,
    dossier: buildRectificationCaseDossier({
      caseValue,
      turns: [],
      events: [target],
      snapshot: null,
      diagnostics: null,
      targetDisposition: "unresolved",
      currentTargetEventId: target.eventId,
    }),
    latestAnswer: target.rawText,
    phase: "final",
    diagnostics,
    generatePlan: async () => { throw new Error("forced_fallback"); },
  });

  assert.equal(result.mode, "deterministic_fallback");
  assert.equal(result.plan.action.type, "ask_question");
  if (result.plan.action.type !== "ask_question") return;
  assert.equal(result.plan.action.focus.targetEventId, target.eventId);
  assert.deepEqual(result.plan.action.focus.requestedFacts, ["month"]);
  assert.match(result.plan.action.question, /2016年离家去外地上大学/);
  assert.match(result.plan.action.question, /哪个月|时间段/);
  assert.doesNotMatch(result.plan.action.question, /另一件|还能想到一件/);
});

test("deterministic fallback pauses instead of repeating a persisted public question", async () => {
  const repeatedQuestion = "你愿意再讲一件与已有记录不同、时间大致明确的经历吗？没有、记不清或不想回答也可以换个方向。";
  const persisted = composeRectificationPublicTurn({
    acknowledgement: "本轮信息已经保留。",
    evidenceExplanation: null,
    candidateUpdate: null,
    limitation: null,
    question: repeatedQuestion,
  });
  const result = await runRectificationDirector({
    caseValue,
    dossier: buildRectificationCaseDossier({
      caseValue,
      turns: [turn(0, { question: persisted, answer: "2016年9月去外地上大学" })],
      events: [],
      snapshot: null,
      diagnostics: null,
      targetDisposition: "not_applicable",
      currentTargetEventId: null,
    }),
    latestAnswer: "",
    phase: "final",
    diagnostics,
    generatePlan: async () => { throw new Error("forced_fallback"); },
  });

  assert.equal(result.mode, "deterministic_fallback");
  assert.equal(result.plan.action.type, "stop_low_confidence");
  if (result.plan.action.type !== "stop_low_confidence") return;
  assert.deepEqual(result.plan.action.reasonCodes, ["deterministic_fallback_rejected"]);
});

test("deterministic fallback stays domain-neutral when the Agent is unavailable", async () => {
  const university = event({
    summary: "2016年9月离家去外地上大学",
    rawText: "2016年9月离家去外地上大学",
    createdAt: "2026-07-30T01:00:00.000Z",
  });
  const internship = event({
    domain: "career",
    eventKind: "career_change",
    summary: "2020年4月去石油化工研究院实习做研究员",
    rawText: "2020年4月去石油化工研究院实习做研究员",
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
    createdAt: "2026-07-30T02:00:00.000Z",
  });
  const turns = [
    turn(0, { questionDomain: "education", question: "请说一件时间比较确定的经历。", answer: university.rawText }),
    turn(1, { questionDomain: "career", question: "你是否有过工作状态变化？", answer: internship.rawText }),
  ];

  const result = await runRectificationDirector({
    caseValue,
    dossier: buildRectificationCaseDossier({
      caseValue,
      turns,
      events: [university, internship],
      snapshot: null,
      diagnostics: null,
      targetDisposition: "not_applicable",
      currentTargetEventId: null,
    }),
    latestAnswer: internship.rawText,
    phase: "final",
    diagnostics,
    generatePlan: async () => { throw new Error("forced_fallback"); },
  });

  assert.equal(result.mode, "deterministic_fallback");
  assert.equal(result.plan.action.type, "ask_question");
  if (result.plan.action.type !== "ask_question") return;
  assert.equal(result.plan.action.focus.targetEventId, null);
  assert.equal(result.plan.action.focus.domain, null);
  assert.deepEqual(result.plan.action.focus.rationaleCodes, ["model_unavailable_neutral_fallback"]);
  assert.match(result.plan.action.question, /愿意.*再讲一件/);
  assert.match(result.plan.action.question, /没有|记不清|不想回答|换/);
  assert.doesNotMatch(result.plan.action.question.split("之外").at(-1) ?? result.plan.action.question, /教育|迁居|关系|职业|财务|健康|大学|实习|搬家/);
  assert.match(result.plan.publicReply.acknowledgement, /2020年4月|石油化工研究院|实习|研究员/);
});

test("the visible assistant turn includes acknowledgement, evidence value, and exactly one question", () => {
  const text = composeRectificationPublicTurn({
    acknowledgement: "你提到的是“2020年4月去石油化工研究院实习做研究员”。",
    evidenceExplanation: "这条职业变化可参考 D10 与 Vimshottari；目前只是方法映射。",
    candidateUpdate: "这条线索有明确时间，也说明了具体发生的变化，可以和其他独立经历交叉比较候选范围。",
    limitation: null,
    question: "如果你愿意，有没有一次长期资格或身份发生变化的经历，大概是哪年哪月？",
  });

  assert.match(text, /石油化工研究院/);
  assert.match(text, /交叉比较候选范围/);
  assert.match(text, /长期资格|身份发生变化/);
  assert.equal((text.match(/[?？]/g) ?? []).length, 1);
});
