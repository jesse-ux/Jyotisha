import { replayedDynamicAction } from "./birth-time-dynamic-action-replay.ts";
import type { PersistedDynamicChoiceQuestion } from "./birth-time-dynamic-choice-internal.ts";
import { dynamicDifferenceInput } from "./birth-time-dynamic-engine-input.ts";
import { publicQuestionAction } from "./birth-time-dynamic-transitions.ts";
import { answerTransition, isDynamicTerminal, withDynamicAction } from "./birth-time-dynamic-transitions.ts";
import { createDynamicSpecialActions } from "./birth-time-dynamic-special-actions.ts";
import { storedDynamicJourneyResponse } from "./birth-time-journey-response.ts";
import type {
  BirthTimeJourneyEngine,
  BirthTimeJourneyPorts,
  DynamicStoredRectificationCase,
  StoredRectificationCase,
} from "./birth-time-journey-service.ts";
import { createDynamicScoringJobSpec } from "./birth-time-scoring-job.ts";
import { StaleJourneyTurnError } from "./birth-time-journey-store-errors.ts";

type ChoiceCommand = {
  readonly caseId: string;
  readonly actionId: string;
  readonly turnVersion: number;
  readonly questionId: string;
  readonly optionId: string;
};
type TurnCommand = Pick<ChoiceCommand, "caseId" | "actionId" | "turnVersion">;
type QuestionCommand = TurnCommand & { readonly unmatchedNote?: string | null };

export class BirthTimeDynamicActionError extends Error {
  readonly name = "BirthTimeDynamicActionError";
  readonly reason: "case_not_found" | "invalid_turn" | "terminal" | "unavailable";

  constructor(reason: BirthTimeDynamicActionError["reason"]) {
    super(`Birth-time dynamic action ${reason}`);
    this.reason = reason;
  }
}

function requireDynamic(value: StoredRectificationCase | null): DynamicStoredRectificationCase {
  if (value === null) throw new BirthTimeDynamicActionError("case_not_found");
  if (value.journeyProtocol !== "dynamic-choice-v2") {
    throw new BirthTimeDynamicActionError("invalid_turn");
  }
  return value;
}

function dynamicEngine(engine: BirthTimeJourneyPorts["engine"]): Pick<BirthTimeJourneyEngine,
  "buildDifferencePacket" | "scoreChoices"
> {
  if (!("buildDifferencePacket" in engine) || !("scoreChoices" in engine)) {
    throw new BirthTimeDynamicActionError("unavailable");
  }
  return engine;
}

function stale(stored: DynamicStoredRectificationCase, expected: number): StaleJourneyTurnError {
  return new StaleJourneyTurnError(stored.id, expected, stored.turnVersion);
}

function terminalSnapshot(stored: DynamicStoredRectificationCase) {
  return {
    ...stored.snapshot,
    state: "candidate" as const,
    assistantIntent: "present_saved_candidate_range" as const,
    input: "candidate_actions" as const,
    confidence: stored.candidateResult?.confidence ?? "low" as const,
    canApply: false,
    activeTime: null,
  };
}

