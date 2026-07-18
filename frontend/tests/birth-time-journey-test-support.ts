import { birthTimeAssessmentSchema, candidateResultSchema, lifeEventSchema } from "../src/lib/birth-time-journey.ts";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import type { BirthTimeJourneyStore, LegacyBirthTimeJourneyEngine, PersistedJourneyAssessment, StoredRectificationCase } from "../src/lib/birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import type { EvidenceDomain } from "../src/lib/birth-time-question-planner.ts";
import { createMemoryScoringJobs } from "./birth-time-scoring-memory-store.ts";

class UnexpectedTestCallError extends Error { readonly name = "UnexpectedTestCallError"; }

class MissingTestCaseError extends Error {
  readonly name = "MissingTestCaseError";
}

export const journeyCaseId = "7299894c-10a8-4b45-91d1-339007282c50";
export const draftActionId = "45857b75-4718-4590-aaf5-7113a03ea765";
export const confirmActionId = "5cb071d6-6d99-46be-85dc-a9bf59ef6ac5";
export const secondActionId = "0790866c-ad5e-4a45-b2b4-a5c73f6be6ea";
export const thirdActionId = "0ef52e51-ab5f-453b-81e5-adb44a929224";

export const hospitalAssessment = birthTimeAssessmentSchema.parse({
  date: "1993-04-17",
  source: "hospital_record",
  reportedTime: "08:16",
  uncertaintyBeforeMinutes: 2,
  uncertaintyAfterMinutes: 2,
  location: { lat: 31.2304, lon: 121.4737, tz: 8 },
});

export const approximateAssessment = birthTimeAssessmentSchema.parse({
  date: "1993-04-17",
  source: "approximate",
  reportedTime: "14:30",
  uncertaintyBeforeMinutes: 30,
  uncertaintyAfterMinutes: 30,
  location: { lat: 31.2304, lon: 121.4737, tz: 8 },
});

export function scanWithSigns(signs: readonly string[]) {
  const samples = signs.map((sign) => ({
    ascendantSign: sign,
    d4Sign: null,
    d9Sign: sign,
    d10Sign: sign,
    d24Sign: null,
    d30Sign: null,
  }));
  return {
    questionnaire: {
      questions: [{ id: "education_environment_shift", prompt: "是否有明显学业变化？" }],
      samples,
      raw: { candidate_scan: { samples } },
    },
  };
}

export function memoryStore(initialCase?: StoredRectificationCase) {
  let savedAssessment: PersistedJourneyAssessment | null = null;
  let savedCase = initialCase ?? null;
  let committedTurnWrites = 0;
  let legacyWrites = 0;
  let guidedCandidateWrites = 0;
  const scoringJobs = createMemoryScoringJobs({
    read: () => savedCase,
    write: (value) => { savedCase = value; },
    committed: () => { committedTurnWrites += 1; },
  });
  const store: BirthTimeJourneyStore = {
    async saveAssessment(value) {
      savedAssessment = value;
      return journeyCaseId;
    },
    async loadCase() {
      return savedCase;
    },
    async saveScoring(value) {
      legacyWrites += 1;
      savedCase = value;
    },
    async saveTurn(value, expectedVersion, actionId) {
      if (!savedCase) throw new MissingTestCaseError();
      const processedActionIds = savedCase.processedActionIds ?? [];
      if (processedActionIds.includes(actionId)) return savedCase;
      if (savedCase.turnVersion !== expectedVersion) {
        throw new StaleJourneyTurnError(savedCase.id, expectedVersion, savedCase.turnVersion ?? 0);
      }
      savedCase = {
        ...value,
        turnVersion: expectedVersion + 1,
        processedActionIds: [...processedActionIds, actionId],
      };
      committedTurnWrites += 1;
      return savedCase;
    },
    ...scoringJobs.methods,
    async saveCandidateResult(value) {
      legacyWrites += 1;
      savedCase = value;
    },
    async saveCandidate(value) {
      legacyWrites += 1;
      savedCase = value;
    },
    async confirmCandidate(value) {
      legacyWrites += 1;
      savedCase = value;
    },
    async commitGuidedCandidate(value, command) {
      if (!savedCase) throw new MissingTestCaseError();
      const receipt = command.actionId.toLowerCase();
      const receipts = savedCase.processedActionIds ?? [];
      if (receipts.includes(receipt)) return savedCase;
      if (savedCase.turnVersion !== command.expectedVersion) {
        throw new StaleJourneyTurnError(savedCase.id, command.expectedVersion, savedCase.turnVersion ?? 0);
      }
      savedCase = {
        ...value,
        turnVersion: command.expectedVersion + 1,
        processedActionIds: [...receipts, receipt],
      };
      guidedCandidateWrites += 1;
      return savedCase;
    },
  };
  return {
    store,
    savedAssessment: () => savedAssessment,
    savedCase: () => savedCase,
    committedTurnWrites: () => committedTurnWrites,
    legacyWrites: () => legacyWrites,
    guidedCandidateWrites: () => guidedCandidateWrites,
    scoringJobStatus: scoringJobs.status,
    scoringJobCount: scoringJobs.count,
    setScoringJobAlgorithm: scoringJobs.setAlgorithm,
    createdScoringCase: scoringJobs.createdCase,
    replaceCase: (value: StoredRectificationCase) => { savedCase = value; },
  };
}

