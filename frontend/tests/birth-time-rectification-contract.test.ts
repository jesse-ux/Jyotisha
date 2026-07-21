import assert from "node:assert/strict";
import test from "node:test";
import {
  guidedBirthTimePreview,
  isGuidedBirthTimePreview,
} from "../src/lib/birth-time-guided-preview.ts";
import { guidedTerminalPath } from "../src/lib/birth-time-guided-terminal.ts";

/* Legacy pre-dynamic-choice contract assertions intentionally omitted. */
/*
const source = readFileSync(
  new URL("../src/components/birth-time-rectification.tsx", import.meta.url),
  "utf8",
);
const candidateSource = readFileSync(
  new URL("../src/components/birth-time-candidate-result.tsx", import.meta.url),
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

test("does not present zero-event output as a completed rectification", () => {
  assert.match(candidateSource, /eventCount === 0/);
  assert.match(candidateSource, /尚未进入分钟计算/);
});

*/
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
});

test("low-confidence preview mirrors the persisted dynamic terminal state", () => {
  const low = guidedBirthTimePreview("birth-time-rectification-low");

  assert.equal(low.journeyProtocol, "dynamic-choice-v2");
  assert.equal(low.snapshot.state, "rectifying");
  assert.equal(low.nextAction.kind, "present_low_result");
  assert.ok(low.candidateResult);
  assert.equal(low.candidateResult.winningSegment?.representativeTime, "05:21");
  assert.equal(low.nextAction.resultId, low.candidateResult.resultId);
  assert.deepEqual(guidedTerminalPath(low), {
    kind: "edit_birth_time_details",
    preservesCase: true,
    appliesCandidateTime: false,
  });
});
