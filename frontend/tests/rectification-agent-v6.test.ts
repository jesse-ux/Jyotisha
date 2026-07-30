import assert from "node:assert/strict";
import { randomUUID } from "node:crypto";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  diagnosticsSummarySchema,
  normalizeQuestionOpportunity,
  type DiagnosticsSummary,
  type QuestionOpportunity,
  type ValidatedDecision,
} from "../src/lib/rectification-agent/contracts.ts";
import { buildQuestionOpportunities } from "../src/lib/rectification-agent/opportunity-builder.ts";
import { buildReasonerState } from "../src/lib/rectification-agent/reasoner-agent.ts";
import { candidateUpdateFor, realizePublicMessage, validateQuestionRealization } from "../src/lib/rectification-agent/renderer-agent.ts";
import { extractLifeEventEvidence, validatedModelAssistedEvidence } from "../src/lib/conversational-rectification/evidence-extractor.ts";
import type { CandidateSnapshot, LifeEventRevision, PendingEvidence, RectificationV4Turn } from "../src/lib/rectification-v4/contracts.ts";
import { reconcileV4Evidence } from "../src/lib/rectification-v4/extraction.ts";

const now = "2026-07-29T00:00:00.000Z";
const caseId = "00000000-0000-4000-8000-000000000601";
const snapshotId = "00000000-0000-4000-8000-000000000602";

function event(overrides: Partial<LifeEventRevision> = {}): LifeEventRevision {
  return {
    id: randomUUID(), eventId: randomUUID(), revision: 1, domain: "education", eventKind: "education_milestone",
    subject: "self", relatedPerson: null, summary: "2016年大学入学", rawText: "2016年9月离家去外地上大学",
    dateRange: { start: "2016-09-01", end: "2016-09-30", precision: "month", label: "2016年9月" },
    scoreability: "scoreable", supersedesRevisionId: null, createdAt: now, ...overrides,
  };
}

function turn(overrides: Partial<RectificationV4Turn> = {}): RectificationV4Turn {
  return {
    id: randomUUID(), caseId, caseVersion: 1, questionId: randomUUID(), questionDomain: "education",
    questionTargetEventId: null, question: "请说一件时间比较确定的经历。", answer: "2016年9月离家去外地上大学。",
    modelId: null, actionId: randomUUID(), createdAt: now, ...overrides,
  };
}

function diagnostics(overrides: Partial<DiagnosticsSummary> = {}): DiagnosticsSummary {
  return diagnosticsSummarySchema.parse({
    id: randomUUID(), caseId, snapshotId, primaryClusterRetentionRate: .8, leaveOneEventOutRetentionRate: .8,
    leaveOneDomainOutRetentionRate: .8, dateSensitivityRetentionRate: .8, neighborSupportMinutes: 8,
    primarySecondaryMarginPercent: 14, clusterMassRatio: .7, unstableEventIds: [], mostDiscriminatingLayers: ["D9"],
    eventDateSensitivity: [], candidateSplits: [], calculationHash: "d".repeat(64), createdAt: now, ...overrides,
  });
}

function snapshot(range: readonly [string, string], overrides: Partial<CandidateSnapshot> = {}): CandidateSnapshot {
  const [startTime, endTime] = range;
  return {
    id: randomUUID(), caseId, caseVersion: 3, evidenceSetHash: "e".repeat(64), calculationSpecHash: "c".repeat(64),
    algorithmVersion: "rectification-v5-matrix-scoring-1",
    candidates: [{ time: startTime, score: 10, supportingEventIds: [], conflictingEventIds: [] }],
    clusters: [{ rank: 1, startTime, endTime, representativeTime: startTime, widthMinutes: 7, peakScore: 10, scoreMass: 1 }],
    robustness: { neighborSupportMinutes: 8, leaveOneOutRetentionRate: .8, leaveOneDomainOutRetentionRate: .8, dateSensitivityRetentionRate: .8, calculationSpecHashMatched: true },
    canConfirmExactMinute: false, canAcceptRange: true, gateReasons: [], createdAt: now, ...overrides,
  };
}

