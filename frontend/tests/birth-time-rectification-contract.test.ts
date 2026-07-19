import assert from "node:assert/strict";
import test from "node:test";
import {
  guidedBirthTimePreview,
  isGuidedBirthTimePreview,
} from "../src/lib/birth-time-guided-preview.ts";
import { guidedTerminalPath } from "../src/lib/birth-time-guided-terminal.ts";

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
  assert.equal(low.nextAction.resultId, low.candidateResult.resultId);
  assert.deepEqual(guidedTerminalPath(low), {
    kind: "complete_with_candidate",
    time: low.candidateResult.winningSegment?.representativeTime,
    preservesCase: true,
    appliesCandidateTime: true,
  });
});
