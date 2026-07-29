import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import test from "node:test";
import type { QuestionOpportunity, ValidatedDecision } from "../src/lib/rectification-agent/contracts.ts";
import { realizePublicMessage, validateQuestionRealization } from "../src/lib/rectification-agent/renderer-agent.ts";
import type { CandidateSnapshot, LifeEventRevision, PendingEvidence } from "../src/lib/rectification-v4/contracts.ts";

const caseId = "00000000-0000-4000-8000-000000000701";
const now = "2026-07-29T00:00:00.000Z";

function event(): LifeEventRevision {
  return {
    id: randomUUID(),
    eventId: randomUUID(),
    revision: 1,
    domain: "career",
    eventKind: "career_change",
    subject: "self",
    relatedPerson: null,
    summary: "2020年4月研究院实习",
    rawText: "2020年4月去石油化工研究院实习做研究员。",
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
    scoreability: "scoreable",
    supersedesRevisionId: null,
    createdAt: now,
  };
}

function opportunity(target: LifeEventRevision): QuestionOpportunity {
  return {
    contractVersion: "semantic-question-v2",
    opportunityId: randomUUID(),
    kind: "refine_event_date",
    domain: "career",
    targetEventId: target.eventId,
    goal: "确认研究院实习发生的大概阶段。",
    requestedFields: ["event_stage"],
    anchors: [target.summary],
    contextFacts: [],
    forbiddenMoves: ["switch_target_event", "ask_multiple_questions", "claim_exact_birth_minute", "invent_event", "invent_date", "expose_private_score", "expose_internal_id", "expose_technique_trace"],
    fallbackPrompt: `关于“${target.summary}”，你更记得是开始、高峰还是结束阶段吗？`,
    reason: "当前事件仍需区分发生阶段。",
    expectedInformationGain: 0.7,
    dateSensitivity: 0.7,
    candidateSplitRelevance: 0.4,
    domainCoverageGain: 0,
    recallEase: 0.6,
    novelty: 0.8,
    repetitionPenalty: 0,
    privacyCost: 0.05,
    utility: 0.65,
    active: true,
  };
}

function validated(selectedOpportunity: QuestionOpportunity): ValidatedDecision {
  return {
    decision: { action: "ask_question", opportunityId: selectedOpportunity.opportunityId, narrativeFocus: ["latest_event"] },
    mode: "agent",
    validationIssues: [],
    selectedOpportunity,
  };
}

function snapshot(range: readonly [string, string]): CandidateSnapshot {
  const [startTime, endTime] = range;
  return {
    id: randomUUID(),
    caseId,
    caseVersion: 3,
    evidenceSetHash: "e".repeat(64),
    calculationSpecHash: "c".repeat(64),
    algorithmVersion: "rectification-v5-matrix-scoring-1",
    candidates: [{ time: startTime, score: 10, supportingEventIds: [], conflictingEventIds: [] }],
    clusters: [{ rank: 1, startTime, endTime, representativeTime: startTime, widthMinutes: 7, peakScore: 10, scoreMass: 1 }],
    robustness: { neighborSupportMinutes: 8, leaveOneOutRetentionRate: 0.8, dateSensitivityRetentionRate: 0.8, calculationSpecHashMatched: true },
    canConfirmExactMinute: false,
    canAcceptRange: true,
    gateReasons: [],
    createdAt: now,
  };
}

test("Renderer 对全部模型可见文本执行 exact-minute 和内部信息安全回落", () => {
  const target = event();
  const selectedOpportunity = opportunity(target);
  const input = {
    latestAnswer: target.rawText,
    acceptedEvents: [target],
    pendingEvidence: [] as PendingEvidence[],
    snapshot: null,
    previousSnapshot: null,
    validated: validated(selectedOpportunity),
  };

  const message = realizePublicMessage({
    acknowledgement: `你提到的是“${target.summary}”，所以准确出生分钟是05:13。`,
    candidateUpdate: null,
    limitation: "准确出生分钟是五点十三分，snapshotId 已确认。",
    question: `关于${target.summary}，唯一出生分钟是什么？`,
  }, input);

  assert.equal(message.acknowledgement, `你提到的是 ${target.dateRange.label} 的“${target.summary}”。`);
  assert.equal(message.limitation, null);
  assert.equal(message.question, selectedOpportunity.fallbackPrompt);
  assert.doesNotMatch(JSON.stringify(message), /05:13|五点十三分|准确出生分钟|唯一出生分钟|snapshotId/);

  for (const question of [
    `关于${target.summary}，你是不是五点十三分出生？`,
    `关于${target.summary}，eventId 是什么？`,
  ]) {
    assert.equal(validateQuestionRealization(question, selectedOpportunity).valid, false, question);
  }
});

test("Renderer 保留服务器生成的合法候选范围表达", () => {
  const target = event();
  const selectedOpportunity = opportunity(target);
  const message = realizePublicMessage({
    acknowledgement: `你提到的是“${target.summary}”。`,
    candidateUpdate: "模型声称出生时间就是05:13。",
    limitation: null,
    question: `关于${target.summary}，你更记得是开始、高峰还是结束阶段吗？`,
  }, {
    latestAnswer: target.rawText,
    acceptedEvents: [target],
    pendingEvidence: [],
    snapshot: snapshot(["05:12", "05:18"]),
    previousSnapshot: null,
    validated: validated(selectedOpportunity),
  });

  assert.match(message.candidateUpdate ?? "", /候选范围.*05:12.*05:18/);
  assert.match(message.candidateUpdate ?? "", /不代表其中某一分钟已被确认/);
  assert.doesNotMatch(message.candidateUpdate ?? "", /就是05:13/);
});
