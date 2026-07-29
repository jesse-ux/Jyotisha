import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  canRegenerateRectificationMessage,
  rectificationV4ChatMessages,
  rectificationPhaseLabel,
  toggleRectificationFeedback,
} from "../src/components/rectification-v4-panel.tsx";
import { applyRectificationV4JobUpdate } from "../src/hooks/use-rectification-v4.ts";
import type { RectificationV4ApiResponse } from "../src/lib/rectification-v4/contracts.ts";

const id = "00000000-0000-4000-8000-000000000901";
const questionId = "00000000-0000-4000-8000-000000000902";
const now = "2026-07-27T00:00:00.000Z";

function response(overrides: Record<string, unknown> = {}): RectificationV4ApiResponse {
  return {
    case: {
      id,
      userId: "00000000-0000-4000-8000-000000000900",
      protocol: "rectification-evidence-v4",
      version: 2,
      status: "awaiting_answer",
      phase: "collecting_evidence",
      calculationSpec: {
        version: "rectification-calculation-spec-v4",
        birthDate: "1997-08-08",
        candidateRange: { start: "04:50", end: "05:10" },
        latitude: 36.419,
        longitude: 114.213,
        timezoneOffsetHours: 8,
        ayanamsa: "lahiri",
        nodeMode: "mean",
        minuteStep: 1,
      },
      calculationSpecHash: "a".repeat(64),
      evidenceSetHash: "b".repeat(64),
      currentQuestion: {
        id: questionId,
        domain: "relocation",
        targetEventId: null,
        prompt: "你提到复读后再次毕业，这段连续变化很清楚。后来还有哪一次环境变化让你印象很深？",
        recallCost: "low",
        reason: "根据对话选择下一条高信息量追问。",
      },
      latestSnapshot: null,
      orchestrationModelId: null,
      narrationModelId: null,
      skillVersion: "birth-time-rectification-v5",
      promptVersion: "rectification-agent-v5-1",
      algorithmVersion: "rectification-v5-matrix-scoring-1",
      deploymentMode: "v5_agent",
      agentMode: "deterministic_fallback",
      featureSnapshotId: null,
      latestDiagnosticsId: null,
      acceptedRange: null,
      createdAt: now,
      updatedAt: now,
      ...overrides,
    },
    job: null,
    events: [],
    analysis: [],
    turns: [{
      id: "00000000-0000-4000-8000-000000000903",
      caseId: id,
      caseVersion: 1,
      questionId: "00000000-0000-4000-8000-000000000904",
      questionDomain: "other",
      questionTargetEventId: null,
      question: "请从你最确定的一段人生经历开始说。",
      answer: "2015年毕业后复读，2016年再次毕业。",
      modelId: "gpt-5.5",
      actionId: "00000000-0000-4000-8000-000000000905",
      createdAt: now,
    }],
  } as unknown as RectificationV4ApiResponse;
}

function analysisTrace(label: string) {
  return {
    status: "completed",
    stages: [{
      phase: "extracting_evidence",
      label,
      status: "completed",
      durationMs: 320,
    }],
    toolCalls: [{
      category: "candidate_engine",
      label: "候选分钟扫描",
      outcome: "succeeded",
      durationMs: 840,
    }],
    techniques: ["Vimshottari Dasha", "D24"],
    reasoningSummary: "现有证据更适合继续收集另一件时间明确的经历。",
    reasoningSource: "provider_summary",
  } as const;
}

