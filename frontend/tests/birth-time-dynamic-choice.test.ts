import assert from "node:assert/strict";
import { readdirSync, readFileSync } from "node:fs";
import { join } from "node:path";
import test from "node:test";
import { publicDynamicChoiceQuestionSchema } from "../src/lib/birth-time-dynamic-choice.ts";
import {
  persistedDynamicChoiceQuestionSchema,
  toPublicDynamicChoiceQuestion,
} from "../src/lib/birth-time-dynamic-choice-internal.ts";
import { dynamicJourneyTurnStateSchema, journeyTurnStateSchema } from "../src/lib/birth-time-journey-turn-protocol.ts";

const internalQuestion = {
  questionId: "11111111-1111-4111-8111-111111111111",
  opportunityId: "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa",
  dimensionCode: "career_change",
  estimatedInformationGain: 0.7,
  scoringVersion: "birth-time-choice-scoring-v2",
  source: "fallback",
  questionFingerprint: "question-fingerprint",
  candidatePartitionFingerprint: "partition-fingerprint",
  prompt: "哪一个时间段更接近这次工作变化？",
  options: [
    {
      optionId: "22222222-2222-4222-8222-222222222222",
      label: "2018—2020 年",
      kind: "primary",
      partitionId: "career-2018-2020",
      candidateScores: { "09:00": 0.8 },
    },
    {
      optionId: "33333333-3333-4333-8333-333333333333",
      label: "2021—2023 年",
      kind: "primary",
      partitionId: "career-2021-2023",
      candidateScores: { "09:30": 0.6 },
    },
    {
      optionId: "44444444-4444-4444-8444-444444444444",
      label: "不确定 / 不记得",
      kind: "unknown",
      partitionId: null,
      candidateScores: null,
    },
    {
      optionId: "55555555-5555-4555-8555-555555555555",
      label: "都不符合",
      kind: "unmatched",
      partitionId: null,
      candidateScores: null,
    },
  ],
} as const;

function sourceFiles(directory: string): readonly string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const path = join(directory, entry.name);
    return entry.isDirectory() ? sourceFiles(path) : [path];
  });
}

test("public questions never expose partition ids", () => {
  const parsed = publicDynamicChoiceQuestionSchema.parse({
    questionId: "11111111-1111-4111-8111-111111111111",
    prompt: "哪一个时间段更接近这次工作变化？",
    options: [
      { optionId: "22222222-2222-4222-8222-222222222222", label: "2018—2020 年", kind: "primary" },
      { optionId: "33333333-3333-4333-8333-333333333333", label: "2021—2023 年", kind: "primary" },
      { optionId: "44444444-4444-4444-8444-444444444444", label: "不确定 / 不记得", kind: "unknown" },
      { optionId: "55555555-5555-4555-8555-555555555555", label: "都不符合", kind: "unmatched" },
    ],
  });

  assert.equal("partitionId" in parsed.options[0], false);
  assert.equal(publicDynamicChoiceQuestionSchema.safeParse({
    ...parsed,
    options: [{ ...parsed.options[0], partitionId: "private" }, ...parsed.options.slice(1)],
  }).success, false);
});

test("public questions enforce the shared prompt limit", () => {
  const publicQuestion = toPublicDynamicChoiceQuestion(internalQuestion);
  const promptWithLength = (length: number) => `${"问".repeat(length - 1)}？`;

  assert.equal(publicDynamicChoiceQuestionSchema.safeParse({
    ...publicQuestion,
    prompt: promptWithLength(120),
  }).success, true);
  assert.equal(publicDynamicChoiceQuestionSchema.safeParse({
    ...publicQuestion,
    prompt: promptWithLength(121),
  }).success, false);
});

test("internal primary choices require a server partition", () => {
  assert.equal(persistedDynamicChoiceQuestionSchema.safeParse(internalQuestion).success, true);
  assert.equal(persistedDynamicChoiceQuestionSchema.safeParse({
    ...internalQuestion,
    options: internalQuestion.options.map((option) => option.kind === "primary"
      ? { optionId: option.optionId, label: option.label, kind: option.kind, partitionId: null }
      : option),
  }).success, false);
});

