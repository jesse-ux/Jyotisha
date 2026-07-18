import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";
import {
  birthTimeGuideRequestSchema,
  type BirthTimeGuideGenerator,
} from "../src/lib/birth-time-guide-agent.ts";
import {
  BirthTimeGuideActionError,
  createBirthTimeGuideService,
} from "../src/lib/birth-time-guide-service.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import type { LegacyStoredRectificationCase, StoredRectificationCase, VersionedJourneyResponse } from "../src/lib/birth-time-journey-service.ts";
import { storedJourneyResponse } from "../src/lib/birth-time-journey-response.ts";
import { createInitialJourneyTurn } from "../src/lib/birth-time-journey-turn.ts";
import type { QuestionSpec } from "../src/lib/birth-time-question-planner.ts";

const caseId = "7299894c-10a8-4b45-91d1-339007282c50";
const actionId = "c70ea014-f8b4-41f2-9305-e4ae60c0d4d1";

type ProposedDraftCall = {
  readonly userId: string;
  readonly caseId: string;
  readonly actionId: string;
  readonly turnVersion: number;
  readonly domain: string;
  readonly precision: string | null;
  readonly date: string | null;
};

function careerQuestion(): QuestionSpec {
  return {
    questionId: "baseline_career_1",
    phase: "baseline",
    domain: "career",
    requestedPrecision: ["year", "month"],
    allowUnknown: true,
    purposeCode: "candidate_difference_career",
    plannerVersion: "candidate-difference-v1",
  };
}

function storedCase(): LegacyStoredRectificationCase {
  return {
    id: caseId,
    userId: "owner-1",
    journeyProtocol: "legacy-guided-v1",
    snapshot: {
      state: "rectifying",
      assistantIntent: "continue_rectification_questions",
      input: "rectification_questions",
      route: "rectification",
      confidence: null,
      canApply: false,
      activeTime: null,
      reportedRange: { label: "04:00—07:59", startTime: "04:00", endTime: "07:59" },
    },
    questionnaire: { questions: [], samples: [], raw: {} },
    answers: {},
    lifeEvents: [],
    turnVersion: 4,
    turnState: createInitialJourneyTurn(careerQuestion(), 4),
    processedActionIds: [],
    persistedProgress: { adaptiveRound: 0, askedDomains: [] },
    evidenceDraft: null,
  };
}

function generator(text: string, onGenerate?: () => void): BirthTimeGuideGenerator {
  return {
    async generate() {
      onGenerate?.();
      return { text };
    },
  };
}

function service(input?: {
  readonly stored?: StoredRectificationCase | null;
  readonly generator?: BirthTimeGuideGenerator | null;
  readonly onLoad?: (userId: string, loadedCaseId: string) => void;
  readonly onPropose?: (value: ProposedDraftCall) => void;
}) {
  const stored = input?.stored === undefined ? storedCase() : input.stored;
  return createBirthTimeGuideService({
    generator: input?.generator ?? null,
    timeoutMs: 20,
    async loadCase(userId, loadedCaseId) {
      input?.onLoad?.(userId, loadedCaseId);
      return stored;
    },
    async proposeEvidenceDraft(userId, loadedCaseId, receivedActionId, turnVersion, proposal) {
      input?.onPropose?.({
        userId,
        caseId: loadedCaseId,
        actionId: receivedActionId,
        turnVersion,
        ...proposal,
      });
      return storedJourneyResponse(storedCase()) satisfies VersionedJourneyResponse;
    },
  });
}

test("render question uses an owner-scoped load and one neutral model question", async () => {
  let loaded: readonly string[] = [];
  const result = await service({
    generator: generator(JSON.stringify({ variant: "gentle" })),
    onLoad: (userId, loadedCaseId) => { loaded = [userId, loadedCaseId]; },
  }).renderQuestion("owner-1", caseId);

  assert.deepEqual(loaded, ["owner-1", caseId]);
  assert.equal(result.type, "question");
  assert.equal(result.questionId, "baseline_career_1");
  assert.equal(result.source, "agent");
  assert.doesNotMatch(result.question, /候选|支持|更符合|更接近/);
});

test("render question falls back when model is absent, throws, times out, or returns invalid output", async () => {
  const failures: readonly (BirthTimeGuideGenerator | null)[] = [
    null,
    { async generate() { throw new Error("offline"); } },
    { async generate() { return Promise.reject("offline"); } },
    { async generate() { return new Promise(() => undefined); } },
    generator(JSON.stringify({ variant: "relationship" })),
    generator(JSON.stringify({ variant: "direct", domain: "relationship" })),
    generator(JSON.stringify({ question: "Which relationship changed?" })),
    generator(JSON.stringify({ question: "具体是哪一天？" })),
    generator(JSON.stringify({ question: "04：00 这个候选时间更符合吗？" })),
    generator(JSON.stringify({ variant: "direct", question: "越权覆盖" })),
  ];
  for (const failingGenerator of failures) {
    const result = await service({ generator: failingGenerator }).renderQuestion("owner-1", caseId);
    assert.equal(result.source, "fallback");
    assert.equal((result.question.match(/[？?]/g) ?? []).length, 1);
    assert.match(result.question, /工作|职业方向|身份变化/);
    assert.doesNotMatch(result.question, /关系进入|关系结束|哪一天|具体日期|04[:：]00|Which/);
  }
});

