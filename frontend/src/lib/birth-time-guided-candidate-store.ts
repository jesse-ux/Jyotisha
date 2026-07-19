import type { BirthTimeJourneyStore } from "./birth-time-journey-service.ts";
import { BirthTimeJourneyStoreError, StaleJourneyTurnError } from "./birth-time-journey-turn-persistence.ts";

type GuidedCandidateMethods = Pick<BirthTimeJourneyStore, "commitGuidedCandidate">;

export type GuidedCandidateRpcClient = {
  rpc(
    functionName: string,
    args: Readonly<Record<string, unknown>>,
  ): PromiseLike<{
    readonly error: { readonly code?: string; readonly message?: string } | null;
  }>;
};

function isDomainError(error: { readonly code?: string; readonly message?: string }, token: string): boolean {
  return error.code === "P0001" && error.message === token;
}

export class GuidedCandidateStoreConflictError extends Error {
  readonly name = "GuidedCandidateStoreConflictError";
}

export function createSupabaseGuidedCandidateStore(
  supabase: GuidedCandidateRpcClient,
  loadCase: BirthTimeJourneyStore["loadCase"],
): GuidedCandidateMethods {
  return {
    async commitGuidedCandidate(value, command) {
      if (!value.turnState || !value.candidateResult) {
        throw new BirthTimeJourneyStoreError("update_case");
      }
      const functionName = command.kind === "save"
        ? "save_guided_birth_time_candidate"
        : "confirm_guided_birth_time_candidate";
      const args = command.kind === "save"
        ? {
            p_user_id: value.userId,
            p_case_id: value.id,
            p_result_id: value.candidateResult.resultId,
            p_action_id: command.actionId,
            p_expected_version: command.expectedVersion,
            p_turn_state: value.turnState,
          }
        : {
            p_user_id: value.userId,
            p_case_id: value.id,
            p_result_id: value.candidateResult.resultId,
            p_time: value.snapshot.activeTime,
            p_action_id: command.actionId,
            p_expected_version: command.expectedVersion,
            p_snapshot: value.snapshot,
            p_turn_state: value.turnState,
          };
      const { error } = await supabase.rpc(functionName, args);
      if (error) {
        const current = await loadCase(value.userId, value.id);
        if (
          current?.journeyProtocol === "legacy-guided-v1"
          && current.processedActionIds?.includes(command.actionId.toLowerCase())
        ) return current;
        if (isDomainError(error, "stale_guided_candidate_turn")) {
          throw new StaleJourneyTurnError(
            value.id,
            command.expectedVersion,
            current?.turnVersion ?? 0,
          );
        }
        if (isDomainError(error, "invalid_guided_candidate_turn")) {
          throw new GuidedCandidateStoreConflictError("Guided candidate turn is invalid");
        }
        throw new BirthTimeJourneyStoreError("update_case");
      }
      const current = await loadCase(value.userId, value.id);
      if (!current || current.journeyProtocol !== "legacy-guided-v1") {
        throw new BirthTimeJourneyStoreError("load_case");
      }
      return current;
    },
  };
}
