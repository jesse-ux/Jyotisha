import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";

import {
  diagnosticsSummarySchema,
  storedPublicMessageSchema,
  type DiagnosticsSummary,
  type QuestionOpportunity,
} from "../src/lib/rectification-agent/contracts.ts";
import { processRectificationAgentTurn } from "../src/lib/rectification-agent/orchestrator.ts";
import { runBoundedReasoner, sanitizeReasoningSummary } from "../src/lib/rectification-agent/reasoner-agent.ts";
import { createRectificationV4CaseService } from "../src/lib/rectification-v4/case-service.ts";
import type { CandidateEngineResult } from "../src/lib/rectification-v4/candidate-engine.ts";
import type {
  CalculationSpec,
  CandidateMinute,
  LifeEventRevision,
  RectificationAnalysisTrace,
  RectificationV4Case,
  RectificationV4Turn,
} from "../src/lib/rectification-v4/contracts.ts";
import { calculationSpecHash } from "../src/lib/rectification-v4/fingerprints.ts";
import { createRectificationV4MemoryStore } from "../src/lib/rectification-v4/memory-store.ts";
import { projectAnalysisMessages } from "../src/lib/rectification-v4/supabase-store.ts";
import type { ClaimedRectificationV4Job } from "../src/lib/rectification-v4/store.ts";
import { createRectificationV4Worker } from "../src/lib/rectification-v4/worker.ts";
import { passingVedAstroValidation, v5EngineResult, withV5Mode } from "./rectification-v5-test-support.ts";

const now = "2026-07-29T00:00:00.000Z";
const rangeReadyCandidates: CandidateMinute[] = [
  { time: "05:13", score: 100, supportingEventIds: [], conflictingEventIds: [] },
  { time: "05:14", score: 99, supportingEventIds: [], conflictingEventIds: [] },
  { time: "05:15", score: 98, supportingEventIds: [], conflictingEventIds: [] },
  { time: "05:16", score: 60, supportingEventIds: [], conflictingEventIds: [] },
  { time: "05:17", score: 97.8, supportingEventIds: [], conflictingEventIds: [] },
  { time: "05:18", score: 97.7, supportingEventIds: [], conflictingEventIds: [] },
  { time: "05:19", score: 97.6, supportingEventIds: [], conflictingEventIds: [] },
];

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

function event(
  domain: LifeEventRevision["domain"],
  eventKind: LifeEventRevision["eventKind"],
  summary: string,
  date: string,
): LifeEventRevision {
  return {
    id: randomUUID(),
    eventId: randomUUID(),
    revision: 1,
    domain,
    eventKind,
    subject: "self",
    relatedPerson: null,
    summary,
    rawText: `${date} ${summary}`,
    dateRange: { start: `${date}-01`, end: `${date}-28`, precision: "month", label: date },
    scoreability: "scoreable",
    supersedesRevisionId: null,
    createdAt: now,
  };
}

function makeClaimed(events: readonly LifeEventRevision[]): ClaimedRectificationV4Job {
  const caseId = randomUUID();
  const turn: RectificationV4Turn = {
    id: randomUUID(),
    caseId,
    caseVersion: 1,
    questionId: randomUUID(),
    questionDomain: "other",
    questionTargetEventId: null,
    question: "请换一个方向，补充一件时间较清楚的经历。",
    answer: "记不清了，换一个吧。",
    modelId: null,
    actionId: randomUUID(),
    createdAt: now,
  };
  const caseValue: RectificationV4Case = {
    id: caseId,
    userId: randomUUID(),
    protocol: "rectification-evidence-v5",
    version: 1,
    status: "processing",
    phase: "extracting_evidence",
    calculationSpec: spec,
    calculationSpecHash: calculationSpecHash(spec),
    evidenceSetHash: "e".repeat(64),
    currentQuestion: null,
    latestSnapshot: null,
    orchestrationModelId: null,
    narrationModelId: null,
    skillVersion: "birth-time-rectification-v6",
    promptVersion: "rectification-agent-v6-1",
    algorithmVersion: "rectification-v5-matrix-scoring-1",
    deploymentMode: "v5_agent",
    agentMode: "deterministic_fallback",
    featureSnapshotId: null,
    latestDiagnosticsId: null,
    acceptedRange: null,
    createdAt: now,
    updatedAt: now,
  };
  return {
    case: caseValue,
    turn,
    turns: [turn],
    events,
    attemptedRefinementEventIds: [],
    job: {
      id: randomUUID(),
      caseId,
      status: "processing",
      phase: "extracting_evidence",
      expectedCaseVersion: 1,
      evidenceSetHash: caseValue.evidenceSetHash,
      calculationSpecHash: caseValue.calculationSpecHash,
      errorCode: null,
      createdAt: now,
      updatedAt: now,
    },
  };
}

