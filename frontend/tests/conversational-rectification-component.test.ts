import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  canRegenerateRectificationMessage,
  rectificationV4ChatMessages,
  toggleRectificationFeedback,
} from "../src/components/rectification-v4-panel.tsx";
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
  };
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
  assert.match(component, /aria-label="重新生成回答"/);
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

test("processing is an ordinary assistant thinking message after the saved answer", () => {
  const messages = rectificationV4ChatMessages(response({ currentQuestion: null, status: "processing" }), true);
  assert.equal(messages.at(-1)?.role, "assistant");
  assert.equal(messages.at(-1)?.state, "thinking");
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
