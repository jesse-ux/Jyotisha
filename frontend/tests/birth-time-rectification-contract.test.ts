import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  guidedBirthTimePreview,
  isGuidedBirthTimePreview,
} from "../src/lib/birth-time-guided-preview.ts";

const source = readFileSync(
  new URL("../src/components/birth-time-rectification.tsx", import.meta.url),
  "utf8",
);
const legacySource = readFileSync(
  new URL("../src/components/birth-time-legacy-rectification.tsx", import.meta.url),
  "utf8",
);
const pageSource = readFileSync(
  new URL("../src/app/page.tsx", import.meta.url),
  "utf8",
);
const storeSource = readFileSync(
  new URL("../src/lib/birth-time-journey-store.ts", import.meta.url),
  "utf8",
);
const routeSource = readFileSync(
  new URL("../src/app/api/birth-time-journey/route.ts", import.meta.url),
  "utf8",
);
const stylesSource = readFileSync(
  new URL("../src/app/globals.css", import.meta.url),
  "utf8",
);

test("rectification UI is driven only by the persisted guided action", () => {
  assert.match(source, /journey\.nextAction/);
  assert.doesNotMatch(source, /questions\.slice\(0, 3\)/);
  assert.doesNotMatch(source, /nextRoundQuestions/);
});

test("development previews cover every guided state with legal persisted actions", () => {
  const expectedActions = new Map([
    ["birth-time-rectification", "ask_dynamic_choice"],
    ["birth-time-rectification-draft", "review_evidence_draft"],
    ["birth-time-rectification-score-pending", "score_pending"],
    ["birth-time-rectification-retry", "retry_scoring"],
    ["birth-time-rectification-adaptive", "ask_adaptive_evidence"],
    ["birth-time-rectification-low", "present_low_result"],
    ["birth-time-rectification-result", "present_medium_result"],
    ["birth-time-rectification-saved", "candidate_saved"],
    ["birth-time-rectification-confirmation", "request_candidate_confirmation"],
    ["birth-time-rectification-ready", "ready"],
  ]);
  for (const [mode, action] of expectedActions) {
    assert.equal(isGuidedBirthTimePreview(mode), true);
    assert.equal(guidedBirthTimePreview(mode).nextAction.kind, action);
  }
  assert.equal(guidedBirthTimePreview("birth-time-rectification").journeyProtocol, "dynamic-choice-v2");
  assert.match(pageSource, /guidedBirthTimePreview\(previewMode\)/);
});

test("journey store keeps scored candidates server-owned until confirmation", () => {
  assert.match(storeSource, /async saveCandidateResult\(value\)/);
  assert.match(storeSource, /life_events: value\.lifeEvents/);
  assert.match(storeSource, /candidate_result: value\.candidateResult/);
  assert.match(storeSource, /async confirmCandidate\(value\)/);
  assert.match(storeSource, /confirm_birth_time_candidate/);
});

test("journey route exposes only structured evidence and guarded candidate actions", () => {
  assert.match(routeSource, /birthTimeJourneyRequestSchema\.safeParse/);
  assert.match(
    routeSource,
    /if \(!parsed\.success\) \{[\s\S]*?status: 400/,
    "invalid structured input must stop at the route boundary before service dispatch",
  );
  assert.match(routeSource, /service\.submitLifeEvents/);
  assert.match(routeSource, /service\.confirmCandidate/);
  assert.match(routeSource, /service\.confirmEvidenceDraft/);
  assert.match(routeSource, /service\.skipEvidenceQuestion/);
  assert.match(routeSource, /service\.pause/);
  assert.match(routeSource, /service\.finishWithCurrentRange/);
  assert.match(routeSource, /GuidedCandidateActionError && error\.reason === "case_not_found"\)[\s\S]*status: 404/);
});

test("declared-time edits preserve the current journey until the revised profile is submitted", () => {
  assert.match(pageSource, /birthTimeRevisionPending\.current = true/);
  assert.match(
    pageSource,
    /await persistProfile\(profileDraft\);[\s\S]*?if \(birthTimeRevisionPending\.current\) \{[\s\S]*?await assessSavedBirthTime\(profileDraft\)/,
  );
  assert.doesNotMatch(
    pageSource.match(/function editDeclaredBirthTimeDetails\(\) \{[\s\S]*?\n  \}/)?.[0] ?? "",
    /setBirthTimeJourney\(null\)/,
  );
});

test("rectification renders draft review and candidates only from nextAction", () => {
  assert.match(legacySource, /action\.kind === "review_evidence_draft"/);
  assert.match(legacySource, /<BirthTimeEvidenceDraftCard/);
  assert.doesNotMatch(source, /BirthTimeEvidenceDraftCard|BirthTimeGuideTurn/);
  assert.match(source, /<BirthTimeChoiceQuestion/);
  assert.match(source, /<BirthTimeCandidateResult/);
  assert.match(pageSource, /controller=\{birthTimeGuided\}/);
  assert.doesNotMatch(pageSource, /submitBirthTimeLifeEvents/);
  assert.doesNotMatch(pageSource, /confirmBirthTimeCandidate/);
});

test("rectification keeps short Chinese evidence phrases intact on mobile", () => {
  assert.match(pageSource, /phraseSafe=\{onboardingStep === "rectification"\}/);
  assert.match(stylesSource, /\.onboarding-message\.is-phrase-safe/);
  assert.match(stylesSource, /\.onboarding-message \.message-markdown p[\s\S]*?word-break: auto-phrase/);
  assert.match(stylesSource, /\.birth-time-evidence-note[\s\S]*?word-break: keep-all/);
  assert.match(stylesSource, /\.birth-time-assistant-intent[\s\S]*?word-break: keep-all/);
});