const opportunity: QuestionOpportunity = {
  contractVersion: "semantic-question-v2",
  opportunityId: randomUUID(),
  kind: "ask_new_event",
  domain: "career",
  targetEventId: null,
  goal: "收集一件有大致日期的新经历。",
  requestedFields: ["new_dated_event"],
  anchors: [],
  contextFacts: [],
  forbiddenMoves: [
    "switch_target_event",
    "ask_multiple_questions",
    "claim_exact_birth_minute",
    "invent_event",
    "invent_date",
    "expose_private_score",
    "expose_internal_id",
    "expose_technique_trace",
  ],
  fallbackPrompt: "请再说一件时间比较明确的经历。",
  reason: "补充可区分的证据。",
  expectedInformationGain: .8,
  dateSensitivity: .5,
  candidateSplitRelevance: .5,
  domainCoverageGain: .8,
  recallEase: .8,
  novelty: 1,
  repetitionPenalty: 0,
  privacyCost: 0,
  utility: .85,
  active: true,
};

const diagnostics: DiagnosticsSummary = diagnosticsSummarySchema.parse({
  id: randomUUID(),
  caseId: randomUUID(),
  snapshotId: randomUUID(),
  primaryClusterRetentionRate: .8,
  leaveOneEventOutRetentionRate: .8,
  leaveOneDomainOutRetentionRate: .8,
  dateSensitivityRetentionRate: .8,
  neighborSupportMinutes: 3,
  primarySecondaryMarginPercent: 12,
  clusterMassRatio: .8,
  unstableEventIds: [],
  mostDiscriminatingLayers: [],
  eventDateSensitivity: [],
  candidateSplits: [],
  calculationHash: "d".repeat(64),
  createdAt: now,
});

function analysisToolLabels(trace: RectificationAnalysisTrace, category: RectificationAnalysisTrace["toolCalls"][number]["category"]): string[] {
  return trace.toolCalls.filter((call) => call.category === category).map((call) => call.label);
}

test("provider reasoning keeps safe summaries and rejects private or copied content", async () => {
  const safeSummary = "现有材料还不足，宜先补充一件时间较清楚的经历。";
  const reasoned = await runBoundedReasoner({
    caseValue: makeClaimed([]).case,
    snapshot: null,
    diagnostics,
    opportunities: [opportunity],
    generateDecision: async () => ({
      object: { action: "ask_question", opportunityId: opportunity.opportunityId, narrativeFocus: ["uncertainty"] },
      reasoningSummary: safeSummary,
      reasoningSource: "provider_summary",
    }),
  });
  assert.equal(reasoned.reasoningSummary, safeSummary);

  const unsafe = [
    "参考 00000000-0000-4000-8000-000000000901",
    "候选是 05:13",
    "score 较高",
    "snapshotId 已更新",
    "opportunityId 已选中",
    "执行 tool call",
    "采用 D9 继续判断",
    "候选更接近清晨五点十三分",
    "保留率低于百分之六十五",
  ];
  for (const value of unsafe) assert.equal(sanitizeReasoningSummary(value), null, value);

  const userText = "2016年9月离家去外地上大学";
  assert.equal(sanitizeReasoningSummary(`用户提到${userText}，所以继续。`, [userText]), null);
  assert.equal(sanitizeReasoningSummary("母亲去世后需要继续收集证据。", ["母亲去世"]), null);
  assert.equal(sanitizeReasoningSummary("癌症使这项证据需要谨慎处理。", ["癌症"]), null);

  const unverifiedSource = await runBoundedReasoner({
    caseValue: makeClaimed([]).case,
    snapshot: null,
    diagnostics,
    opportunities: [opportunity],
    generateDecision: async () => ({
      object: { action: "ask_question", opportunityId: opportunity.opportunityId, narrativeFocus: [] },
      reasoningSummary: safeSummary,
    }),
  });
  assert.equal(unverifiedSource.reasoningSummary, null);
});

