import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  createIdentityRequestCache,
  publishCurrentJourney,
  scheduleCancellableStart,
} from "../src/lib/birth-time-guided-effect-coordinator.ts";
import { confirmReviewedBirthTimeDraft } from "../src/lib/birth-time-guided-draft-confirmation.ts";
import { guidedTerminalPath } from "../src/lib/birth-time-guided-terminal.ts";
import { parseJourneyResponse } from "../src/lib/birth-time-journey-client.ts";
import { dynamicBirthTimePreview } from "../src/lib/birth-time-dynamic-preview.ts";
import { guidedBirthTimePreview } from "../src/lib/birth-time-guided-preview.ts";

test("draft revision publishes its new version before confirmation can fail", async () => {
  const original = guidedBirthTimePreview("birth-time-rectification-draft");
  const revised = parseJourneyResponse({
    ...original,
    turnVersion: original.turnVersion + 1,
    evidenceDraft: { ...original.evidenceDraft, precision: "month", date: "2008-09" },
  });
  const published: typeof original[] = [];
  await assert.rejects(confirmReviewedBirthTimeDraft({
    turn: original,
    precision: "month",
    date: "2008-09",
  }, {
    revise: async () => revised,
    publish: (turn) => { published.push(turn); },
    confirm: async () => { throw new TypeError("response unavailable"); },
  }));

  assert.deepEqual(published, [revised]);
});

test("low without a result and saved medium both return to declared-time editing safely", () => {
  const dynamicLow = dynamicBirthTimePreview("low");
  const low = guidedBirthTimePreview("birth-time-rectification-low");
  const nullResultLow = parseJourneyResponse({
    ...low,
    candidateResult: null,
    nextAction: { kind: "present_low_result", resultId: null },
  });
  const saved = guidedBirthTimePreview("birth-time-rectification-saved");

  assert.equal(dynamicLow.candidateResult, null);
  assert.deepEqual(guidedTerminalPath(nullResultLow), {
    kind: "edit_birth_time_details",
    preservesCase: true,
    appliesCandidateTime: false,
  });
  assert.deepEqual(guidedTerminalPath(saved), {
    kind: "edit_birth_time_details",
    preservesCase: true,
    appliesCandidateTime: false,
  });
});

test("dynamic medium terminal preserves its candidate range without direct adoption", () => {
  const medium = dynamicBirthTimePreview("medium");

  assert.deepEqual(guidedTerminalPath(medium), {
    kind: "edit_birth_time_details",
    preservesCase: true,
    appliesCandidateTime: false,
  });
});

test("candidate completion hook cannot invoke the legacy endpoint for dynamic turns", () => {
  const hookSource = readFileSync(new URL("../src/hooks/use-birth-time-guided-journey.ts", import.meta.url), "utf8");
  assert.doesNotMatch(hookSource, /completeBirthTimeCandidate|completeCandidate/);
});

test("request identity cache and scheduled polling deduplicate Strict Mode starts", async () => {
  const cache = createIdentityRequestCache<number>();
  let loads = 0;
  const load = async () => { loads += 1; return 7; };
  assert.equal(await cache.run("case:1:question", load), 7);
  assert.equal(await cache.run("case:1:question", load), 7);
  assert.equal(loads, 1);

  let starts = 0;
  const cancel = scheduleCancellableStart(() => { starts += 1; });
  cancel();
  await new Promise((resolve) => setTimeout(resolve, 5));
  assert.equal(starts, 0);
  scheduleCancellableStart(() => { starts += 1; });
  await new Promise((resolve) => setTimeout(resolve, 5));
  assert.equal(starts, 1);
});

test("a failed generation identity remains retryable", async () => {
  const cache = createIdentityRequestCache<number>();
  let attempts = 0;
  await assert.rejects(cache.run("case:4", async () => {
    attempts += 1;
    throw new TypeError("offline");
  }));

  assert.equal(await cache.run("case:4", async () => {
    attempts += 1;
    return 8;
  }), 8);
  assert.equal(attempts, 2);
});