test("v4 rectification reuses the ordinary session message list, composer, and model selector", () => {
  const component = readFileSync(new URL("../src/components/rectification-v4-panel.tsx", import.meta.url), "utf8");
  const wrapper = readFileSync(new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url), "utf8");
  const page = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");
  const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

  assert.match(
    component,
    /<>\s*<section className="conversation"[\s\S]*?<\/section>\s*\{showControls && \(\s*<div className="composer-wrap"/,
  );
  assert.match(component, /className="message-list"/);
  assert.match(component, /<ChatMessageRow/);
  assert.match(component, /className="composer-wrap"/);
  assert.match(component, /className="composer"/);
  assert.match(component, /<Textarea/);
  assert.match(component, /<ModelSelector/);
  assert.match(component, /aria-label="赞"/);
  assert.match(component, /aria-label="踩"/);
  assert.match(component, /aria-label="复制回答"/);
  assert.match(component, /aria-label="重新生成回答"/);
  assert.match(component, /<details className="rectification-analysis">/);
  assert.match(component, /<span>分析过程<\/span>/);
  assert.match(
    component,
    /<RectificationAnalysisDetails trace=\{message\.analysisTrace\} \/>[\s\S]*?<RectificationMessageRow[\s\S]*?<div className="rectification-message-actions"/,
  );
  assert.match(component, /caseValue\?\.deploymentMode === "v5_agent"/);
  assert.match(component, /controller\.regenerate\(\)/);
  assert.match(component, /controller\.answer\(answer, props\.selectedModelId \|\| null\)/);
  assert.match(wrapper, /<RectificationV4Panel \{\.\.\.props\} \/>/);
  assert.match(page, /\{!rectificationSurfaceOpen && \(\s*<div className=\{`conversation/);
  assert.match(page, /\{rectificationSurfaceOpen && \(\s*<ConversationalBirthTimeRectification/);
  assert.doesNotMatch(page, /is-rectification/);
  assert.doesNotMatch(component, /rectification-chat/);
  assert.doesNotMatch(css, /\.rectification-chat/);
});

test("V5 Agent feedback is mutually exclusive and regenerate is limited to the current settled assistant question", () => {
  assert.equal(toggleRectificationFeedback(undefined, "up"), "up");
  assert.equal(toggleRectificationFeedback("up", "up"), undefined);
  assert.equal(toggleRectificationFeedback("up", "down"), "down");

  const message = rectificationV4ChatMessages(response(), false).at(-1)!;
  assert.equal(canRegenerateRectificationMessage({
    message,
    currentMessageKey: `rectification-current-${questionId}`,
    deploymentMode: "v5_agent",
    busy: false,
    canAnswer: true,
  }), true);
  assert.equal(canRegenerateRectificationMessage({
    message,
    currentMessageKey: message.renderKey,
    deploymentMode: "v5_shadow",
    busy: false,
    canAnswer: true,
  }), false);
  assert.equal(canRegenerateRectificationMessage({
    message,
    currentMessageKey: message.renderKey,
    deploymentMode: "v5_agent",
    busy: true,
    canAnswer: true,
  }), false);
  assert.equal(canRegenerateRectificationMessage({
    message: { ...message, role: "user" },
    currentMessageKey: message.renderKey,
    deploymentMode: "v5_agent",
    busy: false,
    canAnswer: true,
  }), false);
});

test("turn history and the context-aware next question render as one chat timeline", () => {
  const messages = rectificationV4ChatMessages(response(), false);

  assert.deepEqual(messages.map(({ role, text }) => [role, text]), [
    ["assistant", "请从你最确定的一段人生经历开始说。"],
    ["user", "2015年毕业后复读，2016年再次毕业。"],
    ["assistant", "你提到复读后再次毕业，这段连续变化很清楚。后来还有哪一次环境变化让你印象很深？"],
  ]);
});

test("completed analysis is attached to the next Agent message by source turn", () => {
  const base = response();
  const firstTurn = base.turns[0]!;
  const secondTurn = {
    ...firstTurn,
    id: "00000000-0000-4000-8000-000000000906",
    caseVersion: 2,
    questionId: "00000000-0000-4000-8000-000000000907",
    question: "承接复读后再次毕业，你还记得哪次职业变化的大概时间？",
    answer: "2020年4月去研究院实习。",
    actionId: "00000000-0000-4000-8000-000000000908",
  };
  const firstTrace = analysisTrace("整理第一轮经历");
  const secondTrace = analysisTrace("整理第二轮经历");
  const data = {
    ...base,
    turns: [firstTurn, secondTurn],
    analysis: [
      { sourceTurnId: firstTurn.id, trace: firstTrace },
      { sourceTurnId: secondTurn.id, trace: secondTrace },
    ],
  } as unknown as RectificationV4ApiResponse;

  const assistantMessages = rectificationV4ChatMessages(data, false)
    .filter((message) => message.role === "assistant");

  assert.equal(assistantMessages[0]?.analysisTrace, undefined);
  assert.equal(assistantMessages[1]?.analysisTrace, firstTrace);
  assert.equal(assistantMessages[2]?.analysisTrace, secondTrace);
});

test("legacy and shadow modes do not expose persisted analysis traces", () => {
  const base = response();
  const trace = analysisTrace("不应显示");
  for (const deploymentMode of ["v4_legacy", "v5_shadow"] as const) {
    const data = {
      ...base,
      case: { ...base.case, deploymentMode },
      analysis: [{ sourceTurnId: base.turns[0]!.id, trace }],
    } as unknown as RectificationV4ApiResponse;
    assert.equal(
      rectificationV4ChatMessages(data, false).some((message) => message.analysisTrace),
      false,
      deploymentMode,
    );
  }
});

test("processing follows every server job phase returned by polling", () => {
  const base = response({ currentQuestion: null, status: "processing", phase: "extracting_evidence" });
  const job = {
    id: "00000000-0000-4000-8000-000000000909",
    caseId: id,
    status: "processing",
    phase: "extracting_evidence",
    expectedCaseVersion: 2,
    evidenceSetHash: "b".repeat(64),
    calculationSpecHash: "a".repeat(64),
    errorCode: null,
    createdAt: now,
    updatedAt: now,
  } as const;
  let data = { ...base, job } as unknown as RectificationV4ApiResponse;
  const phases = [
    ["extracting_evidence", "正在整理你刚才提到的经历…"],
    ["planning_question", "正在生成语义问题机会…"],
    ["reasoning", "正在选择下一步动作…"],
    ["rendering", "正在生成安全回复…"],
  ] as const;

  for (const [phase, label] of phases) {
    const updated = applyRectificationV4JobUpdate(data, { ...job, phase });
    assert.ok(updated);
    data = updated;
    const message = rectificationV4ChatMessages(data, true).at(-1);
    assert.equal(message?.role, "assistant");
    assert.equal(message?.state, "thinking");
    assert.equal(message?.text, label);
  }
  assert.equal(rectificationPhaseLabel("checking_robustness"), "正在检查候选范围的稳定性…");
});

test("polling ignores an older job response so the visible phase cannot move backward", () => {
  const base = response({ currentQuestion: null, status: "processing", phase: "rendering" });
  const latest = {
    id: "00000000-0000-4000-8000-000000000909",
    caseId: id,
    status: "processing",
    phase: "rendering",
    expectedCaseVersion: 2,
    evidenceSetHash: "b".repeat(64),
    calculationSpecHash: "a".repeat(64),
    errorCode: null,
    createdAt: now,
    updatedAt: "2026-07-27T00:00:02.000Z",
  } as const;
  const data = { ...base, job: latest } as unknown as RectificationV4ApiResponse;
  const stale = { ...latest, phase: "planning_question" as const, updatedAt: "2026-07-27T00:00:01.000Z" };
  assert.equal(applyRectificationV4JobUpdate(data, stale)?.job?.phase, "rendering");
});

test("analysis details render only public labels and preserve the message action icons", () => {
  const component = readFileSync(new URL("../src/components/rectification-v4-panel.tsx", import.meta.url), "utf8");
  const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

  assert.match(component, /\{stage\.label\}/);
  assert.match(component, /\{toolCall\.label\}/);
  assert.match(component, /trace\.techniques\.join\("、"\)/);
  assert.match(component, /trace\.reasoningSource === "provider_summary"/);
  assert.doesNotMatch(component, />\{stage\.phase\}</);
  assert.doesNotMatch(component, />\{toolCall\.category\}</);
  assert.doesNotMatch(component, />\{item\.sourceTurnId\}</);
  assert.match(component, /<ThumbsUp aria-hidden="true" \/>/);
  assert.match(component, /<ThumbsDown aria-hidden="true" \/>/);
  assert.match(component, /<Copy aria-hidden="true" \/>/);
  assert.match(component, /<RotateCcw aria-hidden="true" \/>/);
  assert.match(css, /\.rectification-analysis > summary/);
  assert.doesNotMatch(component, /candidateScore|contributionMatrix|opportunityId|snapshotId/);
});

test("range messages never claim an exact confirmed birth minute", () => {
  const rangeReady = response({
    status: "range_ready",
    phase: "complete",
    currentQuestion: null,
    latestSnapshot: {
      clusters: [{ startTime: "05:26", endTime: "05:30" }],
      canAcceptRange: true,
    },
  });
  const candidateText = rectificationV4ChatMessages(rangeReady, false).at(-1)?.text ?? "";
  assert.match(candidateText, /05:26–05:30/);
  assert.match(candidateText, /候选范围/);
  assert.match(candidateText, /不是已确认的出生分钟/);

  const acceptedText = rectificationV4ChatMessages(response({
    status: "range_ready",
    phase: "complete",
    currentQuestion: null,
    acceptedRange: { start: "05:26", end: "05:30" },
  }), false).at(-1)?.text ?? "";
  assert.match(acceptedText, /原出生时间没有被自动改写/);
});

test("the retired questionnaire panel and fixed-domain controls are absent", () => {
  const component = readFileSync(new URL("../src/components/rectification-v4-panel.tsx", import.meta.url), "utf8");
  const wrapper = readFileSync(new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url), "utf8");
  const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");

  for (const retired of [
    "生时校正 · 事件证据法",
    "rectification-v4-evidence-grid",
    "支持这个范围的经历",
    "ConversationalRectificationSurface",
  ]) {
    assert.doesNotMatch(component, new RegExp(retired));
    assert.doesNotMatch(wrapper, new RegExp(retired));
  }
  assert.doesNotMatch(css, /Birth-time rectification V4|\.rectification-v4-panel/);
});
