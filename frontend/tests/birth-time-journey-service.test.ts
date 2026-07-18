import assert from "node:assert/strict";
import test from "node:test";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import type { BirthTimeJourneyEngine, StoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";
import {
  approximateAssessment,
  hospitalAssessment,
  journeyCaseId,
  memoryStore,
  scanWithSigns,
  unusedJourneyEngine,
} from "./birth-time-journey-test-support.ts";

test("journey service activates a stable hospital record and persists its scan", async () => {
  const memory = memoryStore();
  let receivedUncertainty = 0;
  const engine: BirthTimeJourneyEngine = {
    ...unusedJourneyEngine,
    async scan(input) {
      receivedUncertainty = input.uncertaintyMinutes;
      return scanWithSigns(["Cancer", "Cancer", "Cancer"]);
    },
  };
  const service = createBirthTimeJourneyService({ store: memory.store, engine });

  const result = await service.assess("user-1", hospitalAssessment);

  assert.equal(receivedUncertainty, 2);
  assert.equal(result.snapshot.route, "direct_chart");
  assert.equal(result.snapshot.activeTime, "08:16");
  assert.equal(result.caseId, journeyCaseId);
  assert.deepEqual(memory.savedAssessment()?.candidateScan, result.questionnaire);
});

test("journey service fails a scanner error closed without activating the time", async () => {
  const memory = memoryStore();
  const engine: BirthTimeJourneyEngine = {
    ...unusedJourneyEngine,
    async scan() {
      throw new TypeError("scanner offline");
    },
  };
  const service = createBirthTimeJourneyService({ store: memory.store, engine });

  const result = await service.assess("user-1", hospitalAssessment);

  assert.equal(result.snapshot.route, "rectification");
  assert.equal(result.snapshot.canApply, false);
  assert.equal(result.questionnaire, null);
  assert.equal(memory.savedAssessment()?.snapshot.activeTime, null);
});

test("journey service projects a fresh active rectification into one baseline ask", async () => {
  const service = createBirthTimeJourneyService({
    store: memoryStore().store,
    engine: {
      ...unusedJourneyEngine,
      async scan() { return scanWithSigns(["Cancer", "Leo", "Virgo"]); },
    },
  });

  const result = await service.assess("user-1", approximateAssessment);

  assert.equal(result.nextAction.kind, "ask_baseline_evidence");
  assert.equal(result.progress.phase, "baseline");
});

test("journey service accumulates legacy answers while preserving the application gate", async () => {
  const questionnaire = scanWithSigns(["Cancer", "Leo", "Leo"]).questionnaire;
  const assessmentService = createBirthTimeJourneyService({
    store: memoryStore().store,
    engine: {
      ...unusedJourneyEngine,
      async scan() { return { questionnaire }; },
    },
  });
  const assessed = await assessmentService.assess("user-1", approximateAssessment);
  const storedCase: StoredRectificationCase = {
    id: journeyCaseId,
    userId: "user-1",
    snapshot: assessed.snapshot,
    questionnaire,
    answers: { education_environment_shift: "A" },
  };
  const memory = memoryStore(storedCase);
  let scoredAnswers: Readonly<Record<string, "A" | "B" | "C" | "D">> = {};
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: {
      ...unusedJourneyEngine,
      async score(input) {
        scoredAnswers = input.answers;
        return {
          answeredCount: 3,
          candidateClusterRankings: [{ cluster: "middle_candidate_cluster", score: 5 }],
          nextRound: 2,
          nextRoundQuestions: [],
          raw: { next_round: 2 },
        };
      },
    },
  });

  const result = await service.answerQuestion(
    "user-1",
    journeyCaseId,
    "career_responsibility_pressure",
    "B",
  );

  assert.deepEqual(scoredAnswers, {
    education_environment_shift: "A",
    career_responsibility_pressure: "B",
  });
  assert.equal(result.snapshot.state, "candidate");
  assert.equal(result.snapshot.canApply, false);
  assert.deepEqual(memory.savedCase()?.answers, scoredAnswers);
});

test("journey service resumes an owner-scoped unfinished legacy case", async () => {
  const storedCase: StoredRectificationCase = {
    id: journeyCaseId,
    userId: "user-1",
    snapshot: {
      state: "rectifying",
      assistantIntent: "continue_rectification_questions",
      input: "rectification_questions",
      route: "rectification",
      confidence: null,
      canApply: false,
      activeTime: null,
      reportedRange: { label: "14:00—15:00", startTime: "14:00", endTime: "15:00" },
    },
    questionnaire: scanWithSigns(["Cancer", "Leo"]).questionnaire,
    answers: { education_environment_shift: "A" },
  };
  const service = createBirthTimeJourneyService({
    store: memoryStore(storedCase).store,
    engine: unusedJourneyEngine,
  });

  const result = await service.resume("user-1", journeyCaseId);

  assert.equal(result.caseId, journeyCaseId);
  assert.deepEqual(result.answers, { education_environment_shift: "A" });
  assert.equal(result.snapshot.canApply, false);
});

test("journey service heals a completed legacy questionnaire into life-event collection", async () => {
  const storedCase: StoredRectificationCase = {
    id: journeyCaseId,
    userId: "user-1",
    snapshot: {
      state: "candidate",
      assistantIntent: "present_saved_candidate_range",
      input: "rectification_questions",
      route: "rectification",
      confidence: null,
      canApply: false,
      activeTime: null,
      reportedRange: { label: "04:00—07:59", startTime: "04:00", endTime: "07:59" },
    },
    questionnaire: scanWithSigns(["Cancer", "Leo"]).questionnaire,
    answers: { education_environment_shift: "A" },
    scoring: {
      answeredCount: 8,
      candidateClusterRankings: [{ cluster: "middle_candidate_cluster", score: 5 }],
      nextRound: null,
      nextRoundQuestions: [],
      raw: { answered_count: 8, next_round: null, next_round_questions: [] },
    },
  };
  const memory = memoryStore(storedCase);
  const service = createBirthTimeJourneyService({ store: memory.store, engine: unusedJourneyEngine });

  const result = await service.resume("user-1", journeyCaseId);

  assert.equal(result.snapshot.state, "rectifying");
  assert.equal(result.snapshot.input, "life_events");
  assert.equal(memory.savedCase()?.snapshot.input, "life_events");
});

test("journey service resumes a fail-closed case without a questionnaire", async () => {
  const storedCase: StoredRectificationCase = {
    id: journeyCaseId,
    userId: "user-1",
    snapshot: {
      state: "rectifying",
      assistantIntent: "explain_assessment_unavailable",
      input: "rectification_questions",
      route: "rectification",
      confidence: null,
      canApply: false,
      activeTime: null,
      reportedRange: { label: "08:14—08:18", startTime: "08:14", endTime: "08:18" },
    },
    questionnaire: null,
    answers: {},
  };
  const service = createBirthTimeJourneyService({
    store: memoryStore(storedCase).store,
    engine: unusedJourneyEngine,
  });

  const result = await service.resume("user-1", journeyCaseId);

  assert.equal(result.questionnaire, null);
  assert.equal(result.snapshot.canApply, false);
});
