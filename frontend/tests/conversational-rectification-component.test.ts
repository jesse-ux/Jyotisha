import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import React from "react";
import { renderToStaticMarkup } from "react-dom/server";
import {
  ConversationalRectificationSurface,
} from "../src/components/conversational-birth-time-rectification.tsx";
import type { ConversationalRectificationController } from "../src/hooks/use-conversational-rectification.ts";
import type { ConversationalRectificationTurn } from "../src/lib/conversational-rectification/contracts.ts";

// The repository keeps JSX in preserve mode for Next.js; direct Node SSR needs the classic global.
Object.assign(globalThis, { React });

const turn: ConversationalRectificationTurn = {
  caseId: "00000000-0000-4000-8000-000000000821",
  journeyProtocol: "conversational-evidence-v3",
  status: "confirming",
  turnVersion: 6,
  narrative: "## 当前判断\n\n**05:18** 只是待验证候选；D9 与 D10 仍需真实经历交叉验证。",
  candidate: {
    status: "ready_for_confirmation",
    representativeTime: "05:18",
    rangeStart: "05:16",
    rangeEnd: "05:20",
  },
  technicalReceipt: {
    calculationVersion: "rectification-technical-v1",
    stableLayers: ["D1"],
    sensitiveLayers: ["D9", "D10"],
    candidateDifferenceRefs: ["consult-d9", "consult-d10"],
  },
  evidenceRequest: {
    domains: ["relationship", "career", "relocation"],
    datePrecision: "month_preferred",
    freeTextAllowed: true,
  },
  evidenceRecap: [{
    id: "00000000-0000-4000-8000-000000000822",
    summary: "开始第一份长期工作",
    dateLabel: "2021 年 7 月",
  }],
  actions: ["answer", "pause", "abandon", "confirm"],
  pendingConsultationQuestion: "我适合什么时候换工作？",
};

function controller(overrides: Partial<ConversationalRectificationController> = {}): ConversationalRectificationController {
  return {
    turn,
    draft: "",
    selectedDomain: null,
    pending: false,
    error: "",
    getSnapshot: () => ({ turn, draft: "", selectedDomain: null, pending: false, error: "" }),
    subscribe: () => () => undefined,
    setDraft: () => undefined,
    selectDomain: () => undefined,
    start: async () => turn,
    resume: async () => turn,
    answer: async () => turn,
    pause: async () => turn,
    abandon: async () => turn,
    confirm: async () => turn,
    ...overrides,
  };
}

test("rich narrative precedes 2–4 domain choices while free text remains available", () => {
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller() },
  ));

  assert.match(markup, /<h2>当前判断<\/h2>/);
  assert.match(markup, /<strong>05:18<\/strong>/);
  assert.ok(markup.indexOf("当前判断") < markup.indexOf("重要关系"));
  assert.equal((markup.match(/data-evidence-domain=/g) ?? []).length, 3);
  assert.match(markup, /<textarea[^>]+id="conversational-rectification-answer"/);
  assert.match(markup, /Ctrl\/⌘ \+ Enter/);
  assert.doesNotMatch(markup, /2006[^<]*2011|BirthTimeChoiceQuestion|birth-time-choice-question/);
});

test("evidence is correctable, technical receipts stay visible, and confirmation is explicit", () => {
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: controller() },
  ));

  assert.match(markup, /已记录的真实经历/);
  assert.match(markup, /2021 年 7 月/);
  assert.match(markup, /更正这条经历：开始第一份长期工作/);
  assert.match(markup, /本轮技术回执/);
  assert.match(markup, /rectification-technical-v1/);
  assert.match(markup, /consult-d9/);
  assert.match(markup, /待确认 · 未验证/);
  assert.match(markup, /确认将 05:18 设为当前排盘时间/);
  assert.match(markup, /不会自动采用/);
  assert.match(markup, /暂停，稍后继续/);
  assert.match(markup, /放弃本次校正/);
});

test("pending markup and responsive CSS expose accessibility contracts", () => {
  const pendingController = controller({
    pending: true,
    draft: "保留中的文字",
    getSnapshot: () => ({
      turn,
      draft: "保留中的文字",
      selectedDomain: "career",
      pending: true,
      error: "",
    }),
  });
  const markup = renderToStaticMarkup(React.createElement(
    ConversationalRectificationSurface,
    { controller: pendingController },
  ));
  const css = readFileSync(new URL("../src/app/globals.css", import.meta.url), "utf8");
  const component = readFileSync(
    new URL("../src/components/conversational-birth-time-rectification.tsx", import.meta.url),
    "utf8",
  );

  assert.match(markup, /aria-busy="true"/);
  assert.match(markup, /<textarea[^>]+disabled=""[^>]*>保留中的文字<\/textarea>/);
  assert.match(markup, /aria-label="生时校正对话"/);
  assert.match(markup, /role="alert"|aria-live="polite"/);
  assert.match(css, /\.conversational-rectification[\s\S]*min-width:\s*0/);
  assert.match(css, /\.conversational-rectification[^}]*overflow-wrap:\s*anywhere/);
  assert.match(css, /\.conversational-rectification button[^}]*min-height:\s*44px/);
  assert.match(css, /\.conversational-rectification[^}]*:focus-visible/);
  assert.match(css, /@media\s*\(max-width:\s*430px\)[\s\S]*\.conversational-rectification/);
  assert.match(component, /确认放弃且不应用候选/);
});