test("non-question turns are rejected", async () => {
  const stored = storedCase();
  const turn = createInitialJourneyTurn(careerQuestion(), 4);
  const scoring = {
    ...stored,
    turnState: {
      ...turn,
      nextAction: { kind: "score_pending", jobId: "75a5fbb3-bf1d-44b2-8c74-c92cf7578f82" },
      progress: { ...turn.progress, phase: "scoring" },
    },
  } satisfies StoredRectificationCase;

  await assert.rejects(
    service({ stored: scoring }).renderQuestion("owner-1", caseId),
    BirthTimeGuideActionError,
  );
});

test("draft keeps action/version and calls only the review-only proposal action", async () => {
  let proposed: ProposedDraftCall | null = null;
  const result = await service({
    generator: generator(JSON.stringify({ domain: "career", precision: "month", date: "2023-04" })),
    onPropose: (value) => { proposed = value; },
  }).draftEvidence("owner-1", {
    caseId,
    actionId,
    turnVersion: 4,
    message: "我在 2023 年 4 月换了工作",
  });

  assert.deepEqual(proposed, {
    userId: "owner-1",
    caseId,
    actionId,
    turnVersion: 4,
    domain: "career",
    precision: "month",
    date: "2023-04",
  });
  assert.equal(result.type, "evidence_draft");
  assert.equal(result.actionId, actionId);
  assert.equal(result.requestedTurnVersion, 4);
  assert.equal("nextAction" in result, false);
  assert.equal(result.turn.caseId, caseId);
});

test("stale draft versions fail before model generation or mutation", async () => {
  let generations = 0;
  let proposals = 0;
  await assert.rejects(
    service({
      generator: generator("{}", () => { generations += 1; }),
      onPropose: () => { proposals += 1; },
    }).draftEvidence("owner-1", {
      caseId,
      actionId,
      turnVersion: 3,
      message: "2023 年换工作",
    }),
    StaleJourneyTurnError,
  );
  assert.equal(generations, 0);
  assert.equal(proposals, 0);
});

test("a processed draft action replays the persisted turn before stale checking", async () => {
  let generations = 0;
  let proposals = 0;
  const stored = { ...storedCase(), processedActionIds: [actionId] } satisfies StoredRectificationCase;
  const result = await service({
    stored,
    generator: generator("{}", () => { generations += 1; }),
    onPropose: () => { proposals += 1; },
  }).draftEvidence("owner-1", {
    caseId,
    actionId,
    turnVersion: 1,
    message: "2023 年换工作",
  });

  assert.equal(generations, 0);
  assert.equal(proposals, 0);
  assert.equal(result.turn.turnVersion, 4);
  assert.equal(result.requestedTurnVersion, 1);
});

test("guide requests are strict and bound the natural-language message", () => {
  const valid = { type: "draft_evidence", caseId, actionId, turnVersion: 4, message: "  2023 年换工作  " };
  const parsed = birthTimeGuideRequestSchema.parse(valid);
  assert.equal(parsed.type === "draft_evidence" ? parsed.message : null, "2023 年换工作");
  assert.equal(birthTimeGuideRequestSchema.safeParse({ ...valid, score: 10 }).success, false);
  assert.equal(birthTimeGuideRequestSchema.safeParse({ ...valid, message: "" }).success, false);
  assert.equal(birthTimeGuideRequestSchema.safeParse({ ...valid, message: "字".repeat(501) }).success, false);
  assert.equal(birthTimeGuideRequestSchema.safeParse({ type: "render_question", caseId, extra: true }).success, false);
});

test("route authenticates before body parsing and has no privileged workflow imports", () => {
  const source = readFileSync(new URL("../src/app/api/birth-time-guide/route.ts", import.meta.url), "utf8");
  assert.ok(source.indexOf("auth.getUser") < source.indexOf("requestPayload(request)"));
  for (const forbidden of [
    "begin_consultation_credit",
    "getJyotishAgent",
    "consultationTool",
    "scoreEvents",
    "saveBirthTimeCandidate",
    "confirmBirthTimeCandidate",
    "active_birth_time",
  ]) {
    assert.doesNotMatch(source, new RegExp(forbidden));
  }
});
