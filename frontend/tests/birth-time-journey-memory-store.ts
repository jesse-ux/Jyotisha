import { isDeepStrictEqual } from "node:util";
import type {
  BirthTimeJourneyStore,
  DynamicScoringJobCommand,
  DynamicScoringJobFailureCommand,
  DynamicStoredRectificationCase,
  PersistedJourneyAssessment,
  StoredRectificationCase,
} from "../src/lib/birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";
import {
  isTerminalLegacyCase,
  prepareLegacyDynamicUpgrade,
} from "../src/lib/birth-time-journey-dynamic-state.ts";
import { createMemoryScoringJobs } from "./birth-time-scoring-memory-store.ts";

class MissingTestCaseError extends Error {
  readonly name = "MissingTestCaseError";
}

export const journeyCaseId = "7299894c-10a8-4b45-91d1-339007282c50";

type DynamicScoringReceipt = {
  readonly kind: "complete" | "fail";
  readonly command: DynamicScoringJobCommand | DynamicScoringJobFailureCommand;
  readonly result: DynamicStoredRectificationCase["candidateResult"];
};

function sameScoringOperation(
  receipt: DynamicScoringReceipt,
  next: DynamicScoringReceipt,
): boolean {
  const prior = receipt.command;
  const command = next.command;
  return receipt.kind === next.kind
    && prior.expectedVersion === command.expectedVersion
    && prior.jobId.toLowerCase() === command.jobId.toLowerCase()
    && prior.evidenceFingerprint === command.evidenceFingerprint
    && prior.algorithmVersion === command.algorithmVersion
    && (receipt.kind !== "fail" || (
      "failureCode" in prior && "failureCode" in command
      && prior.failureCode === command.failureCode
    ))
    && (receipt.kind !== "complete" || isDeepStrictEqual(receipt.result, next.result));
}

export function memoryStore(
  initialCase?: StoredRectificationCase,
  asOfDate = "2026-07-18",
) {
  let savedAssessment: PersistedJourneyAssessment | null = null;
  let savedCase = initialCase ?? null;
  let savedDynamicCase: DynamicStoredRectificationCase | null =
    initialCase?.journeyProtocol === "dynamic-choice-v2" ? initialCase : null;
  let committedTurnWrites = 0;
  let legacyWrites = 0;
  let guidedCandidateWrites = 0;
  let dynamicScoringReceipt: DynamicScoringReceipt | null = null;
  const scoringJobs = createMemoryScoringJobs({
    read: () => savedCase,
    write: (value) => {
      savedCase = value;
    },
    committed: () => {
      committedTurnWrites += 1;
    },
  });
  function persistDynamicScoring(
    value: DynamicStoredRectificationCase,
    receipt: DynamicScoringReceipt,
  ): DynamicStoredRectificationCase {
    if (!savedDynamicCase) throw new MissingTestCaseError();
    const expectedVersion = receipt.command.expectedVersion;
    if (savedDynamicCase.turnVersion === expectedVersion + 1) {
      if (dynamicScoringReceipt && sameScoringOperation(dynamicScoringReceipt, receipt)) {
        return savedDynamicCase;
      }
      throw new StaleJourneyTurnError(value.id, expectedVersion, savedDynamicCase.turnVersion);
    }
    if (savedDynamicCase.turnVersion !== expectedVersion) {
      throw new StaleJourneyTurnError(value.id, expectedVersion, savedDynamicCase.turnVersion);
    }
    const saved = {
      ...value,
      turnVersion: expectedVersion + 1,
      dynamicTurnState: { ...value.dynamicTurnState, turnVersion: expectedVersion + 1 },
    };
    savedCase = saved;
    savedDynamicCase = saved;
    dynamicScoringReceipt = receipt;
    return saved;
  }
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
      if (savedCase.journeyProtocol !== "legacy-guided-v1") {
        throw new StaleJourneyTurnError(savedCase.id, expectedVersion, savedCase.turnVersion);
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
    async saveDynamicTurn(value, expectedVersion, actionId) {
      if (!savedCase) throw new MissingTestCaseError();
      const receipt = actionId.toLowerCase();
      const receipts = savedCase.processedActionIds ?? [];
      if (receipts.includes(receipt)) {
        if (!savedDynamicCase) throw new MissingTestCaseError();
        return savedDynamicCase;
      }
      if (savedCase.turnVersion !== expectedVersion) {
        throw new StaleJourneyTurnError(savedCase.id, expectedVersion, savedCase.turnVersion ?? 0);
      }
      const savedDynamic = {
        ...value,
        turnVersion: expectedVersion + 1,
        dynamicTurnState: { ...value.dynamicTurnState, turnVersion: expectedVersion + 1 },
        processedActionIds: [...receipts, receipt],
      };
      savedCase = savedDynamic;
      savedDynamicCase = savedDynamic;
      committedTurnWrites += 1;
      return savedDynamic;
    },
    async completeDynamicScoringJob(value, command) {
      return persistDynamicScoring(value, { kind: "complete", command, result: value.candidateResult });
    },
    async failDynamicScoringJob(value, command) {
      return persistDynamicScoring(value, { kind: "fail", command, result: null });
    },
    async upgradeLegacyActiveCase(value) {
      if (isTerminalLegacyCase(value)) {
        return value;
      }
      const upgraded = prepareLegacyDynamicUpgrade(value, asOfDate);
      savedCase = upgraded;
      savedDynamicCase = upgraded;
      return upgraded;
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
      if (savedCase.journeyProtocol !== "legacy-guided-v1") {
        throw new StaleJourneyTurnError(
          savedCase.id,
          command.expectedVersion,
          savedCase.turnVersion,
        );
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
      savedDynamicCase = value.journeyProtocol === "dynamic-choice-v2" ? value : null;
      dynamicScoringReceipt = null;
    },
  };
}