test("below the scoring gate does not claim candidate scanning, diagnostics, or techniques", async () => {
  let scoreCalls = 0;
  const result = await processRectificationAgentTurn({
    claimed: makeClaimed([
      event("education", "education_milestone", "离家去外地上大学", "2016-09"),
      event("career", "career_change", "开始第一份工作", "2020-04"),
    ]),
    engine: { score: async () => { scoreCalls += 1; throw new Error("candidate_engine_should_not_run"); } },
    now: new Date(now),
  });
  const trace = result.publicMessage.analysisTrace;
  assert.ok(trace);
  assert.equal(scoreCalls, 0);
  assert.equal(result.snapshot, null);
  assert.equal(trace.stages.some((stage) => stage.phase === "scoring_candidates"), false);
  assert.equal(trace.stages.some((stage) => stage.phase === "checking_robustness"), false);
  assert.equal(trace.stages.some((stage) => /安全校验|服务器安全问题/.test(stage.label)), true);
  assert.deepEqual(trace.toolCalls, []);
  assert.deepEqual(trace.techniques, []);
});

test("scoring trace records one real engine call and only matrix-confirmed techniques", async () => {
  const claimed = makeClaimed([
    event("education", "education_milestone", "离家去外地上大学", "2016-09"),
    event("relocation", "relocation", "搬到北京长期居住", "2018-08"),
    event("career", "career_change", "开始负责商业巡演公司", "2023-09"),
  ]);
  let scoreCalls = 0;
  const result = await processRectificationAgentTurn({
    claimed,
    engine: {
      score: async ({ calculationSpec, events }) => {
        scoreCalls += 1;
        const base = v5EngineResult(calculationSpec, events, rangeReadyCandidates);
        const contributionMatrix: CandidateEngineResult["contributionMatrix"] = Object.fromEntries(
          Object.entries(base.contributionMatrix).map(([eventId, candidates]) => [
            eventId,
            Object.fromEntries(Object.entries(candidates).map(([time, contribution]) => [time, {
              ...contribution,
              rule_ids: ["vimshottari_dasha", "D60"],
              technique_layers: ["D2", "D60"],
            }])),
          ]),
        );
        return { ...base, contributionMatrix };
      },
    },
    now: new Date(now),
  });
  const trace = result.publicMessage.analysisTrace;
  assert.ok(trace);
  assert.equal(scoreCalls, 1);
  assert.equal(result.snapshot?.canConfirmExactMinute, false);
  assert.equal(trace.stages.some((stage) => stage.phase === "scoring_candidates"), true);
  assert.equal(trace.stages.some((stage) => stage.phase === "checking_robustness"), true);
  assert.deepEqual(analysisToolLabels(trace, "candidate_engine"), ["候选分钟扫描与稳定性诊断"]);
  assert.deepEqual(analysisToolLabels(trace, "diagnostic"), []);
  assert.deepEqual(new Set(trace.techniques), new Set(["Vimshottari Dasha", "D2"]));
  assert.equal(trace.techniques.includes("D60"), false);
  assert.equal(trace.techniques.includes("D9"), false);
  assert.equal(trace.techniques.includes("D10"), false);
  assert.deepEqual(analysisToolLabels(trace, "agent_diagnostic"), []);
});

