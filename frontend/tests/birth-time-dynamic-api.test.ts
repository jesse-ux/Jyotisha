import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import { birthTimeGuideRequestSchema } from "../src/lib/birth-time-guide-agent.ts";
import { birthTimeJourneyRequestSchema } from "../src/lib/birth-time-journey-request.ts";
import { parseJourneyResponse } from "../src/lib/birth-time-journey-client.ts";
import { storedDynamicJourneyResponse } from "../src/lib/birth-time-journey-response.ts";
import { dynamicCase, persistedQuestion } from "./birth-time-dynamic-persistence-fixture.ts";

const caseId = "45857b75-4718-4590-aaf5-7113a03ea765";
const actionId = "a9890e09-d535-46f0-9a36-86017515a5a1";

test("choice commands accept only public ids", () => {
  const valid = {
    type: "answer_dynamic_choice",
    caseId,
    actionId,
    turnVersion: 7,
    questionId: persistedQuestion.questionId,
    optionId: persistedQuestion.options[0].optionId,
  };
  assert.equal(birthTimeJourneyRequestSchema.safeParse(valid).success, true);
  for (const field of ["partitionId", "candidateScores", "confidence", "time"] as const) {
    assert.equal(birthTimeJourneyRequestSchema.safeParse({ ...valid, [field]: "forged" }).success, false);
  }
});

test("unmatched context is optional, trimmed, and bounded", () => {
  const valid = {
    type: "reframe_unmatched",
    caseId,
    actionId,
    turnVersion: 8,
    questionId: persistedQuestion.questionId,
    note: "  更像是 2017 年  ",
  };
  const parsed = birthTimeGuideRequestSchema.parse(valid);
  assert.equal(parsed.type === "reframe_unmatched" ? parsed.note : null, "更像是 2017 年");
  assert.equal(birthTimeGuideRequestSchema.safeParse({ ...valid, note: "字".repeat(241) }).success, false);
  assert.equal(birthTimeGuideRequestSchema.safeParse({ ...valid, partitionId: "private" }).success, false);
});

test("dynamic responses preserve the protocol discriminant without private scoring data", () => {
  const response = storedDynamicJourneyResponse(dynamicCase());
  const parsed = parseJourneyResponse(response);

  assert.equal(parsed.journeyProtocol, "dynamic-choice-v2");
  assert.equal(parsed.nextAction.kind, "ask_dynamic_choice");
  const serialized = JSON.stringify(parsed);
  assert.doesNotMatch(serialized, /partitionId|candidateScores|agentContext|candidateModel/);
  assert.throws(() => parseJourneyResponse({ ...response, partitionId: "forged" }));
});

test("dynamic routes authenticate before parsing and dispatch scoped methods", () => {
  const journeyRoute = readFileSync(new URL("../src/app/api/birth-time-journey/route.ts", import.meta.url), "utf8");
  const guideRoute = readFileSync(new URL("../src/app/api/birth-time-guide/route.ts", import.meta.url), "utf8");
  assert.ok(journeyRoute.indexOf("auth.getUser") < journeyRoute.indexOf("requestPayload(request)"));
  assert.ok(guideRoute.indexOf("auth.getUser") < guideRoute.indexOf("requestPayload(request)"));
  assert.match(journeyRoute, /answerDynamicChoice/);
  assert.match(journeyRoute, /pollDynamicScoringJob/);
  assert.match(guideRoute, /generateQuestion/);
  assert.match(guideRoute, /submitUnmatchedContext/);
});
