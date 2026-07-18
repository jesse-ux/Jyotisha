import { z } from "zod";
import { toPublicDynamicChoiceQuestion } from "./birth-time-dynamic-choice-internal.ts";
import {
  dynamicJourneyTurnStateSchema,
} from "./birth-time-journey-turn-protocol.ts";
import type { DynamicJourneyTurnState } from "./birth-time-journey-turn-protocol.ts";
import type {
  DynamicStoredRectificationCase,
  LegacyStoredRectificationCase,
  StoredRectificationCase,
} from "./birth-time-journey-service.ts";
import {
  dynamicPrivateStateSchema,
  isTerminalLegacyCase,
  prepareLegacyDynamicUpgrade,
} from "./birth-time-journey-dynamic-state.ts";
import type { DynamicPrivateJourneyState } from "./birth-time-journey-dynamic-state.ts";
import {
  BirthTimeJourneyStoreError,
  StaleJourneyTurnError,
} from "./birth-time-journey-store-errors.ts";

export { BirthTimeDynamicStateMissingError } from "./birth-time-journey-dynamic-state.ts";

const actionIdSchema = z.string().uuid();
const rpcVersionSchema = z.number().int().nonnegative();
type RpcError = { readonly message: string };
type RpcResult = { readonly data: unknown; readonly error: RpcError | null };
export type DynamicRpcClient = {
  readonly rpc: (
    name: string,
    args: Readonly<Record<string, unknown>>,
  ) => PromiseLike<RpcResult>;
};

function publicTurn(
  value: DynamicStoredRectificationCase,
  turnVersion: number,
): DynamicJourneyTurnState {
  const currentQuestion = value.currentChoiceQuestion;
  if (value.dynamicTurnState.nextAction.kind === "ask_dynamic_choice") {
    if (currentQuestion === null) throw new BirthTimeJourneyStoreError("update_case");
    return dynamicJourneyTurnStateSchema.parse({
      ...value.dynamicTurnState,
      turnVersion,
      nextAction: {
        kind: "ask_dynamic_choice",
        question: toPublicDynamicChoiceQuestion(currentQuestion),
      },
    });
  }
  return dynamicJourneyTurnStateSchema.parse({
    ...value.dynamicTurnState,
    turnVersion,
  });
}

function privateState(value: DynamicStoredRectificationCase): DynamicPrivateJourneyState {
  return dynamicPrivateStateSchema.parse({
    candidateModel: value.candidateModel,
    currentChoiceQuestion: value.currentChoiceQuestion,
    choiceAnswers: value.choiceAnswers,
    choiceEvidence: value.choiceEvidence,
    dynamicControl: value.dynamicControl,
    agentContext: value.agentContext,
  });
}

function isStaleRpc(error: RpcError): boolean {
  return error.message.includes("stale_birth_time_dynamic_turn")
    || error.message.includes("stale_birth_time_legacy_upgrade");
}

export function createDynamicTurnPersistence(
  client: DynamicRpcClient,
  loadCase: (userId: string, caseId: string) => Promise<StoredRectificationCase | null>,
  asOfDate: () => string,
) {
  async function loadedDynamic(userId: string, caseId: string): Promise<DynamicStoredRectificationCase> {
    const loaded = await loadCase(userId, caseId);
    if (!loaded || loaded.journeyProtocol !== "dynamic-choice-v2") {
      throw new BirthTimeJourneyStoreError("load_case");
    }
    return loaded;
  }

  return {
    async saveDynamicTurn(
      value: DynamicStoredRectificationCase,
      expectedVersion: number,
      actionId: string,
    ): Promise<DynamicStoredRectificationCase> {
      const receipt = actionIdSchema.parse(actionId).toLowerCase();
      const result = await client.rpc("save_birth_time_dynamic_turn", {
        p_user_id: value.userId,
        p_case_id: value.id,
        p_expected_version: expectedVersion,
        p_action_id: receipt,
        p_public_turn_state: publicTurn(value, expectedVersion + 1),
        p_snapshot: value.snapshot,
        p_candidate_result: value.candidateResult ?? {},
        p_private_state: privateState(value),
      });
      if (result.error) {
        const current = await loadCase(value.userId, value.id);
        if (isStaleRpc(result.error) && current?.processedActionIds?.includes(receipt)) {
          return loadedDynamic(value.userId, value.id);
        }
        if (isStaleRpc(result.error)) {
          throw new StaleJourneyTurnError(
            value.id,
            expectedVersion,
            current?.turnVersion ?? 0,
          );
        }
        throw new BirthTimeJourneyStoreError("update_case");
      }
      rpcVersionSchema.parse(result.data);
      return loadedDynamic(value.userId, value.id);
    },

    async upgradeLegacyActiveCase(
      value: LegacyStoredRectificationCase,
    ): Promise<StoredRectificationCase> {
      if (isTerminalLegacyCase(value)) return value;
      const upgraded = prepareLegacyDynamicUpgrade(value, asOfDate());
      const result = await client.rpc("upgrade_birth_time_legacy_case", {
        p_user_id: value.userId,
        p_case_id: value.id,
        p_expected_version: value.turnVersion ?? 0,
        p_public_turn_state: upgraded.dynamicTurnState,
        p_private_state: privateState(upgraded),
      });
      if (result.error) {
        if (isStaleRpc(result.error)) {
          const current = await loadCase(value.userId, value.id);
          throw new StaleJourneyTurnError(
            value.id,
            value.turnVersion ?? 0,
            current?.turnVersion ?? 0,
          );
        }
        throw new BirthTimeJourneyStoreError("update_case");
      }
      rpcVersionSchema.parse(result.data);
      return loadedDynamic(value.userId, value.id);
    },
  };
}
