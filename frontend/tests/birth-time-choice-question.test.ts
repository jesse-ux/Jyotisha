import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  choiceQuestionGroups,
  choiceSelectionIntent,
  normalizeUnmatchedNote,
} from "../src/lib/birth-time-choice-question-model.ts";
import type { PublicDynamicChoiceQuestion } from "../src/lib/birth-time-dynamic-choice.ts";
import {
  advanceDynamicBirthTimePreview,
  dynamicBirthTimePreview,
} from "../src/lib/birth-time-dynamic-preview.ts";

const question: PublicDynamicChoiceQuestion = {
  questionId: "education-shift",
  prompt: "哪段时间更接近一次明显的学习方向变化？",
  options: [
    { optionId: "early", label: "更接近 2007—2009 年", kind: "primary" },
    { optionId: "late", label: "更接近 2010—2012 年", kind: "primary" },
    { optionId: "unknown", label: "不记得", kind: "unknown" },
    { optionId: "unmatched", label: "都不符合", kind: "unmatched" },
  ],
};

test("click intent submits primary and unknown options immediately", () => {
  const groups = choiceQuestionGroups(question);

  assert.deepEqual(groups.primary.map((option) => option.optionId), ["early", "late"]);
  assert.deepEqual(choiceSelectionIntent(groups.primary[0]), {
    kind: "submit", optionId: "early", effective: true,
  });
  assert.deepEqual(choiceSelectionIntent(groups.unknown), {
    kind: "submit", optionId: "unknown", effective: false,
  });
});

test("unmatched requests clarification without creating scoring evidence", () => {
  const groups = choiceQuestionGroups(question);

  assert.deepEqual(choiceSelectionIntent(groups.unmatched), {
    kind: "submit", optionId: "unmatched", effective: false,
  });
  assert.equal(normalizeUnmatchedNote("  大约是在搬家之后  "), "大约是在搬家之后");
  assert.equal(normalizeUnmatchedNote("甲".repeat(260)).length, 240);
});

test("the rendered component keeps one-click and optional-note semantics", () => {
  const source = readFileSync(
    new URL("../src/components/birth-time-choice-question.tsx", import.meta.url),
    "utf8",
  );

  assert.match(source, /<fieldset/);
  assert.match(source, /<legend/);
  assert.match(source, /onSelect\(intent\.optionId\)/);
  assert.match(source, /maxLength=\{240\}/);
  assert.doesNotMatch(source, /整理为经历草稿|记得的精度|发生时间|第.*\/.*轮/);
  assert.doesNotMatch(source, /required/);
});

test("preview choices expose real local interaction states without authentication", () => {
  const start = dynamicBirthTimePreview();
  const scoring = advanceDynamicBirthTimePreview(start, { kind: "select", optionId: "earlier" });
  const clarification = advanceDynamicBirthTimePreview(start, { kind: "select", optionId: "unmatched" });
  const reframed = advanceDynamicBirthTimePreview(clarification, { kind: "reframe" });
  const terminal = advanceDynamicBirthTimePreview(reframed, { kind: "finish" });

  assert.equal(scoring.nextAction.kind, "score_pending");
  assert.equal(clarification.nextAction.kind, "clarify_unmatched_answer");
  assert.equal(reframed.nextAction.kind, "ask_dynamic_choice");
  assert.equal(terminal.nextAction.kind, "present_low_result");
});

test("dynamic previews cover every visible result and recovery state", () => {
  const expected = new Map([
    ["generating", "generate_dynamic_question"],
    ["question-retry", "retry_question_generation"],
    ["question", "ask_dynamic_choice"],
    ["clarification", "clarify_unmatched_answer"],
    ["scoring", "score_pending"],
    ["scoring-retry", "retry_scoring"],
    ["low", "present_low_result"],
    ["medium", "present_medium_result"],
    ["confirmation", "request_candidate_confirmation"],
    ["ready", "ready"],
    ["paused", "paused"],
  ] as const);

  for (const [state, action] of expected) {
    assert.equal(dynamicBirthTimePreview(state).nextAction.kind, action);
  }
});