test("VedAstro post-validation runs only after the local range gate and blocks publication on safe failure", async () => {
  const claimed = makeClaimed([
    event("education", "education_milestone", "离家去外地上大学", "2016-09"),
    event("relocation", "relocation", "搬到北京长期居住", "2018-08"),
    event("career", "career_change", "开始负责商业巡演公司", "2023-09"),
    event("relationship", "relationship_start", "开始一段长期关系", "2021-05"),
    event("finance", "finance_change", "收入结构发生明显变化", "2024-02"),
  ]);
  let validationCalls = 0;
  const blocked = await processRectificationAgentTurn({
    claimed,
    engine: {
      score: async ({ calculationSpec, events }) => v5EngineResult(calculationSpec, events, rangeReadyCandidates),
      validateWithVedAstro: async ({ candidateTimes }) => {
        validationCalls += 1;
        assert.deepEqual(candidateTimes, ["05:13", "05:14"]);
        return passingVedAstroValidation(candidateTimes, {
          status: "blocked",
          providerStatus: "timeout",
          blockers: ["vedastro_timeout"],
          minuteSensitiveValidation: { comparisonReady: false, discriminated: false, discriminatedLayers: [] },
        });
      },
    },
    now: new Date(now),
  });
  assert.equal(validationCalls, 1);
  assert.equal(blocked.snapshot?.canAcceptRange, false);
  assert.equal(blocked.snapshot?.canConfirmExactMinute, false);
  assert.ok(blocked.snapshot?.gateReasons.includes("vedastro_validation_not_passed"));
  assert.equal(blocked.diagnostics?.externalValidation?.status, "blocked");
  assert.deepEqual(analysisToolLabels(blocked.publicMessage.analysisTrace!, "diagnostic"), ["VedAstro 事后校验"]);

  validationCalls = 0;
  const localGateBlocked = await processRectificationAgentTurn({
    claimed,
    engine: {
      score: async ({ calculationSpec, events }) => {
        const result = v5EngineResult(calculationSpec, events, rangeReadyCandidates);
        return { ...result, robustness: { ...result.robustness, leaveOneDomainOutRetentionRate: 0 } };
      },
      validateWithVedAstro: async ({ candidateTimes }) => {
        validationCalls += 1;
        return passingVedAstroValidation(candidateTimes);
      },
    },
    now: new Date(now),
  });
  assert.equal(validationCalls, 0);
  assert.equal(localGateBlocked.snapshot?.canAcceptRange, false);
  assert.equal(localGateBlocked.diagnostics?.externalValidation, undefined);
});

test("legacy and shadow modes never call VedAstro post-validation", async () => {
  const events = [
    event("education", "education_milestone", "离家去外地上大学", "2016-09"),
    event("relocation", "relocation", "搬到北京长期居住", "2018-08"),
    event("career", "career_change", "开始负责商业巡演公司", "2023-09"),
    event("relationship", "relationship_start", "开始一段长期关系", "2021-05"),
    event("finance", "finance_change", "收入结构发生明显变化", "2024-02"),
  ];
  for (const deploymentMode of ["v4_legacy", "v5_shadow"] as const) {
    const base = makeClaimed(events);
    let validationCalls = 0;
    const result = await processRectificationAgentTurn({
      claimed: { ...base, case: { ...base.case, deploymentMode } },
      engine: {
        score: async ({ calculationSpec, events: scoreEvents }) => v5EngineResult(calculationSpec, scoreEvents),
        validateWithVedAstro: async ({ candidateTimes }) => {
          validationCalls += 1;
          return passingVedAstroValidation(candidateTimes);
        },
      },
      now: new Date(now),
    });
    assert.equal(validationCalls, 0, deploymentMode);
    assert.equal(result.diagnostics?.externalValidation, undefined, deploymentMode);
    assert.equal(result.snapshot?.canConfirmExactMinute, false, deploymentMode);
  }
});

test("read-only Agent diagnostics are traced only when the reasoner actually requests one", async () => {
  const caseValue = makeClaimed([]).case;
  const direct = await runBoundedReasoner({
    caseValue,
    snapshot: null,
    diagnostics,
    opportunities: [opportunity],
    generateDecision: async () => ({ object: { action: "ask_question", opportunityId: opportunity.opportunityId, narrativeFocus: [] } }),
  });
  assert.deepEqual(direct.toolCalls, []);

  const phases: string[] = [];
  const diagnosticRun = await runBoundedReasoner({
    caseValue,
    snapshot: null,
    diagnostics,
    opportunities: [opportunity],
    generateDecision: async (_prompt, phase) => {
      phases.push(phase);
      return phase === "initial"
        ? { object: { action: "run_diagnostic", diagnostic: "neighbor_stability" } }
        : { object: { action: "ask_question", opportunityId: opportunity.opportunityId, narrativeFocus: ["uncertainty"] } };
    },
  });
  assert.deepEqual(phases, ["initial", "after_diagnostic"]);
  assert.deepEqual(diagnosticRun.toolCalls.map((call) => [call.tool, call.diagnostic, call.outcome]), [
    ["run_rectification_diagnostics", "neighbor_stability", "succeeded"],
  ]);
});

