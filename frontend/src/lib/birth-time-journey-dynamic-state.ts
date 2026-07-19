import { z } from "zod";
import {
  dynamicControlStateSchema,
  persistedDynamicChoiceQuestionSchema,
  serverChoiceEvidenceSchema,
  storedChoiceAnswerSchema,
  toPublicDynamicChoiceQuestion,
} from "./birth-time-dynamic-choice-internal.ts";
import type {
  DynamicControlState,
  PersistedDynamicChoiceQuestion,
  ServerChoiceEvidence,
  StoredChoiceAnswer,
} from "./birth-time-dynamic-choice-internal.ts";
import { dynamicJourneyTurnStateSchema } from "./birth-time-journey-turn-protocol.ts";
import type { DynamicJourneyTurnState } from "./birth-time-journey-turn-protocol.ts";
import { timeRangeSchema } from "./birth-time-dynamic-choice.ts";
import type {
  DynamicStoredRectificationCase,
  LegacyStoredRectificationCase,
  StoredRectificationCase,
} from "./birth-time-journey-service.ts";
import type { JourneySnapshot } from "./birth-time-journey.ts";

const agentContextSchema = z.array(
  z.string().min(1).max(240).refine((value) => value.trim().length > 0),
).max(10).readonly();
export const dynamicPrivateStateSchema = z.object({
  candidateModel: z.record(z.unknown()).nullable(),
  currentChoiceQuestion: persistedDynamicChoiceQuestionSchema.nullable(),
  choiceAnswers: z.array(storedChoiceAnswerSchema).max(50).readonly(),
  choiceEvidence: z.array(serverChoiceEvidenceSchema).max(10).readonly(),
  dynamicControl: dynamicControlStateSchema,
  agentContext: agentContextSchema,
}).strict().readonly();
const dynamicPrivateRowSchema = z.object({
  case_id: z.string().uuid(),
  user_id: z.string().uuid(),
  candidate_model: z.record(z.unknown()).nullable(),
  current_choice_question: persistedDynamicChoiceQuestionSchema.nullable(),
  choice_answers: z.array(storedChoiceAnswerSchema).max(50).readonly(),
  choice_evidence: z.array(serverChoiceEvidenceSchema).max(10).readonly(),
  dynamic_control: dynamicControlStateSchema,
  agent_context: agentContextSchema,
}).strict().readonly();

export type DynamicPrivateJourneyState = {
  readonly candidateModel: Readonly<Record<string, unknown>> | null;
  readonly currentChoiceQuestion: PersistedDynamicChoiceQuestion | null;
  readonly choiceAnswers: readonly StoredChoiceAnswer[];
  readonly choiceEvidence: readonly ServerChoiceEvidence[];
  readonly dynamicControl: DynamicControlState;
  readonly agentContext: readonly string[];
};

export class BirthTimeDynamicStateMissingError extends Error {
  readonly name = "BirthTimeDynamicStateMissingError";
  readonly caseId: string;

  constructor(caseId: string) {
    super(`Dynamic birth-time state for ${caseId} is missing`);
    this.caseId = caseId;
  }
}

export class BirthTimeDynamicStateInvalidError extends Error {
  readonly name = "BirthTimeDynamicStateInvalidError";
  readonly caseId: string;

  constructor(caseId: string) {
    super(`Dynamic birth-time state for ${caseId} is invalid`);
    this.caseId = caseId;
  }
}

export function parseDynamicPrivateRow(
  value: unknown,
  userId: string,
  caseId: string,
): DynamicPrivateJourneyState {
  if (value === null) throw new BirthTimeDynamicStateMissingError(caseId);
  const parsed = dynamicPrivateRowSchema.safeParse(value);
  if (!parsed.success || parsed.data.case_id !== caseId || parsed.data.user_id !== userId) {
    throw new BirthTimeDynamicStateInvalidError(caseId);
  }
  return dynamicPrivateStateSchema.parse({
    candidateModel: parsed.data.candidate_model,
    currentChoiceQuestion: parsed.data.current_choice_question,
    choiceAnswers: parsed.data.choice_answers,
    choiceEvidence: parsed.data.choice_evidence,
    dynamicControl: parsed.data.dynamic_control,
    agentContext: parsed.data.agent_context,
  });
}

