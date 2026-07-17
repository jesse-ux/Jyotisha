import assert from "node:assert/strict";
import test from "node:test";
import { parseJourneyResponse } from "../src/lib/birth-time-journey-client.ts";

const snapshot = {
  state: "rectifying",
  assistantIntent: "start_standard_rectification",
  input: "rectification_questions",
  route: "rectification",
  confidence: null,
  canApply: false,
  activeTime: null,
  reportedRange: { label: "14:00—15:00", startTime: "14:00", endTime: "15:00" },
} as const;

test("journey client parses the sanitized API response", () => {
  const parsed = parseJourneyResponse({
    caseId: "7299894c-10a8-4b45-91d1-339007282c50",
    snapshot,
    questionnaire: {
      questions: [{
        id: "education_environment_shift",
        prompt: "是否有明显学业变化？",
        options: [{ key: "A", label: "明确有" }],
      }],
      samples: [],
      raw: {},
    },
    scoring: null,
  });

  assert.equal(parsed.snapshot.route, "rectification");
  assert.equal(parsed.questionnaire?.questions[0]?.id, "education_environment_shift");
});

test("journey client rejects an API response that tries to apply a rectification result", () => {
  assert.throws(() => parseJourneyResponse({
    caseId: "7299894c-10a8-4b45-91d1-339007282c50",
    snapshot: { ...snapshot, canApply: true, activeTime: "14:24" },
    questionnaire: null,
    scoring: null,
  }));
});
