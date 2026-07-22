import { withConfirmedCandidate } from "./birth-time-evidence.ts";
import { replayedDynamicAction } from "./birth-time-dynamic-action-replay.ts";
import { withDynamicAction } from "./birth-time-dynamic-transitions.ts";
import { BirthTimeDynamicActionError } from "./birth-time-dynamic-actions.ts";
import { storedDynamicJourneyResponse } from "./birth-time-journey-response.ts";
import type {
  BirthTimeJourneyPorts,
  DynamicCandidateConfirmationCommand,
  DynamicStoredRectificationCase,
} from "./birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "./birth-time-journey-store-errors.ts";

function stale(stored: DynamicStoredRectificationCase, expectedVersion: number) {
  return new StaleJourneyTurnError(stored.id, expectedVersion, stored.turnVersion);
}

export function createDynamicCandidateConfirmation(ports: BirthTimeJourneyPorts) {
  return {
    async confirm(input: DynamicCandidateConfirmationCommand) {
      const stored = await ports.store.loadCase(input.userId, input.caseId);
      if (!stored) throw new BirthTimeDynamicActionError("case_not_found");
      if (stored.journeyProtocol !== "dynamic-choice-v2") {
        throw new BirthTimeDynamicActionError("invalid_turn");
      }
      const receipt = stored.dynamicControl.lastActionReceipt;
      if (replayedDynamicAction(stored, input.actionId, input.expectedVersion, () => (
        stored.dynamicTurnState.nextAction.kind === "ready"
        && stored.dynamicTurnState.nextAction.activeTime === input.time
        && stored.snapshot.activeTime === input.time
        && receipt?.kind === "confirm_candidate"
        && receipt.actionId === input.actionId.toLowerCase()
        && receipt.turnVersion === input.expectedVersion
        && receipt.resultId === input.resultId
        && receipt.time === input.time
      ))) return storedDynamicJourneyResponse(stored);

      const action = stored.dynamicTurnState.nextAction;
      const candidate = stored.candidateResult;
      if (
        stored.turnVersion !== input.expectedVersion
        || action.kind !== "request_candidate_confirmation"
        || action.resultId !== input.resultId
        || !stored.dynamicTurnState.permissions.canConfirmCandidate
        || candidate?.resultId !== input.resultId
        || candidate.canApply !== true
        || candidate.winningSegment?.representativeTime !== input.time
      ) throw stale(stored, input.expectedVersion);

      const transitioned = withDynamicAction(
        stored,
        { kind: "ready", activeTime: input.time },
        input.expectedVersion + 1,
      );
      const updated = {
        ...transitioned,
        snapshot: withConfirmedCandidate(stored.snapshot, candidate, input.time),
        currentChoiceQuestion: null,
        dynamicTurnState: {
          ...transitioned.dynamicTurnState,
          permissions: { canConfirmCandidate: false },
        },
        dynamicControl: {
          ...stored.dynamicControl,
          lastActionReceipt: {
            actionId: input.actionId.toLowerCase(),
            kind: "confirm_candidate" as const,
            turnVersion: input.expectedVersion,
            resultId: input.resultId,
            time: input.time,
          },
        },
      } satisfies DynamicStoredRectificationCase;
      return storedDynamicJourneyResponse(await ports.store.confirmDynamicCandidate(updated, input));
    },
  };
}