test("choice questions require a bounded complete option set", () => {
  assert.equal(publicDynamicChoiceQuestionSchema.safeParse({
    questionId: "11111111-1111-4111-8111-111111111111",
    prompt: "哪一个时间段更接近这次工作变化？",
    options: [
      { optionId: "22222222-2222-4222-8222-222222222222", label: "2018—2020 年", kind: "primary" },
      { optionId: "44444444-4444-4444-8444-444444444444", label: "不确定 / 不记得", kind: "unknown" },
      { optionId: "55555555-5555-4555-8555-555555555555", label: "都不符合", kind: "unmatched" },
    ],
  }).success, false);
});

test("dynamic schemas accept opaque server-issued identifiers", () => {
  const publicQuestion = {
    questionId: "question-career-window",
    prompt: "哪一个时间段更接近这次工作变化？",
    options: [
      { optionId: "window-a", label: "2018—2020 年", kind: "primary" },
      { optionId: "window-b", label: "2021—2023 年", kind: "primary" },
      { optionId: "unknown", label: "不确定 / 不记得", kind: "unknown" },
      { optionId: "unmatched", label: "都不符合", kind: "unmatched" },
    ],
  };

  assert.equal(publicDynamicChoiceQuestionSchema.safeParse(publicQuestion).success, true);
  assert.equal(persistedDynamicChoiceQuestionSchema.safeParse({
    ...internalQuestion,
    ...publicQuestion,
    opportunityId: "career-window",
    options: [
      { ...publicQuestion.options[0], partitionId: "window-a", candidateScores: { "09:00": 0.8 } },
      { ...publicQuestion.options[1], partitionId: "window-b", candidateScores: { "09:30": 0.6 } },
      { ...publicQuestion.options[2], partitionId: null, candidateScores: null },
      { ...publicQuestion.options[3], partitionId: null, candidateScores: null },
    ],
  }).success, true);
});

test("public code never imports the internal dynamic choice contract", () => {
  const publicSourceFiles = [
    ...sourceFiles(new URL("../src/components", import.meta.url).pathname),
    ...sourceFiles(new URL("../src/hooks", import.meta.url).pathname),
    ...sourceFiles(new URL("../src/lib", import.meta.url).pathname).filter((path) =>
      path.includes("client") || path.endsWith("response-schema.ts")),
  ];

  for (const path of publicSourceFiles) {
    assert.equal(readFileSync(path, "utf8").includes("birth-time-dynamic-choice-internal"), false, path);
  }
});

test("dynamic turn state is explicitly discriminated from the legacy protocol", () => {
  const dynamicTurn = {
    journeyProtocol: "dynamic-choice-v2",
    turnVersion: 0,
    nextAction: { kind: "generate_dynamic_question" },
    progress: {
      phase: "question",
      answeredCount: 0,
      effectiveAnswerCount: 0,
      currentRange: { startTime: "09:00", endTime: "10:00" },
      previousRange: null,
      plateauCount: 0,
    },
    permissions: { canConfirmCandidate: false },
  };

  assert.equal(dynamicJourneyTurnStateSchema.safeParse(dynamicTurn).success, true);
  assert.equal(journeyTurnStateSchema.safeParse(dynamicTurn).success, false);
  assert.equal(dynamicJourneyTurnStateSchema.safeParse({
    ...dynamicTurn,
    journeyProtocol: "legacy-guided-v1",
  }).success, false);
  assert.equal(dynamicJourneyTurnStateSchema.safeParse({
    ...dynamicTurn,
    nextAction: {
      kind: "ask_baseline_evidence",
      question: {
        questionId: "legacy",
        phase: "baseline",
        domain: "career",
        requestedPrecision: ["year"],
        allowUnknown: true,
        purposeCode: "candidate_difference_career",
        plannerVersion: "candidate-difference-v1",
      },
    },
  }).success, false);
});
