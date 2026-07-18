import { withConfirmedCandidate } from "./birth-time-evidence.ts";
import { currentJourneyTurn, storedJourneyResponse } from "./birth-time-journey-response.ts";
import type {
  BirthTimeJourneyStore,
  StoredRectificationCase,
} from "./birth-time-journey-service.ts";
import type { JourneyTurnState } from "./birth-time-journey-turn.ts";
import { StaleJourneyTurnError } from "./birth-time-journey-turn-persistence.ts";

export type GuidedCandidateCommit = {
  readonly kind: "save" | "confirm";
  readonly expectedVersion: number;
  readonly actionId: string;
};

export class GuidedCandidateActionError extends Error {
  readonly name = "GuidedCandidateActionError";
  readonly reason: "case_not_found" | "invalid_turn" | "invalid_candidate";
  constructor(reason: "case_not_found" | "invalid_turn" | "invalid_candidate") {
    super(`Guided candidate action ${reason}`);
    this.reason = reason;
  }
}

type CandidateMutation = {
  readonly userId: string;
  readonly caseId: string;
  readonly actionId: string;
  readonly expectedVersion: number;
  readonly resultId: string;
};
type CandidateConfirmation = CandidateMutation & { readonly time: string };
type GuidedCandidatePorts = { readonly store: BirthTimeJourneyStore };

async function ownedCase(ports: GuidedCandidatePorts, userId: string, caseId: string) {
  const stored = await ports.store.loadCase(userId, caseId);
  if (!stored) throw new GuidedCandidateActionError("case_not_found");
  return stored;
}

function replayed(stored: StoredRectificationCase, actionId: string): boolean {
  return stored.processedActionIds?.includes(actionId.toLowerCase()) === true;
}

function assertCurrentVersion(stored: StoredRectificationCase, expectedVersion: number): void {
  const currentVersion = stored.turnVersion ?? 0;
  if (currentVersion !== expectedVersion) {
    throw new StaleJourneyTurnError(stored.id, expectedVersion, currentVersion);
  }
}

function savedTurn(stored: StoredRectificationCase, nextVersion: number): JourneyTurnState {
  const current = currentJourneyTurn(stored);
  const result = stored.candidateResult;
  if (
    current.nextAction.kind !== "present_medium_result"
    || result?.confidence !== "medium"
    || current.nextAction.resultId !== result.resultId
  ) throw new GuidedCandidateActionError("invalid_turn");
  return {
    ...current,
    turnVersion: nextVersion,
    nextAction: { kind: "candidate_saved", resultId: result.resultId },
  };
}

function confirmedTurn(
  input: {
    readonly stored: StoredRectificationCase;
    readonly resultId: string;
    readonly time: string;
    readonly nextVersion: number;
  },
): StoredRectificationCase {
  const current = currentJourneyTurn(input.stored);
  const result = input.stored.candidateResult;
  if (
    current.nextAction.kind !== "request_candidate_confirmation"
    || !current.permissions.canConfirmCandidate
    || result?.confidence !== "high"
    || result.resultId !== input.resultId
    || current.nextAction.resultId !== input.resultId
  ) throw new GuidedCandidateActionError("invalid_turn");
  const snapshot = withConfirmedCandidate(input.stored.snapshot, result, input.time);
  const turnState: JourneyTurnState = {
    ...current,
    turnVersion: input.nextVersion,
    nextAction: { kind: "ready", activeTime: input.time },
    progress: { ...current.progress, phase: "ready" },
    permissions: { canConfirmCandidate: false },
    evidenceDraft: null,
  };
  return { ...input.stored, snapshot, turnState, evidenceDraft: null };
}

export function createGuidedCandidateActions(ports: GuidedCandidatePorts) {
  return {
    async save(input: CandidateMutation) {
      const stored = await ownedCase(ports, input.userId, input.caseId);
      if (replayed(stored, input.actionId)) return storedJourneyResponse(stored);
      assertCurrentVersion(stored, input.expectedVersion);
      if (stored.candidateResult?.resultId !== input.resultId) {
        throw new GuidedCandidateActionError("invalid_candidate");
      }
      const value = {
        ...stored,
        turnState: savedTurn(stored, input.expectedVersion + 1),
      } satisfies StoredRectificationCase;
      return storedJourneyResponse(await ports.store.commitGuidedCandidate(value, {
        kind: "save", expectedVersion: input.expectedVersion, actionId: input.actionId,
      }));
    },
    async confirm(input: CandidateConfirmation) {
      const stored = await ownedCase(ports, input.userId, input.caseId);
      if (replayed(stored, input.actionId)) return storedJourneyResponse(stored);
      assertCurrentVersion(stored, input.expectedVersion);
      const value = confirmedTurn({
        stored,
        resultId: input.resultId,
        time: input.time,
        nextVersion: input.expectedVersion + 1,
      });
      return storedJourneyResponse(await ports.store.commitGuidedCandidate(value, {
        kind: "confirm", expectedVersion: input.expectedVersion, actionId: input.actionId,
      }));
    },
  };
}
