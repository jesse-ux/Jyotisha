import { withCandidateResult } from "./birth-time-evidence.ts";
import type { CandidateResult } from "./birth-time-evidence.ts";
import { decideDynamicStop } from "./birth-time-dynamic-stop-policy.ts";
import { toPublicDynamicChoiceQuestion } from "./birth-time-dynamic-choice-internal.ts";
import type {
  PausedDynamicAction,
  PersistedDynamicChoiceQuestion,
} from "./birth-time-dynamic-choice-internal.ts";
import type { DynamicNextAction } from "./birth-time-journey-turn-protocol.ts";
import type { DynamicStoredRectificationCase } from "./birth-time-journey-service.ts";
import type { TimeRange } from "./birth-time-dynamic-choice.ts";

const terminalKinds = new Set<DynamicNextAction["kind"]>([
  "present_low_result",
  "present_medium_result",
  "request_candidate_confirmation",
  "ready",
]);

export class DynamicPauseActionError extends Error {
  readonly code = "invalid_dynamic_pause_action";
  constructor(kind: DynamicNextAction["kind"]) {
    super(`Cannot pause dynamic action ${kind}`);
    this.name = "DynamicPauseActionError";
  }
}

export function isDynamicTerminal(value: DynamicStoredRectificationCase): boolean {
  return terminalKinds.has(value.dynamicTurnState.nextAction.kind);
}

export function publicQuestionAction(question: PersistedDynamicChoiceQuestion): DynamicNextAction {
  return { kind: "ask_dynamic_choice", question: toPublicDynamicChoiceQuestion(question) };
}

export function toPausedDynamicAction(action: DynamicNextAction): PausedDynamicAction {
  switch (action.kind) {
    case "ask_dynamic_choice":
      return { kind: action.kind, questionId: action.question.questionId };
    case "generate_dynamic_question":
    case "clarify_unmatched_answer":
    case "retry_question_generation":
    case "score_pending":
    case "retry_scoring":
      return action;
    case "present_low_result":
    case "present_medium_result":
    case "request_candidate_confirmation":
    case "ready":
    case "paused":
      throw new DynamicPauseActionError(action.kind);
  }
}

export function progressPhase(action: DynamicNextAction): DynamicStoredRectificationCase["dynamicTurnState"]["progress"]["phase"] {
  switch (action.kind) {
    case "generate_dynamic_question":
    case "ask_dynamic_choice":
    case "retry_question_generation":
      return "question";
    case "clarify_unmatched_answer":
      return "clarification";
    case "score_pending":
    case "retry_scoring":
      return "scoring";
    case "present_low_result":
    case "present_medium_result":
    case "request_candidate_confirmation":
      return "result";
    case "ready":
      return "ready";
    case "paused":
      return "paused";
  }
}

export function withDynamicAction(
  stored: DynamicStoredRectificationCase,
  action: DynamicNextAction,
  nextVersion: number,
): DynamicStoredRectificationCase {
  return {
    ...stored,
    dynamicTurnState: {
      ...stored.dynamicTurnState,
      turnVersion: nextVersion,
      nextAction: action,
      progress: { ...stored.dynamicTurnState.progress, phase: progressPhase(action) },
    },
  };
}

