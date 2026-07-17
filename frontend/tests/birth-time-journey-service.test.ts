import assert from "node:assert/strict";
import test from "node:test";
import { birthTimeAssessmentSchema } from "../src/lib/birth-time-journey.ts";
import {
  createBirthTimeJourneyService,
  type BirthTimeJourneyEngine,
  type BirthTimeJourneyStore,
  type PersistedJourneyAssessment,
  type StoredRectificationCase,
} from "../src/lib/birth-time-journey-service.ts";

const hospitalAssessment = birthTimeAssessmentSchema.parse({
  date: "1993-04-17",
  source: "hospital_record",
  reportedTime: "08:16",
  uncertaintyBeforeMinutes: 2,
  uncertaintyAfterMinutes: 2,
  location: { lat: 31.2304, lon: 121.4737, tz: 8 },
});

function scanWithSigns(signs: readonly string[]) {
  const samples = signs.map((sign) => ({
    ascendantSign: sign,
    d9Sign: sign,
    d10Sign: sign,
  }));
  return {
    questionnaire: {
      questions: [{ id: "education_environment_shift", prompt: "是否有明显学业变化？" }],
      samples,
      raw: { candidate_scan: { samples } },
    },
  };
}

function memoryStore(initialCase?: StoredRectificationCase) {
  let savedAssessment: PersistedJourneyAssessment | null = null;
  let savedCase = initialCase ?? null;
  const store: BirthTimeJourneyStore = {
    async saveAssessment(value) {
      savedAssessment = value;
      return "case-1";
    },
    async loadCase() {
      return savedCase;
    },
    async saveScoring(value) {
      savedCase = value;
    },
  };
  return {
    store,
    savedAssessment: () => savedAssessment,
    savedCase: () => savedCase,
  };
}

test("journey service activates a stable hospital record and persists its scan", async () => {
  const memory = memoryStore();
  let receivedUncertainty = 0;
  const engine: BirthTimeJourneyEngine = {
    async scan(input) {
      receivedUncertainty = input.uncertaintyMinutes;
      return scanWithSigns(["Cancer", "Cancer", "Cancer"]);
    },
    async score() {
      throw new Error("not used");
    },
  };
  const service = createBirthTimeJourneyService({ store: memory.store, engine });

  const result = await service.assess("user-1", hospitalAssessment);

  assert.equal(receivedUncertainty, 2);
  assert.equal(result.snapshot.route, "direct_chart");
  assert.equal(result.snapshot.activeTime, "08:16");
  assert.equal(result.caseId, "case-1");
  assert.deepEqual(memory.savedAssessment()?.candidateScan, result.questionnaire);
});

test("journey service fails a scanner error closed without activating the time", async () => {
  const memory = memoryStore();
  const engine: BirthTimeJourneyEngine = {
    async scan() {
      throw new TypeError("scanner offline");
    },
    async score() {
      throw new Error("not used");
    },
  };
  const service = createBirthTimeJourneyService({ store: memory.store, engine });

  const result = await service.assess("user-1", hospitalAssessment);

  assert.equal(result.snapshot.route, "rectification");
  assert.equal(result.snapshot.canApply, false);
  assert.equal(result.questionnaire, null);
  assert.equal(memory.savedAssessment()?.snapshot.activeTime, null);
});

test("journey service accumulates answers while preserving the application gate", async () => {
  const approximate = birthTimeAssessmentSchema.parse({
    date: "1993-04-17",
    source: "approximate",
    reportedTime: "14:30",
    uncertaintyBeforeMinutes: 30,
    uncertaintyAfterMinutes: 30,
    location: { lat: 31.2304, lon: 121.4737, tz: 8 },
  });
  const questionnaire = scanWithSigns(["Cancer", "Leo", "Leo"]).questionnaire;
  const initialSnapshot = createBirthTimeJourneyService({
    store: memoryStore().store,
    engine: {
      async scan() { return { questionnaire }; },
      async score() { throw new Error("not used"); },
    },
  });
  const assessed = await initialSnapshot.assess("user-1", approximate);
  const storedCase: StoredRectificationCase = {
    id: "case-1",
    userId: "user-1",
    snapshot: assessed.snapshot,
    questionnaire,
    answers: { education_environment_shift: "A" },
  };
  const memory = memoryStore(storedCase);
  let scoredAnswers: Readonly<Record<string, "A" | "B" | "C" | "D">> = {};
  const engine: BirthTimeJourneyEngine = {
    async scan() {
      return { questionnaire };
    },
    async score(input) {
      scoredAnswers = input.answers;
      return {
        answeredCount: 3,
        candidateClusterRankings: [{ cluster: "middle_candidate_cluster", score: 5 }],
        raw: { next_round: 2 },
      };
    },
  };
  const service = createBirthTimeJourneyService({ store: memory.store, engine });

  const result = await service.answerQuestion("user-1", "case-1", "career_responsibility_pressure", "B");

  assert.deepEqual(scoredAnswers, {
    education_environment_shift: "A",
    career_responsibility_pressure: "B",
  });
  assert.equal(result.snapshot.state, "candidate");
  assert.equal(result.snapshot.canApply, false);
  assert.deepEqual(memory.savedCase()?.answers, scoredAnswers);
});
