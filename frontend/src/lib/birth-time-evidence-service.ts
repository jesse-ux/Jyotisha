import {
  withCandidateResult,
  withConfirmedCandidate,
} from "./birth-time-evidence.ts";
import type { CandidateResult, LifeEvent } from "./birth-time-evidence.ts";
import type {
  BirthTimeJourneyPorts,
  JourneyResponse,
  StoredRectificationCase,
} from "./birth-time-journey-service.ts";

export class BirthTimeEvidenceContextError extends Error {
  readonly name = "BirthTimeEvidenceContextError";
}

export class StaleCandidateConfirmationError extends Error {
  readonly name = "StaleCandidateConfirmationError";
  readonly caseId: string;
  constructor(caseId: string) {
    super(`Candidate result for ${caseId} is stale`);
    this.caseId = caseId;
  }
}

export class EvidenceRectificationCaseNotFoundError extends Error {
  readonly name = "EvidenceRectificationCaseNotFoundError";
  readonly caseId: string;
  constructor(caseId: string) {
    super(`Rectification case ${caseId} was not found`);
    this.caseId = caseId;
  }
}

export class GuidedJourneyLegacyMutationError extends Error {
  readonly name = "GuidedJourneyLegacyMutationError";
  readonly caseId: string;
  constructor(caseId: string) {
    super(`Guided journey ${caseId} cannot use a legacy mutation`);
    this.caseId = caseId;
  }
}

export function assertLegacyJourneyMutation(
  stored: StoredRectificationCase,
): void {
  if (stored.turnState) throw new GuidedJourneyLegacyMutationError(stored.id);
}

function response(
  stored: StoredRectificationCase,
  lifeEvents: readonly LifeEvent[],
  candidateResult: CandidateResult | null,
): JourneyResponse {
  return {
    caseId: stored.id,
    snapshot: stored.snapshot,
    questionnaire: stored.questionnaire,
    scoring: stored.scoring ?? null,
    answers: stored.answers,
    lifeEvents,
    candidateResult,
  };
}

async function ownedCase(
  ports: BirthTimeJourneyPorts,
  userId: string,
  caseId: string,
) {
  const stored = await ports.store.loadCase(userId, caseId);
  if (!stored) throw new EvidenceRectificationCaseNotFoundError(caseId);
  assertLegacyJourneyMutation(stored);
  return stored;
}

export function createBirthTimeEvidenceActions(ports: BirthTimeJourneyPorts) {
  return {
    async submitLifeEvents(
      userId: string,
      caseId: string,
      events: readonly LifeEvent[],
    ): Promise<JourneyResponse> {
      const stored = await ownedCase(ports, userId, caseId);
      const context = stored.eventContext;
      const { startTime, endTime } = stored.snapshot.reportedRange;
      const acceptsEvidence = stored.snapshot.input === "life_events"
        || stored.snapshot.input === "candidate_actions"
        || stored.snapshot.input === "candidate_confirmation";
      if (!context || !startTime || !endTime || !acceptsEvidence) {
        throw new BirthTimeEvidenceContextError();
      }
      const candidateResult = await ports.engine.scoreEvents({
        ...context,
        startTime,
        endTime,
        events,
      });
      const snapshot = withCandidateResult(stored.snapshot, candidateResult);
      const updated = { ...stored, snapshot, lifeEvents: events, candidateResult };
      await ports.store.saveCandidateResult(updated);
      return response(updated, events, candidateResult);
    },

    async saveCandidate(
      userId: string,
      caseId: string,
      resultId: string,
    ): Promise<JourneyResponse> {
      const stored = await ownedCase(ports, userId, caseId);
      const candidateResult = stored.candidateResult ?? null;
      if (!candidateResult || candidateResult.resultId !== resultId) {
        throw new StaleCandidateConfirmationError(caseId);
      }
      await ports.store.saveCandidate(stored);
      return response(stored, stored.lifeEvents ?? [], candidateResult);
    },

    async confirmCandidate(
      userId: string,
      caseId: string,
      resultId: string,
      time: string,
    ): Promise<JourneyResponse> {
      const stored = await ownedCase(ports, userId, caseId);
      const candidateResult = stored.candidateResult ?? null;
      if (!candidateResult || candidateResult.resultId !== resultId) {
        throw new StaleCandidateConfirmationError(caseId);
      }
      const snapshot = withConfirmedCandidate(stored.snapshot, candidateResult, time);
      const updated = { ...stored, snapshot };
      await ports.store.confirmCandidate(updated);
      return response(updated, stored.lifeEvents ?? [], candidateResult);
    },
  };
}
