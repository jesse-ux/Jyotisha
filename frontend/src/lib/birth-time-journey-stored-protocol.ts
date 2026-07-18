import type {
  DynamicControlState,
  PersistedDynamicChoiceQuestion,
  ServerChoiceEvidence,
  StoredChoiceAnswer,
} from "./birth-time-dynamic-choice-internal.ts";
import type { DynamicJourneyTurnState } from "./birth-time-journey-turn-protocol.ts";
import type { EvidenceDraft, JourneyTurnState } from "./birth-time-journey-turn.ts";
import type { EvidenceDomain } from "./birth-time-question-planner.ts";

type LegacyProgress = {
  readonly adaptiveRound: number;
  readonly askedDomains: readonly EvidenceDomain[];
};

export type LegacyStoredFields = {
  readonly journeyProtocol?: "legacy-guided-v1";
  readonly turnVersion?: number;
  readonly turnState?: JourneyTurnState | null;
  readonly evidenceDraft?: EvidenceDraft | null;
  readonly processedActionIds?: readonly string[];
  readonly persistedProgress?: LegacyProgress;
  readonly dynamicTurnState?: never;
  readonly candidateModel?: never;
  readonly currentChoiceQuestion?: never;
  readonly choiceAnswers?: never;
  readonly choiceEvidence?: never;
  readonly dynamicControl?: never;
  readonly agentContext?: never;
};

export type DynamicStoredFields = {
  readonly journeyProtocol: "dynamic-choice-v2";
  readonly turnVersion: number;
  readonly turnState?: null;
  readonly dynamicTurnState: DynamicJourneyTurnState;
  readonly evidenceDraft?: null;
  readonly processedActionIds: readonly string[];
  readonly persistedProgress?: LegacyProgress;
  readonly candidateModel: Readonly<Record<string, unknown>> | null;
  readonly currentChoiceQuestion: PersistedDynamicChoiceQuestion | null;
  readonly choiceAnswers: readonly StoredChoiceAnswer[];
  readonly choiceEvidence: readonly ServerChoiceEvidence[];
  readonly dynamicControl: DynamicControlState;
  readonly agentContext: readonly string[];
};