export function answerTransition(input: {
  readonly stored: DynamicStoredRectificationCase;
  readonly option: PersistedDynamicChoiceQuestion["options"][number];
  readonly answeredAt: string;
  readonly jobId: string;
  readonly nextVersion: number;
}): DynamicStoredRectificationCase {
  const { stored, option } = input;
  const question = stored.currentChoiceQuestion;
  if (question === null) return stored;
  const answeredCount = stored.dynamicControl.answeredCount + 1;
  const effective = option.kind === "primary";
  const effectiveAnswerCount = stored.dynamicControl.effectiveAnswerCount + (effective ? 1 : 0);
  const answer = {
    questionId: question.questionId,
    optionId: option.optionId,
    kind: option.kind,
    opportunityId: question.opportunityId,
    answeredAt: input.answeredAt,
  };
  const evidence = option.kind === "primary" ? [{
    questionId: question.questionId,
    opportunityId: question.opportunityId,
    partitionId: option.partitionId,
    dimensionCode: question.dimensionCode,
    candidateScores: option.candidateScores,
    informationGain: question.estimatedInformationGain,
  }] : [];
  const nextAction: DynamicNextAction = option.kind === "primary"
    ? { kind: "score_pending", jobId: input.jobId }
    : option.kind === "unknown"
      ? { kind: "generate_dynamic_question" }
      : { kind: "clarify_unmatched_answer", questionId: question.questionId };
  const cleared = option.kind === "unmatched" ? question : null;
  const dismissed = option.kind === "primary" || option.kind === "unmatched"
    ? stored.dynamicControl.dismissedOpportunityIds
    : [...stored.dynamicControl.dismissedOpportunityIds, question.opportunityId];
  const updated = withDynamicAction(stored, nextAction, input.nextVersion);
  return {
    ...updated,
    currentChoiceQuestion: cleared,
    choiceAnswers: [...stored.choiceAnswers, answer],
    choiceEvidence: [...stored.choiceEvidence, ...evidence],
    dynamicControl: {
      ...stored.dynamicControl,
      answeredCount,
      effectiveAnswerCount,
      dismissedOpportunityIds: dismissed,
    },
    dynamicTurnState: {
      ...updated.dynamicTurnState,
      progress: {
        ...updated.dynamicTurnState.progress,
        answeredCount,
        effectiveAnswerCount,
      },
    },
  };
}

export function completeDynamicScoreTransition(input: {
  readonly stored: DynamicStoredRectificationCase;
  readonly candidate: CandidateResult;
  readonly usefulOpportunityCount: number;
  readonly repeatedOnly: boolean;
  readonly nextVersion: number;
  readonly candidateModel?: Readonly<Record<string, unknown>>;
  readonly continuationRange?: TimeRange;
}): DynamicStoredRectificationCase {
  const stored = input.stored;
  const decision = decideDynamicStop({
    result: input.candidate,
    effectiveAnswer: true,
    previousResult: stored.candidateResult ?? null,
    priorPlateauCount: stored.dynamicControl.plateauCount,
    usefulOpportunityCount: input.usefulOpportunityCount,
    repeatedOnly: input.repeatedOnly,
    effectiveAnswerCount: stored.dynamicControl.effectiveAnswerCount,
    forcedReason: null,
  });
  const action: DynamicNextAction = input.candidate.confidence === "high"
    ? { kind: "request_candidate_confirmation", resultId: input.candidate.resultId }
    : decision.kind === "continue"
      ? { kind: "generate_dynamic_question" }
      : input.candidate.confidence === "medium"
        ? { kind: "present_medium_result", resultId: input.candidate.resultId }
        : { kind: "present_low_result", resultId: input.candidate.resultId };
  const priorRange = stored.dynamicTurnState.progress.currentRange;
  const segment = input.candidate.winningSegment;
  const candidateRange = segment === null
    ? priorRange
    : { startTime: segment.startTime, endTime: segment.endTime };
  const currentRange = decision.kind === "continue"
    ? input.continuationRange ?? candidateRange
    : candidateRange;
  const rangeChanged = currentRange.startTime !== priorRange.startTime
    || currentRange.endTime !== priorRange.endTime;
  const previousRange = rangeChanged
    ? priorRange
    : stored.dynamicTurnState.progress.previousRange;
  const updated = withDynamicAction(stored, action, input.nextVersion);
  return {
    ...updated,
    snapshot: withCandidateResult(stored.snapshot, input.candidate),
    candidateResult: input.candidate,
    candidateModel: input.candidateModel ?? stored.candidateModel,
    dynamicControl: {
      ...stored.dynamicControl,
      plateauCount: decision.plateauCount,
      recentRanges: [...stored.dynamicControl.recentRanges, candidateRange],
    },
    dynamicTurnState: {
      ...updated.dynamicTurnState,
      progress: {
        ...updated.dynamicTurnState.progress,
        currentRange,
        previousRange,
        plateauCount: decision.plateauCount,
      },
      permissions: { canConfirmCandidate: input.candidate.confidence === "high" },
    },
  };
}
