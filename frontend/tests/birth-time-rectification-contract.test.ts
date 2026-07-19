import assert from "node:assert/strict";
import test from "node:test";
import {
  guidedBirthTimePreview,
  isGuidedBirthTimePreview,
} from "../src/lib/birth-time-guided-preview.ts";

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