test("old public messages without analysisTrace remain readable and are omitted from trace history", async () => {
  await withV5Mode("v5_agent", async () => {
    const store = createRectificationV4MemoryStore();
    const service = createRectificationV4CaseService(store, { now: () => new Date(now) });
    const worker = createRectificationV4Worker({
      store,
      now: () => new Date(now),
      engine: { score: async () => { throw new Error("candidate_engine_should_not_run"); } },
    });
    const userId = randomUUID();
    const created = await service.createCase({ userId, actionId: randomUUID(), calculationSpec: spec });
    const queued = await service.answer({
      userId,
      caseId: created.case.id,
      actionId: randomUUID(),
      expectedCaseVersion: created.case.version,
      answer: "2016年9月离家去外地上大学",
    });
    assert.ok(queued?.job);
    assert.equal(await worker.runOnce(), true);

    const legacyMessage = storedPublicMessageSchema.parse({
      acknowledgement: "你提到的是离家去外地上大学。",
      candidateUpdate: null,
      limitation: null,
      question: "请再说一件时间比较明确的经历。",
    });
    assert.equal(legacyMessage.analysisTrace, undefined);
    store.publicMessages.set(queued.job.id, legacyMessage);
    assert.deepEqual(await store.loadAnalysisMessages(userId, created.case.id), []);
  });
});


function storedMessageWithTrace(trace: unknown): Record<string, unknown> {
  return {
    acknowledgement: "承接这段经历。",
    candidateUpdate: null,
    limitation: null,
    question: "请再说一件时间比较明确的经历。",
    analysisTrace: trace,
  };
}

test("Supabase analysis projection orders multiple turns and maps job ids to turn ids", () => {
  const earlierJobId = randomUUID();
  const laterJobId = randomUUID();
  const earlierTurnId = randomUUID();
  const laterTurnId = randomUUID();
  const earlierTrace: RectificationAnalysisTrace = {
    status: "completed",
    stages: [],
    toolCalls: [],
    techniques: ["D2"],
    reasoningSummary: null,
    reasoningSource: "none",
  };
  const laterTrace: RectificationAnalysisTrace = {
    status: "completed",
    stages: [],
    toolCalls: [],
    techniques: ["D4"],
    reasoningSummary: null,
    reasoningSource: "none",
  };

  const projected = projectAnalysisMessages([
    { job_id: laterJobId, message: storedMessageWithTrace(laterTrace), created_at: "2026-07-29T02:00:00.000Z" },
    { job_id: earlierJobId, message: storedMessageWithTrace(earlierTrace), created_at: "2026-07-29T01:00:00.000Z" },
  ], [
    { id: laterJobId, turn_id: laterTurnId },
    { id: earlierJobId, turn_id: earlierTurnId },
  ]);

  assert.deepEqual(projected, [
    { sourceTurnId: earlierTurnId, trace: earlierTrace },
    { sourceTurnId: laterTurnId, trace: laterTrace },
  ]);
});

test("Supabase analysis projection ignores legacy messages without analysisTrace", () => {
  const jobId = randomUUID();
  const turnId = randomUUID();
  assert.deepEqual(projectAnalysisMessages([{
    job_id: jobId,
    message: {
      acknowledgement: "承接这段经历。",
      candidateUpdate: null,
      limitation: null,
      question: "请再说一件时间比较明确的经历。",
    },
    created_at: "2026-07-29T01:00:00.000Z",
  }], [{ id: jobId, turn_id: turnId }]), []);
});

test("Supabase analysis projection ignores invalid traces", () => {
  const jobId = randomUUID();
  const turnId = randomUUID();
  assert.deepEqual(projectAnalysisMessages([{
    job_id: jobId,
    message: storedMessageWithTrace({
      status: "invented",
      stages: [],
      toolCalls: [],
      techniques: [],
      reasoningSummary: null,
      reasoningSource: "none",
    }),
    created_at: "2026-07-29T01:00:00.000Z",
  }], [{ id: jobId, turn_id: turnId }]), []);
});