export const unusedJourneyEngine: LegacyBirthTimeJourneyEngine = {
  async scan() { throw new UnexpectedTestCallError(); },
  async score() { throw new UnexpectedTestCallError(); },
  async scoreEvents() { throw new UnexpectedTestCallError(); },
};

export function evidenceQuestion(
  phase: "baseline" | "adaptive",
  domain: EvidenceDomain,
  round: number,
) {
  return {
    questionId: `${phase}_${domain}_${round}`,
    phase,
    domain,
    requestedPrecision: ["year", "month"] as const,
    allowUnknown: true as const,
    purposeCode: `candidate_difference_${domain}`,
    plannerVersion: "candidate-difference-v1",
  };
}

export const existingEducationEvent = lifeEventSchema.parse({
  id: "1d8ee348-61a3-433d-8907-ff6d281b9992",
  domain: "education",
  precision: "year",
  date: "2011",
});

export const existingCareerEvent = lifeEventSchema.parse({
  id: "12dc56f0-1f17-4a2f-86bf-1056ab78def9",
  domain: "career",
  precision: "month",
  date: "2019-07",
});

export const lowCandidate = candidateResultSchema.parse({
  resultId: "a485f35d-bfb3-4c9b-9151-d812510b9e80",
  confidence: "low",
  canApply: false,
  winningSegment: null,
  eventCount: 3,
  domainCount: 3,
  topScore: 8,
  secondScore: 7,
  marginPercent: 12.5,
  reasons: ["Candidate scores remain close."],
  evidence: [],
  algorithmVersion: "birth-time-event-scoring-v1",
});

type GuidedCaseInput = {
  readonly version?: number;
  readonly phase?: "baseline" | "adaptive";
  readonly domain?: EvidenceDomain;
  readonly adaptiveRound?: number;
  readonly askedDomains?: readonly EvidenceDomain[];
  readonly lifeEvents?: readonly ReturnType<typeof lifeEventSchema.parse>[];
  readonly candidateResult?: ReturnType<typeof candidateResultSchema.parse> | null;
};

export function guidedCase(input: GuidedCaseInput = {}): StoredRectificationCase {
  const version = input.version ?? 0;
  const phase = input.phase ?? "baseline";
  const domain = input.domain ?? "career";
  const adaptiveRound = input.adaptiveRound ?? 0;
  const question = evidenceQuestion(phase, domain, phase === "adaptive" ? adaptiveRound : 1);
  const lifeEvents = input.lifeEvents ?? [];
  const candidateResult = input.candidateResult ?? null;
  return {
    id: journeyCaseId,
    userId: "user-1",
    snapshot: {
      state: "rectifying",
      assistantIntent: candidateResult?.confidence === "low"
        ? "explain_event_evidence_insufficient"
        : "continue_rectification_questions",
      input: "rectification_questions",
      route: "rectification",
      confidence: candidateResult?.confidence ?? null,
      canApply: false,
      activeTime: null,
      reportedRange: { label: "14:00—15:00", startTime: "14:00", endTime: "15:00" },
    },
    questionnaire: scanWithSigns(["Cancer", "Leo", "Virgo"]).questionnaire,
    answers: {},
    eventContext: { birthDate: "1993-04-17", lat: 31.2304, lon: 121.4737, tz: 8 },
    lifeEvents,
    candidateResult,
    turnVersion: version,
    turnState: {
      turnVersion: version,
      nextAction: phase === "baseline"
        ? { kind: "ask_baseline_evidence", question }
        : { kind: "ask_adaptive_evidence", question },
      progress: {
        phase,
        baselineDomainCount: new Set(lifeEvents.map((event) => event.domain)).size,
        confirmedEvidenceCount: lifeEvents.length,
        adaptiveRound,
        maxAdaptiveRounds: 3,
      },
      permissions: { canConfirmCandidate: false },
      evidenceDraft: null,
    },
    evidenceDraft: null,
    processedActionIds: [],
    persistedProgress: { adaptiveRound, askedDomains: input.askedDomains ?? [] },
  };
}

export function progressionService(storedCase: StoredRectificationCase) {
  let scoreEventsCalls = 0;
  const memory = memoryStore(storedCase);
  const service = createBirthTimeJourneyService({
    store: memory.store,
    engine: {
      ...unusedJourneyEngine,
      async scoreEvents() {
        scoreEventsCalls += 1;
        return lowCandidate;
      },
    },
  });
  return { memory, service, scoreEventsCalls: () => scoreEventsCalls };
}