function targetOpportunity(target: LifeEventRevision): QuestionOpportunity {
  return {
    contractVersion: "semantic-question-v2", opportunityId: randomUUID(), kind: "refine_event_date", domain: target.domain,
    targetEventId: target.eventId, goal: `细化“${target.summary}”的日期。`, requestedFields: ["event_day"], anchors: [target.summary],
    contextFacts: ["日期敏感性较高。"],
    forbiddenMoves: ["switch_target_event", "ask_multiple_questions", "claim_exact_birth_minute", "invent_event", "invent_date", "expose_private_score", "expose_internal_id", "expose_technique_trace"],
    fallbackPrompt: `关于“${target.summary}”，你还记得大概哪一天吗？`, reason: "日期敏感性诊断显示该事件可能改变候选排序。",
    expectedInformationGain: .8, dateSensitivity: .8, candidateSplitRelevance: .5, domainCoverageGain: 0,
    recallEase: .6, novelty: .8, repetitionPenalty: 0, privacyCost: .05, utility: .7, active: true,
  };
}

function validated(opportunity: QuestionOpportunity): ValidatedDecision {
  return {
    decision: { action: "ask_question", opportunityId: opportunity.opportunityId, narrativeFocus: ["latest_event"] },
    mode: "agent", validationIssues: [], selectedOpportunity: opportunity,
  };
}

test("研究院实习被确定性提取为 career/self/month/scoreable", () => {
  const [result] = extractLifeEventEvidence({ rawText: "2020 年 4 月去石油化工研究院实习做研究员。", sourceTurnId: randomUUID(), asOfDate: "2026-07-29" });
  assert.ok(result);
  assert.equal(result.domain, "career");
  assert.equal(result.eventKind, "career_change");
  assert.equal(result.subject, "self");
  assert.equal(result.datePrecision, "month");
  assert.equal(result.dateValue, "2020-04");
  assert.equal(result.scoreability, "scoreable");
  assert.equal(result.scoreable, true);
});

