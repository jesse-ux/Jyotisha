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

test("dynamic responses project one exact public shape", () => {
  const stored = {
    ...dynamicCase(),
    questionnaire: { questions: [], samples: [], raw: { candidateVector: [0.4, 0.6] } },
    scoring: {
      answeredCount: 1,
      candidateClusterRankings: [{ cluster: "05:00", score: 9 }],
      raw: { candidateVector: [0.4, 0.6] },
      nextRound: null,
      nextRoundQuestions: [],
    },
    answers: { legacy_private_answer: "A" as const },
    lifeEvents: [{
      id: "ec4ab5f0-829c-468a-90ea-42842f9f70d3",
      domain: "career" as const,
      precision: "year" as const,
      date: "2020",
    }],
  };
  const response = storedDynamicJourneyResponse(stored);
  const parsed = parseJourneyResponse(response);

  assert.deepEqual(Object.keys(parsed).sort(), [
    "answers", "candidateResult", "caseId", "evidenceDraft", "journeyProtocol",
    "lifeEvents", "nextAction", "permissions", "progress", "questionnaire",
    "scoring", "snapshot", "turnVersion",
  ]);
  assert.equal(parsed.journeyProtocol, "dynamic-choice-v2");
  assert.deepEqual({
    questionnaire: parsed.questionnaire,
    scoring: parsed.scoring,
    answers: parsed.answers,
    lifeEvents: parsed.lifeEvents,
  }, { questionnaire: null, scoring: null, answers: {}, lifeEvents: [] });
});

test("dynamic response parsing rejects private legacy and candidate payloads", () => {
  const response = storedDynamicJourneyResponse(dynamicCase());
  const scoring = {
    answeredCount: 1,
    candidateClusterRankings: [{ cluster: "05:00", score: 9 }],
    raw: { candidateVectors: { "05:00": [0.4, 0.6] } },
    nextRound: null,
    nextRoundQuestions: [],
  };
  const privatePayloads = [
    { ...response, scoring },
    { ...response, questionnaire: { questions: [], samples: [], raw: { candidateVectors: [1] } } },
    { ...response, answers: { hidden: "A" } },
    { ...response, lifeEvents: [{ id: "ec4ab5f0-829c-468a-90ea-42842f9f70d3", domain: "career", precision: "year", date: "2020" }] },
    { ...response, candidateModel: { candidates: ["05:10"] } },
    { ...response, currentChoiceQuestion: persistedQuestion },
    { ...response, partitionId: "window-a" },
    { ...response, nextAction: { ...response.nextAction, question: {
      ...persistedQuestion,
      options: persistedQuestion.options,
    } } },
  ];

  for (const payload of privatePayloads) assert.throws(() => parseJourneyResponse(payload));
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
