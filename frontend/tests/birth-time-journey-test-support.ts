import { birthTimeAssessmentSchema, candidateResultSchema, lifeEventSchema } from "../src/lib/birth-time-journey.ts";
import { createBirthTimeJourneyService } from "../src/lib/birth-time-journey-service.ts";
import type {
  LegacyBirthTimeJourneyEngine,
  LegacyStoredRectificationCase,
} from "../src/lib/birth-time-journey-service.ts";
import type { EvidenceDomain } from "../src/lib/birth-time-question-planner.ts";
import {
  journeyCaseId,
  memoryStore,
} from "./birth-time-journey-memory-store.ts";

class UnexpectedTestCallError extends Error {
  readonly name = "UnexpectedTestCallError";
}

export { journeyCaseId, memoryStore };
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

export function guidedCase(input: GuidedCaseInput = {}): LegacyStoredRectificationCase {
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

export function progressionService(storedCase: LegacyStoredRectificationCase) {
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