export function createDynamicJourneyActions(ports: BirthTimeJourneyPorts) {
  async function load(userId: string, caseId: string) {
    return requireDynamic(await ports.store.loadCase(userId, caseId));
  }

  function requireMutable(stored: DynamicStoredRectificationCase): void {
    if (isDynamicTerminal(stored)) throw new BirthTimeDynamicActionError("terminal");
  }

  async function save(
    stored: DynamicStoredRectificationCase,
    updated: DynamicStoredRectificationCase,
    actionId: string,
  ) {
    return ports.store.saveDynamicTurn(updated, stored.turnVersion, actionId);
  }
  const specialActions = createDynamicSpecialActions(ports, load, requireMutable);

  return {
    ...specialActions,
    async answerDynamicChoice(userId: string, command: ChoiceCommand) {
      const stored = await load(userId, command.caseId);
      const lastAnswer = stored.choiceAnswers.at(-1);
      const actionKind = stored.dynamicTurnState.nextAction.kind;
      if (replayedDynamicAction(stored, command.actionId, command.turnVersion, () => (
        lastAnswer?.questionId === command.questionId && lastAnswer.optionId === command.optionId
        && stored.dynamicControl.lastActionReceipt?.actionId !== command.actionId.toLowerCase()
        && (lastAnswer.kind === "primary"
          ? actionKind === "score_pending"
          : lastAnswer.kind === "unknown"
            ? actionKind === "generate_dynamic_question"
            : actionKind === "clarify_unmatched_answer")
      ))) {
        return storedDynamicJourneyResponse(stored);
      }
      requireMutable(stored);
      const action = stored.dynamicTurnState.nextAction;
      const question = stored.currentChoiceQuestion;
      if (stored.turnVersion !== command.turnVersion
        || action.kind !== "ask_dynamic_choice"
        || action.question.questionId !== command.questionId
        || question?.questionId !== command.questionId) {
        throw stale(stored, command.turnVersion);
      }
      const option = question.options.find((item) => item.optionId === command.optionId);
      if (!option) throw stale(stored, command.turnVersion);
      const updated = answerTransition({
        stored,
        option,
        answeredAt: (ports.now?.() ?? new Date()).toISOString(),
        jobId: globalThis.crypto.randomUUID(),
        nextVersion: stored.turnVersion + 1,
      });
      if (option.kind === "primary") {
        const createJob = ports.store.createDynamicScoringJob;
        if (!createJob) throw new BirthTimeDynamicActionError("unavailable");
        const spec = createDynamicScoringJobSpec(
          updated.dynamicTurnState.nextAction.kind === "score_pending"
            ? updated.dynamicTurnState.nextAction.jobId
            : "",
          updated.choiceEvidence,
          ports.now?.() ?? new Date(),
        );
        const saved = await createJob(
          updated,
          stored.turnVersion,
          command.actionId,
          question.questionId,
          spec,
        );
        return storedDynamicJourneyResponse(saved);
      }
      return storedDynamicJourneyResponse(await save(stored, updated, command.actionId));
    },

    async loadDynamicQuestionBuild(userId: string, command: QuestionCommand) {
      const stored = await load(userId, command.caseId);
      requireMutable(stored);
      const kind = stored.dynamicTurnState.nextAction.kind;
      if (stored.turnVersion !== command.turnVersion
        || (kind !== "generate_dynamic_question" && kind !== "retry_question_generation")) {
        throw stale(stored, command.turnVersion);
      }
      return dynamicEngine(ports.engine).buildDifferencePacket(dynamicDifferenceInput(stored));
    },

    async commitDynamicQuestion(
      userId: string,
      command: QuestionCommand,
      question: PersistedDynamicChoiceQuestion | null,
    ) {
      const stored = await load(userId, command.caseId);
      if (replayedDynamicAction(stored, command.actionId, command.turnVersion, () => (
        question === null
          ? stored.currentChoiceQuestion === null
            && stored.dynamicTurnState.nextAction.kind === "present_low_result"
          : stored.currentChoiceQuestion?.questionId === question.questionId
            && stored.currentChoiceQuestion.questionFingerprint === question.questionFingerprint
            && stored.dynamicControl.lastActionReceipt?.actionId !== command.actionId.toLowerCase()
      ))) {
        return { nextAction: stored.dynamicTurnState.nextAction };
      }
      requireMutable(stored);
      const kind = stored.dynamicTurnState.nextAction.kind;
      if (stored.turnVersion !== command.turnVersion
        || (kind !== "generate_dynamic_question" && kind !== "retry_question_generation")) {
        throw stale(stored, command.turnVersion);
      }
      const repeated = question !== null && (
        stored.dynamicControl.questionFingerprints.includes(question.questionFingerprint)
        || stored.dynamicControl.partitionFingerprints.includes(question.candidatePartitionFingerprint)
      );
      const nextQuestion = repeated ? null : question;
      const action = nextQuestion === null
        ? { kind: "present_low_result" as const, resultId: stored.candidateResult?.resultId ?? null }
        : publicQuestionAction(nextQuestion);
      const updated = withDynamicAction(stored, action, stored.turnVersion + 1);
      const saved = await save(stored, {
        ...updated,
        snapshot: nextQuestion === null ? terminalSnapshot(stored) : stored.snapshot,
        currentChoiceQuestion: nextQuestion,
        dynamicControl: nextQuestion === null ? stored.dynamicControl : {
          ...stored.dynamicControl,
          questionFingerprints: [...stored.dynamicControl.questionFingerprints, nextQuestion.questionFingerprint],
          partitionFingerprints: [...stored.dynamicControl.partitionFingerprints, nextQuestion.candidatePartitionFingerprint],
        },
      }, command.actionId);
      return { nextAction: saved.dynamicTurnState.nextAction };
    },

    async resumeDynamic(userId: string, caseId: string) {
      const stored = await load(userId, caseId);
      if (isDynamicTerminal(stored) || stored.dynamicTurnState.nextAction.kind !== "paused") {
        return storedDynamicJourneyResponse(stored);
      }
      const paused = stored.dynamicControl.pausedAction;
      if (paused === null) throw new BirthTimeDynamicActionError("invalid_turn");
      const action = paused.kind === "ask_dynamic_choice"
        ? stored.currentChoiceQuestion?.questionId === paused.questionId
          ? publicQuestionAction(stored.currentChoiceQuestion)
          : null
        : paused;
      if (action === null) throw new BirthTimeDynamicActionError("invalid_turn");
      const updated = withDynamicAction(stored, action, stored.turnVersion + 1);
      const saved = await save(stored, {
        ...updated,
        dynamicControl: { ...stored.dynamicControl, pausedAction: null },
      }, globalThis.crypto.randomUUID());
      return storedDynamicJourneyResponse(saved);
    },

  };
}
