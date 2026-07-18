import type {
  BirthTimeJourneyStore,
  PersistedJourneyAssessment,
  StoredRectificationCase,
} from "../src/lib/birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import { createMemoryScoringJobs } from "./birth-time-scoring-memory-store.ts";

class MissingTestCaseError extends Error {
  readonly name = "MissingTestCaseError";
}

export const journeyCaseId = "7299894c-10a8-4b45-91d1-339007282c50";

export function memoryStore(initialCase?: StoredRectificationCase) {
  let savedAssessment: PersistedJourneyAssessment | null = null;
  let savedCase = initialCase ?? null;
  let committedTurnWrites = 0;
  let legacyWrites = 0;
  let guidedCandidateWrites = 0;
  const scoringJobs = createMemoryScoringJobs({
    read: () => savedCase,
    write: (value) => {
      savedCase = value;
    },
    committed: () => {
      committedTurnWrites += 1;
    },
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
      if (!savedCase) {
        throw new MissingTestCaseError();
      }
      const processedActionIds = savedCase.processedActionIds ?? [];
      if (processedActionIds.includes(actionId)) {
        return savedCase;
      }
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
      if (!savedCase) {
        throw new MissingTestCaseError();
      }
      const receipt = command.actionId.toLowerCase();
      const receipts = savedCase.processedActionIds ?? [];
      if (receipts.includes(receipt)) {
        return savedCase;
      }
      if (savedCase.turnVersion !== command.expectedVersion) {
        throw new StaleJourneyTurnError(
          savedCase.id,
          command.expectedVersion,
          savedCase.turnVersion ?? 0,
        );
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
    replaceCase: (value: StoredRectificationCase) => {
      savedCase = value;
    },
  };
}