export function dynamicTurnMatchesPrivateQuestion(
  turn: DynamicJourneyTurnState,
  state: DynamicPrivateJourneyState,
): boolean {
  const action = turn.nextAction;
  if (action.kind !== "ask_dynamic_choice") return true;
  if (state.currentChoiceQuestion === null) return false;
  const projected = toPublicDynamicChoiceQuestion(state.currentChoiceQuestion);
  return projected.questionId === action.question.questionId
    && projected.prompt === action.question.prompt
    && projected.options.length === action.question.options.length
    && projected.options.every((option, index) => {
      const persisted = action.question.options[index];
      return persisted !== undefined
        && option.optionId === persisted.optionId
        && option.label === persisted.label
        && option.kind === persisted.kind;
    });
}

function rangeFrom(snapshot: JourneySnapshot) {
  const { startTime, endTime } = snapshot.reportedRange;
  return timeRangeSchema.parse(startTime === null && endTime === null
    ? { startTime: "00:00", endTime: "23:59" }
    : { startTime, endTime });
}

export function createInitialDynamicState(
  snapshot: JourneySnapshot,
  asOfDate: string,
): {
  readonly turn: DynamicJourneyTurnState;
  readonly privateState: DynamicPrivateJourneyState;
} {
  const currentRange = rangeFrom(snapshot);
  const dynamicControl = dynamicControlStateSchema.parse({
    asOfDate,
    answeredCount: 0,
    effectiveAnswerCount: 0,
    plateauCount: 0,
    questionFingerprints: [],
    partitionFingerprints: [],
    dismissedOpportunityIds: [],
    recentRanges: [currentRange],
    pausedAction: null,
    lastActionReceipt: null,
  });
  const ready = snapshot.state === "ready";
  return {
    turn: dynamicJourneyTurnStateSchema.parse({
      journeyProtocol: "dynamic-choice-v2",
      turnVersion: 0,
      nextAction: ready
        ? { kind: "ready", activeTime: snapshot.activeTime }
        : { kind: "generate_dynamic_question" },
      progress: {
        phase: ready ? "ready" : "question",
        answeredCount: 0,
        effectiveAnswerCount: 0,
        currentRange,
        previousRange: null,
        plateauCount: 0,
      },
      permissions: { canConfirmCandidate: false },
    }),
    privateState: {
      candidateModel: null,
      currentChoiceQuestion: null,
      choiceAnswers: [],
      choiceEvidence: [],
      dynamicControl,
      agentContext: [],
    },
  };
}

const terminalLegacyActions = new Set([
  "present_low_result",
  "present_medium_result",
  "candidate_saved",
  "request_candidate_confirmation",
  "ready",
]);

export function isTerminalLegacyCase(value: StoredRectificationCase): boolean {
  return value.snapshot.state === "candidate"
    || value.snapshot.state === "confirming"
    || value.snapshot.state === "ready"
    || terminalLegacyActions.has(value.turnState?.nextAction.kind ?? "");
}

export function prepareLegacyDynamicUpgrade(
  value: LegacyStoredRectificationCase,
  asOfDate: string,
): DynamicStoredRectificationCase {
  const currentRange = rangeFrom(value.snapshot);
  const confirmedCount = value.lifeEvents?.length ?? 0;
  const effectiveAnswerCount = Math.min(confirmedCount, 10);
  const answeredCount = Math.min(confirmedCount, 50);
  const dynamicControl = dynamicControlStateSchema.parse({
    asOfDate,
    answeredCount,
    effectiveAnswerCount,
    plateauCount: 0,
    questionFingerprints: [],
    partitionFingerprints: [],
    dismissedOpportunityIds: [],
    recentRanges: [currentRange],
    pausedAction: null,
    lastActionReceipt: null,
  });
  const dynamicTurnState = dynamicJourneyTurnStateSchema.parse({
    journeyProtocol: "dynamic-choice-v2",
    turnVersion: value.turnVersion ?? 0,
    nextAction: { kind: "generate_dynamic_question" },
    progress: {
      phase: "question",
      answeredCount,
      effectiveAnswerCount,
      currentRange,
      previousRange: null,
      plateauCount: 0,
    },
    permissions: { canConfirmCandidate: false },
  });
  return {
    ...value,
    journeyProtocol: "dynamic-choice-v2",
    turnVersion: value.turnVersion ?? 0,
    processedActionIds: value.processedActionIds ?? [],
    persistedProgress: value.persistedProgress ?? { adaptiveRound: 0, askedDomains: [] },
    turnState: null,
    evidenceDraft: null,
    dynamicTurnState,
    candidateModel: null,
    currentChoiceQuestion: null,
    choiceAnswers: [],
    choiceEvidence: [],
    dynamicControl,
    agentContext: [],
  };
}
