import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { guidedTurnIdentity } from "../src/lib/birth-time-guided-turn-identity.ts";

const read = (path: string) => readFileSync(new URL(path, import.meta.url), "utf8");
const rectificationSource = read("../src/components/birth-time-rectification.tsx");
const turnSource = read("../src/components/birth-time-guide-turn.tsx");
const draftSource = read("../src/components/birth-time-evidence-draft-card.tsx");
const candidateSource = read("../src/components/birth-time-candidate-result.tsx");
const hookSource = read("../src/hooks/use-birth-time-guided-journey.ts");
const automaticEffectsSource = read("../src/hooks/use-birth-time-automatic-journey-effects.ts");

test("guided rectification renders exactly the persisted action, never a questionnaire slice", () => {
  assert.match(rectificationSource, /journey\.nextAction/);
  assert.doesNotMatch(rectificationSource, /questions\.slice\(0, 3\)/);
  assert.doesNotMatch(rectificationSource, /nextRoundQuestions/);
  assert.match(turnSource, /说出大概年份也可以/);
});

test("each persisted question has a stable remount identity so skipped input cannot leak", () => {
  assert.equal(guidedTurnIdentity(3, "education_entry"), "3:education_entry");
  assert.notEqual(
    guidedTurnIdentity(3, "education_entry"),
    guidedTurnIdentity(4, "relationship_entry"),
  );
  assert.match(rectificationSource, /key=\{guidedTurnIdentity\(props\.journey\.turnVersion, action\.question\.questionId\)\}/);
});

test("draft review is explicit, domain locked, and incomplete confirmation stays disabled", () => {
  assert.match(draftSource, /确认并用于校正/);
  assert.match(draftSource, /disabled=\{props\.pending \|\| !isValid\}/);
  assert.match(draftSource, /domainLabels\[props\.draft\.domain\]/);
  assert.doesNotMatch(draftSource, /name=["']domain/);
  assert.match(hookSource, /reviseBirthTimeEvidenceDraft/);
  assert.match(hookSource, /confirmBirthTimeEvidenceDraft/);
});

test("guided orchestration owns fallback copy, unique actions, polling, and retry", () => {
  assert.match(automaticEffectsSource, /fallbackQuestionCopy/);
  assert.match(automaticEffectsSource, /requestBirthTimeGuidePrompt/);
  assert.match(automaticEffectsSource, /crypto\.randomUUID\(\)/);
  assert.match(automaticEffectsSource, /runBirthTimeScoringPoll/);
  assert.match(hookSource, /retry_scoring/);
  assert.match(automaticEffectsSource, /AbortController/);
});

test("candidate UI is nextAction-gated and keeps application boundary explicit", () => {
  assert.match(candidateSource, /present_medium_result/);
  assert.match(candidateSource, /request_candidate_confirmation/);
  assert.match(candidateSource, /ready/);
  assert.match(candidateSource, /候选时间/);
  assert.match(candidateSource, /当前排盘使用时间/);
  assert.doesNotMatch(candidateSource, /真实出生分钟/);
});

test("candidate confirmation and ready copy keep semantic time phrases intact", () => {
  assert.match(candidateSource, /<span className="phrase-nowrap">当前排盘使用时间<\/span>已更新为/);
  assert.match(candidateSource, /<span className="phrase-nowrap">原始填报时间<\/span>仍已保留/);
  assert.match(candidateSource, /<span className="phrase-nowrap">原始填报时间<\/span>仍会保留/);
});

test("guided controls expose live status and minimum target classes", () => {
  assert.match(turnSource, /aria-live=["']polite/);
  assert.match(draftSource, /role=["']alert/);
  assert.match(turnSource, /birth-time-guided-action/);
  assert.match(candidateSource, /birth-time-guided-action/);
});