test("month 默认不细化，只有 retention 低于 .65 时才允许细化", () => {
  const internship = event({ domain: "career", eventKind: "career_change", summary: "去石油化工研究院实习做研究员", rawText: "2020年4月去石油化工研究院实习做研究员", dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" } });
  const coveredEvents = [
    internship,
    event({ domain: "education", eventKind: "education_milestone" }),
    event({ domain: "relocation", eventKind: "relocation" }),
    event({ domain: "relationship", eventKind: "relationship_change", relatedPerson: "partner" }),
    event({ domain: "finance", eventKind: "finance_change" }),
    event({ domain: "health_pressure", eventKind: "self_health_event" }),
  ];
  const build = (summary: DiagnosticsSummary | null) => buildQuestionOpportunities({ caseId, events: coveredEvents, turns: [], snapshot: null, diagnostics: summary });
  assert.equal(build(null).some((item) => item.kind === "refine_event_date"), false);
  const sensitivity = (winnerRetentionRate: number, candidateClusterRetentionRate: number) => diagnostics({
    eventDateSensitivity: [{ eventId: internship.eventId, declaredDateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month" }, sampleDates: ["2020-04-01", "2020-04-30"], winnerRetentionRate, scoreVariance: 1, candidateClusterRetentionRate }],
  });
  const sensitiveOpportunities = build(sensitivity(.64, .1));
  assert.equal(sensitiveOpportunities.some((item) => item.kind === "refine_event_date" && item.targetEventId === internship.eventId), true);
  assert.doesNotMatch(sensitiveOpportunities.find((item) => item.kind === "refine_event_date")!.fallbackPrompt, /敏感性|排序|保持率|score/i);
  assert.equal(build(sensitivity(.65, .65)).some((item) => item.kind === "refine_event_date"), false);
});

test("不知道或换方向不产生 pending，也不再生成同 target 机会", () => {
  const target = event({ dateRange: { start: "2016-01-01", end: "2016-12-31", precision: "year", label: "2016年" } });
  const answer = "记不清了，换一个吧。";
  const result = reconcileV4Evidence({ caseId, answer, sourceTurnId: randomUUID(), asOfDate: "2026-07-29", existing: [target], targetEventId: target.eventId });
  assert.equal(result.targetDisposition, "direction_change");
  assert.deepEqual(result.pending, []);
  const opportunities = buildQuestionOpportunities({ caseId, events: [target], turns: [turn({ questionTargetEventId: target.eventId, answer })], snapshot: null, diagnostics: null, targetDisposition: result.targetDisposition, retryTargetEventIds: [target.eventId] });
  assert.equal(opportunities.some((item) => item.targetEventId === target.eventId), false);
  assert.ok(opportunities.some((item) => item.kind === "ask_new_event"));
});

test("无 target 的换方向表达也不会被记为 event_unparsed", () => {
  const result = reconcileV4Evidence({ caseId, answer: "后来有一次搬家，但我记不清时间了，换一个吧。", sourceTurnId: randomUUID(), asOfDate: "2026-07-29", existing: [] });
  assert.equal(result.targetDisposition, "direction_change");
  assert.deepEqual(result.pending, []);
  assert.equal(result.revisions.some((item) => item.scoreability === "scoreable"), false);
});

test("回答新 relocation 不覆盖 education target，原目标最多补问一次", () => {
  const target = event({ dateRange: { start: "2016-01-01", end: "2016-12-31", precision: "year", label: "2016年" } });
  const answer = "2018 年 8 月搬到北京。";
  const assisted = validatedModelAssistedEvidence({
    rawText: answer,
    sourceTurnId: randomUUID(),
    asOfDate: "2026-07-29",
    extraction: { sourceSpan: "2018 年 8 月搬到北京", summary: "搬到北京", domain: "relocation", eventKind: "relocation", subject: "self", relatedPerson: null, dateText: "2018 年 8 月" },
  });
  assert.ok(assisted);
  const result = reconcileV4Evidence({ caseId, answer, sourceTurnId: randomUUID(), asOfDate: "2026-07-29", existing: [target], targetEventId: target.eventId, assistedEvidence: [assisted] });
  assert.equal(result.targetDisposition, "answered_other_event");
  const relocation = result.revisions.find((item) => item.domain === "relocation");
  assert.ok(relocation);
  assert.notEqual(relocation.eventId, target.eventId);
  assert.equal(result.revisions.some((item) => item.eventId === target.eventId), false);
  const firstTurns = [turn({ questionTargetEventId: target.eventId, answer: "2018 年 8 月搬到北京。" })];
  const first = buildQuestionOpportunities({ caseId, events: [target, relocation], turns: firstTurns, snapshot: null, diagnostics: null, targetDisposition: "answered_other_event", retryTargetEventIds: [target.eventId] });
  assert.equal(first.filter((item) => item.kind === "resolve_event_conflict" && item.targetEventId === target.eventId).length, 1);
  const second = buildQuestionOpportunities({ caseId, events: [target, relocation], turns: [...firstTurns, turn({ questionTargetEventId: target.eventId, answer: "2020年又搬到上海。" })], snapshot: null, diagnostics: null, targetDisposition: "answered_other_event", retryTargetEventIds: [target.eventId] });
  assert.equal(second.some((item) => item.kind === "resolve_event_conflict" && item.targetEventId === target.eventId), false);
});

test("Renderer 对切换目标、多问题、出生分钟和内部信息统一回落锚定 fallback", () => {
  const target = event({ summary: "2020年4月研究院实习" });
  const opportunity = targetOpportunity(target);
  const input = { latestAnswer: target.rawText, acceptedEvents: [target], pendingEvidence: [] as PendingEvidence[], snapshot: null, previousSnapshot: null, validated: validated(opportunity) };
  const invalidQuestions = [
    "你后来有没有搬家？",
    "关于2020年4月研究院实习，你还记得具体月份吗？另外后来有没有换工作？",
    "关于2020年4月研究院实习，你是不是05:13出生？",
    "关于2020年4月研究院实习，opportunityId 是什么？",
    "关于2020年4月研究院实习，snapshotId 是什么？",
    "关于2020年4月研究院实习，请告诉我 score。",
    "关于2020年4月研究院实习，D9 显示什么？",
    "关于2020年4月研究院实习，tool call 返回什么？",
  ];
  for (const question of invalidQuestions) {
    assert.equal(validateQuestionRealization(question, opportunity).valid, false, question);
    const message = realizePublicMessage({ acknowledgement: `你提到的是“${target.summary}”。`, candidateUpdate: null, limitation: null, question }, input);
    assert.equal(message.question, opportunity.fallbackPrompt, question);
  }
});

test("稳定候选范围相同不重复提示，实际变化才提示且不确认唯一分钟", () => {
  const previous = snapshot(["05:00", "05:30"]);
  const same = snapshot(["05:00", "05:30"]);
  const changed = snapshot(["05:12", "05:18"]);
  assert.equal(candidateUpdateFor({ snapshot: same, previousSnapshot: previous, decisionAction: "ask_question" }), null);
  const update = candidateUpdateFor({ snapshot: changed, previousSnapshot: previous, decisionAction: "ask_question" });
  assert.ok(update);
  assert.match(update, /05:12.*05:18/);
  assert.doesNotMatch(update, /唯一|确认.*分钟|代表分钟/);
  assert.equal(changed.canConfirmExactMinute, false);
});

test("Builder 的领域排序不受事件输入数组顺序影响", () => {
  const education = event();
  const career = event({ domain: "career", eventKind: "career_change", summary: "2023年开始负责商业巡演经纪公司", rawText: "2023年9月开始负责一家商业巡演经纪公司", dateRange: { start: "2023-09-01", end: "2023-09-30", precision: "month", label: "2023年9月" } });
  const domains = (events: readonly LifeEventRevision[]) => buildQuestionOpportunities({ caseId, events, turns: [], snapshot: null, diagnostics: null }).map((item) => [item.kind, item.domain, item.utility]);
  assert.deepEqual(domains([education, career]), domains([career, education]));
});

test("外地上大学不会被换词提升为迁居问题", () => {
  const education = event({
    summary: "离家去外地上大学",
    rawText: "2016 年 9 月离家去外地上大学",
  });
  const opportunities = buildQuestionOpportunities({
    caseId,
    events: [education],
    turns: [turn({ answer: education.rawText })],
    snapshot: null,
    diagnostics: null,
  });

  assert.notEqual(opportunities[0]?.domain, "relocation");
  const relocation = opportunities.find((item) => item.kind === "ask_new_event" && item.domain === "relocation");
  assert.ok(relocation);
  assert.doesNotMatch(relocation.fallbackPrompt, /搬到新城市|长期离乡|以.*为(?:时间)?参照/);
  assert.match(relocation.fallbackPrompt, /除了.*离家去外地上大学.*搬家或迁居/);

  const repeated = "以“离家去外地上大学”为时间参照，你哪次搬到新城市或长期离乡的年月最确定？";
  assert.equal(validateQuestionRealization(repeated, relocation).valid, false);
  assert.equal(validateQuestionRealization("离家去外地上大学这件事大概发生在哪年哪月？", relocation).valid, false);
  assert.equal(validateQuestionRealization("除了离家去外地上大学，你哪次工作变化发生在哪年哪月？", relocation).valid, false);
  const message = realizePublicMessage({ acknowledgement: "你提到的是 2016 年 9 月离家去外地上大学。", candidateUpdate: null, limitation: null, question: repeated }, {
    latestAnswer: education.rawText,
    acceptedEvents: [education],
    pendingEvidence: [],
    snapshot: null,
    previousSnapshot: null,
    validated: validated(relocation),
  });
  assert.equal(message.question, relocation.fallbackPrompt);
});

test("外地上大学场景的机会排序不受事件数组顺序影响", () => {
  const education = event({
    summary: "离家去外地上大学",
    rawText: "2016 年 9 月离家去外地上大学",
    createdAt: "2026-07-29T02:00:00.000Z",
  });
  const career = event({
    domain: "career",
    eventKind: "career_change",
    summary: "开始第一份工作",
    rawText: "2019 年 7 月开始第一份工作",
    dateRange: { start: "2019-07-01", end: "2019-07-31", precision: "month", label: "2019年7月" },
    createdAt: "2026-07-29T01:00:00.000Z",
  });
  const ranked = (events: readonly LifeEventRevision[]) => buildQuestionOpportunities({
    caseId,
    events,
    turns: [turn({ answer: education.rawText, createdAt: education.createdAt })],
    snapshot: null,
    diagnostics: null,
  }).map((item) => [item.kind, item.domain, item.utility, item.fallbackPrompt]);

  assert.deepEqual(ranked([education, career]), ranked([career, education]));
  assert.doesNotMatch(ranked([education, career]).map((item) => item[3]).join("\n"), /搬到新城市|长期离乡|以.*为(?:时间)?参照/);
});

test("研究院实习后优先延续最新主题，不被旧教育事件的离家关键词拉回迁居问卷", () => {
  const education = event({
    summary: "离家去外地上大学",
    rawText: "2016年9月离家去外地上大学",
    createdAt: "2026-07-29T01:00:00.000Z",
  });
  const career = event({
    domain: "career",
    eventKind: "career_change",
    summary: "去石油化工研究院实习做研究员",
    rawText: "2020年4月去石油化工研究院实习做研究员",
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
    createdAt: "2026-07-29T02:00:00.000Z",
  });
  const opportunities = buildQuestionOpportunities({
    caseId,
    events: [education, career],
    turns: [
      turn({ answer: education.rawText, createdAt: "2026-07-29T01:00:00.000Z" }),
      turn({ answer: career.rawText, createdAt: "2026-07-29T02:00:00.000Z" }),
    ],
    snapshot: null,
    diagnostics: null,
  });

  assert.equal(opportunities.some((item) => item.kind === "refine_event_date"), false);
  assert.equal(opportunities[0]?.kind, "ask_new_event");
  assert.equal(opportunities[0]?.domain, "career");
  assert.match(opportunities[0]?.fallbackPrompt ?? "", /研究院实习/);
  assert.doesNotMatch(opportunities[0]?.fallbackPrompt ?? "", /承接.*请再说一件|哪次搬家、离乡或长期迁居/);
});

test("Renderer 接受锚定最新事件的自然新事件问题并拒绝旧固定模板", () => {
  const latest = event({
    domain: "career",
    eventKind: "career_change",
    summary: "去石油化工研究院实习做研究员",
    rawText: "2020年4月去石油化工研究院实习做研究员",
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
  });
  const opportunity = buildQuestionOpportunities({ caseId, events: [latest], turns: [turn({ answer: latest.rawText })], snapshot: null, diagnostics: null })
    .find((item) => item.kind === "ask_new_event" && item.domain === "career");
  assert.ok(opportunity);
  const naturalQuestion = "研究院实习之后，下一次工作发生明显变化大概是什么时候？";
  const canned = `承接“${latest.summary}”，请再说一件时间相对明确的经历：哪次工作变化的时间你比较确定？`;
  assert.equal(validateQuestionRealization(naturalQuestion, opportunity).valid, true);
  assert.equal(validateQuestionRealization(canned, opportunity).valid, false);
  const message = realizePublicMessage({ acknowledgement: `你提到的是“${latest.summary}”。`, candidateUpdate: null, limitation: null, question: naturalQuestion }, {
    latestAnswer: latest.rawText,
    acceptedEvents: [latest],
    pendingEvidence: [],
    snapshot: null,
    previousSnapshot: null,
    validated: validated(opportunity),
  });
  assert.equal(message.question, naturalQuestion);
  assert.notEqual(message.question, opportunity.fallbackPrompt);
});

test("ask_new_event 领域验证忽略承接 anchor，拒绝实际询问的跨领域事件", () => {
  const latest = event({
    domain: "career",
    eventKind: "career_change",
    summary: "去石油化工研究院实习做研究员",
    rawText: "2020年4月去石油化工研究院实习做研究员",
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
  });
  const opportunity = buildQuestionOpportunities({ caseId, events: [latest], turns: [turn({ answer: latest.rawText })], snapshot: null, diagnostics: null })
    .find((item) => item.kind === "ask_new_event" && item.domain === "career");
  assert.ok(opportunity);

  const result = validateQuestionRealization("研究院实习之后，下一次升学大概发生在什么时候？", opportunity);
  assert.equal(result.valid, false);
  assert.ok(result.issues.includes("new_event_domain_mismatch"));
});

test("ask_new_event 允许明确代词承接并识别教育领域的升学事件", () => {
  const latest = event({
    domain: "career",
    eventKind: "career_change",
    summary: "去石油化工研究院实习做研究员",
    rawText: "2020年4月去石油化工研究院实习做研究员",
    dateRange: { start: "2020-04-01", end: "2020-04-30", precision: "month", label: "2020年4月" },
  });
  const baseOpportunity = buildQuestionOpportunities({ caseId, events: [latest], turns: [turn({ answer: latest.rawText })], snapshot: null, diagnostics: null })
    .find((item) => item.kind === "ask_new_event" && item.domain === "career");
  assert.ok(baseOpportunity);
  const opportunity: QuestionOpportunity = { ...baseOpportunity, domain: "education" };

  for (const reference of ["这次经历", "刚才那段", "你刚说的"]) {
    const result = validateQuestionRealization(`${reference}之后，下一次升学大概发生在什么时候？`, opportunity);
    assert.equal(result.valid, true, `${reference}: ${result.issues.join(",")}`);
  }
});

test("targetEventId 非空时只接受完整真实 anchor，不接受代词或四字片段", () => {
  const target = event({ summary: "2020年4月研究院实习" });
  const opportunity = targetOpportunity(target);

  assert.equal(validateQuestionRealization("关于2020年4月研究院实习，你还记得具体日期吗？", opportunity).valid, true);
  assert.equal(validateQuestionRealization("关于研究院实习，你还记得具体日期吗？", opportunity).valid, false);
  assert.equal(validateQuestionRealization("关于这次经历，你还记得具体日期吗？", opportunity).valid, false);
});

test("Builder 和 Reasoner 按事件创建时间承接最近经历而不是 UUID 顺序", () => {
  const older = event({
    eventId: "ffffffff-ffff-4fff-8fff-ffffffffffff",
    summary: "较早的研究院实习",
    createdAt: "2026-07-29T01:00:00.000Z",
  });
  const newer = event({
    eventId: "00000000-0000-4000-8000-000000000000",
    domain: "relocation",
    eventKind: "relocation",
    summary: "刚提到的搬到北京",
    rawText: "2018年8月搬到北京",
    dateRange: { start: "2018-08-01", end: "2018-08-31", precision: "month", label: "2018年8月" },
    createdAt: "2026-07-29T02:00:00.000Z",
  });
  const opportunities = buildQuestionOpportunities({ caseId, events: [newer, older], turns: [], snapshot: null, diagnostics: null });
  const askNewEvent = opportunities.find((item) => item.kind === "ask_new_event");
  assert.ok(askNewEvent);
  assert.match(askNewEvent.fallbackPrompt, /刚提到的搬到北京/);
  assert.doesNotMatch(askNewEvent.fallbackPrompt, /较早的研究院实习/);

  const state = buildReasonerState({ snapshot: null, diagnostics: diagnostics(), opportunities, recentEvents: [newer, older] });
  assert.equal(state.recentEvents.at(-1)?.summary, "刚提到的搬到北京");
});

test("Reasoner 状态包含最近语义上下文但不包含贡献矩阵", () => {
  const latestEvent = event();
  const opportunity = targetOpportunity(latestEvent);
  const recentTurns = Array.from({ length: 7 }, (_, index) => turn({ answer: `回答${index}` }));
  const pending: PendingEvidence = { id: randomUUID(), caseId, turnId: recentTurns.at(-1)!.id, rawText: "后来去了北京", reasonCode: "date_unresolved", targetEventId: null, resolvedEventId: null, createdAt: now, resolvedAt: null };
  const state = buildReasonerState({ snapshot: snapshot(["05:12", "05:18"]), diagnostics: diagnostics(), opportunities: [opportunity], recentTurns, recentEvents: [latestEvent], currentTarget: latestEvent, targetDisposition: "unresolved", pendingEvidence: [pending], candidateRangeChanged: true });
  assert.equal(state.latestAnswer, "回答6");
  assert.equal(state.recentTurns.length, 6);
  assert.equal(state.recentEvents[0]?.summary, latestEvent.summary);
  assert.equal(state.targetDisposition, "unresolved");
  assert.equal(state.opportunities[0]?.goal, opportunity.goal);
  assert.equal(state.pendingEvidence.count, 1);
  assert.doesNotMatch(JSON.stringify(state), /contribution(?:Matrix| matrix|_matrix)?/i);
});

test("模型辅助提取拒绝发明日期，接受原文连续日期并可进入 Event Ledger", () => {
  const invented = validatedModelAssistedEvidence({
    rawText: "大学毕业后去了北京。", sourceTurnId: randomUUID(), asOfDate: "2026-07-29",
    extraction: { sourceSpan: "大学毕业后去了北京", summary: "大学毕业后去了北京", domain: "relocation", eventKind: "relocation", subject: "self", relatedPerson: null, dateText: "2020年7月" },
  });
  assert.equal(invented, null);
  const normalizedButNotLiteral = validatedModelAssistedEvidence({
    rawText: "２０２２年１１月把生活重心挪到了成都。", sourceTurnId: randomUUID(), asOfDate: "2026-07-29",
    extraction: { sourceSpan: "2022年11月把生活重心挪到了成都", summary: "把生活重心挪到了成都", domain: "relocation", eventKind: "relocation", subject: "self", relatedPerson: null, dateText: "2022年11月" },
  });
  assert.equal(normalizedButNotLiteral, null);
  const rawText = "2022年11月把生活重心挪到了成都。";
  const assisted = validatedModelAssistedEvidence({
    rawText, sourceTurnId: randomUUID(), asOfDate: "2026-07-29",
    extraction: { sourceSpan: "2022年11月把生活重心挪到了成都", summary: "把生活重心挪到了成都", domain: "relocation", eventKind: "relocation", subject: "self", relatedPerson: null, dateText: "2022年11月" },
  });
  assert.ok(assisted);
  assert.equal(assisted.dateValue, "2022-11");
  const reconciled = reconcileV4Evidence({ caseId, answer: rawText, sourceTurnId: randomUUID(), asOfDate: "2026-07-29", existing: [], assistedEvidence: [assisted] });
  assert.ok(reconciled.revisions.some((item) => item.domain === "relocation" && item.scoreability === "scoreable"));
});

test("旧 prompt Opportunity 归一化为 semantic-question-v2", () => {
  const legacyPrompt = "请说一件时间比较明确的经历。";
  const normalized = normalizeQuestionOpportunity({ prompt: legacyPrompt, domain: "career", reason: "历史记录" });
  assert.equal(normalized.contractVersion, "semantic-question-v2");
  assert.equal(normalized.fallbackPrompt, legacyPrompt);
  assert.equal(normalized.domain, "career");
  assert.ok(normalized.opportunityId);
});

test("V6 迁移只更新未完成 Case 版本且不写 active_birth_time", () => {
  const migration = readFileSync(new URL("../supabase/migrations/20260729010000_rectification_agent_v6_versions.sql", import.meta.url), "utf8");
  assert.match(migration, /alter column skill_version set default 'birth-time-rectification-v6'/);
  assert.match(migration, /alter column prompt_version set default 'rectification-agent-v6-1'/);
  assert.match(migration, /where status in \('awaiting_answer', 'processing', 'paused'\)/);
  assert.doesNotMatch(migration, /profiles\s*\.\s*active_birth_time|active_birth_time/i);
});