test("a resolved mutation cannot publish over a changed case or version", () => {
  const expected = guidedBirthTimePreview("birth-time-rectification");
  const current = parseJourneyResponse({ ...expected, turnVersion: expected.turnVersion + 1 });
  let publishes = 0;
  assert.equal(publishCurrentJourney({
    expected,
    current,
    next: guidedBirthTimePreview("birth-time-rectification-draft"),
    publish: () => { publishes += 1; },
  }), false);
  assert.equal(publishes, 0);
});

test("ready completion is explicit and terminal low has no finish mutation", () => {
  const hookSource = readFileSync(new URL("../src/hooks/use-birth-time-guided-journey.ts", import.meta.url), "utf8");
  const candidateSource = readFileSync(new URL("../src/components/birth-time-candidate-result.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(hookSource, /turn\.nextAction\.kind === "ready"\) onReady/);
  assert.match(candidateSource, /acknowledgeReady/);
  assert.doesNotMatch(candidateSource, /controller\.finish/);
  assert.doesNotMatch(hookSource, /completeGuidedBirthTimeCandidate/);
  assert.doesNotMatch(hookSource, /completeCandidate:/);
});

test("unconfirmed terminal candidates preserve the range without offering direct adoption", () => {
  const candidateResultSource = readFileSync(new URL("../src/components/birth-time-candidate-result.tsx", import.meta.url), "utf8");
  const choiceQuestionSource = readFileSync(new URL("../src/components/birth-time-choice-question.tsx", import.meta.url), "utf8");
  const rectificationSource = readFileSync(new URL("../src/components/birth-time-rectification.tsx", import.meta.url), "utf8");
  const legacyRectificationSource = readFileSync(new URL("../src/components/birth-time-legacy-rectification.tsx", import.meta.url), "utf8");

  assert.match(candidateResultSource, /尚未达到采用条件/);
  assert.match(candidateResultSource, /补充资料并重新评估/);
  assert.doesNotMatch(candidateResultSource, /采用 \$\{path\.time\} 并进入对话/);
  assert.doesNotMatch(candidateResultSource, /birth-time-next-step/);
  assert.match(rectificationSource, /error=\{error\}/);
  assert.match(rectificationSource, /const childOwnsError = action\.kind === "ask_dynamic_choice"\s*\|\| action\.kind === "clarify_unmatched_answer"/);
  assert.match(rectificationSource, /error && !showsCandidate && !childOwnsError/);
  assert.equal(choiceQuestionSource.match(/role="alert"/g)?.length, 1);
  assert.match(legacyRectificationSource, /error=\{error\}/);
  assert.match(legacyRectificationSource, /error && !showsCandidate/);
});

test("terminal CJK copy stays intact while homepage candidates remain unconfirmed in v3", () => {
  const candidateResultSource = readFileSync(new URL("../src/components/birth-time-candidate-result.tsx", import.meta.url), "utf8");
  const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(candidateResultSource, /候选范围已保留，但当前证据不足以将具体分钟写入当前排盘时间。补充经历后可重新评估。/);
  assert.match(pageSource, /未确认；\$\{birthTimeConsultationOptionsCopy\(profile\)\}/);
  assert.match(pageSource, /<ConversationalBirthTimeRectification/);
  assert.doesNotMatch(pageSource, /当前使用候选时间排盘/);
});

test("completed rectification transcript does not repeat the birth place turn", () => {
  const pageSource = readFileSync(new URL("../src/app/page.tsx", import.meta.url), "utf8");

  assert.match(
    pageSource,
    /\{!profileComplete && onboardingStep === "rectification" && selectedBirthPlace\(profileDraft\)/,
  );
});

test("journey turn implementation stays within the 250 pure-LOC boundary", () => {
  const source = readFileSync(new URL("../src/lib/birth-time-journey-turn.ts", import.meta.url), "utf8");
  const pureLines = source.split("\n").filter((line) => {
    const trimmed = line.trim();
    return trimmed.length > 0 && !trimmed.startsWith("//");
  });
  assert.ok(pureLines.length <= 250, `birth-time-journey-turn.ts has ${pureLines.length} pure LOC`);
});
