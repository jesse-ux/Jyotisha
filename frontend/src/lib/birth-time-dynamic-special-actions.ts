import { z } from "zod";
import { replayedDynamicAction } from "./birth-time-dynamic-action-replay.ts";
import { toPausedDynamicAction, withDynamicAction } from "./birth-time-dynamic-transitions.ts";
import { storedDynamicJourneyResponse } from "./birth-time-journey-response.ts";
import type { BirthTimeJourneyPorts, DynamicStoredRectificationCase } from "./birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "./birth-time-journey-store-errors.ts";

type UnmatchedCommand = {
  readonly caseId: string;
  readonly actionId: string;
  readonly turnVersion: number;
  readonly questionId: string;
  readonly note: string;
};

function stale(stored: DynamicStoredRectificationCase, expected: number) {
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

export function createDynamicSpecialActions(ports: BirthTimeJourneyPorts, load: (
  userId: string, caseId: string,
) => Promise<DynamicStoredRectificationCase>, requireMutable: (
  stored: DynamicStoredRectificationCase,
) => void) {
  const save = (stored: DynamicStoredRectificationCase, updated: DynamicStoredRectificationCase, actionId: string) => (
    ports.store.saveDynamicTurn(updated, stored.turnVersion, actionId)
  );
  return {
    async submitUnmatchedContext(userId: string, command: UnmatchedCommand) {
      const stored = await load(userId, command.caseId);
      const note = z.string().trim().max(240).parse(command.note);
      const priorAnswer = stored.choiceAnswers.at(-1);
      const receipt = stored.dynamicControl.lastActionReceipt;
      if (replayedDynamicAction(stored, command.actionId, command.turnVersion, () => (
        stored.dynamicTurnState.nextAction.kind === "generate_dynamic_question"
        && priorAnswer?.kind === "unmatched" && priorAnswer.questionId === command.questionId
        && priorAnswer.unmatchedContext === note
        && receipt?.actionId === command.actionId.toLowerCase()
        && receipt.kind === "unmatched_context" && receipt.turnVersion === command.turnVersion
        && receipt.questionId === command.questionId && receipt.note === note
      ))) return storedDynamicJourneyResponse(stored);
      requireMutable(stored);
      const question = stored.currentChoiceQuestion;
      if (stored.turnVersion !== command.turnVersion
        || stored.dynamicTurnState.nextAction.kind !== "clarify_unmatched_answer"
        || question?.questionId !== command.questionId
        || priorAnswer?.kind !== "unmatched"
        || priorAnswer.questionId !== command.questionId) throw stale(stored, command.turnVersion);
      const updated = withDynamicAction(stored, { kind: "generate_dynamic_question" }, stored.turnVersion + 1);
      const saved = await save(stored, {
        ...updated,
        currentChoiceQuestion: null,
        choiceAnswers: [...stored.choiceAnswers.slice(0, -1), { ...priorAnswer, unmatchedContext: note }],
        agentContext: note.length === 0 ? stored.agentContext : [...stored.agentContext.slice(-9), note],
        dynamicControl: {
          ...stored.dynamicControl,
          dismissedOpportunityIds: [...stored.dynamicControl.dismissedOpportunityIds, question.opportunityId],
          lastActionReceipt: {
            actionId: command.actionId.toLowerCase(), kind: "unmatched_context",
            turnVersion: command.turnVersion, questionId: command.questionId, note,
          },
        },
      }, command.actionId);
      return storedDynamicJourneyResponse(saved);
    },

    async pauseDynamic(userId: string, caseId: string, actionId: string, turnVersion: number) {
      const stored = await load(userId, caseId);
      const receipt = stored.dynamicControl.lastActionReceipt;
      if (replayedDynamicAction(stored, actionId, turnVersion, () => (
        stored.dynamicTurnState.nextAction.kind === "paused"
        && stored.dynamicControl.pausedAction !== null
        && receipt?.actionId === actionId.toLowerCase()
        && receipt.kind === "pause" && receipt.turnVersion === turnVersion
      ))) return storedDynamicJourneyResponse(stored);
      requireMutable(stored);
      if (stored.turnVersion !== turnVersion || stored.dynamicTurnState.nextAction.kind === "paused") {
        throw stale(stored, turnVersion);
      }
      const pausedAction = toPausedDynamicAction(stored.dynamicTurnState.nextAction);
      const updated = withDynamicAction(stored, { kind: "paused" }, stored.turnVersion + 1);
      const saved = await save(stored, {
        ...updated,
        dynamicControl: {
          ...stored.dynamicControl,
          pausedAction,
          lastActionReceipt: { actionId: actionId.toLowerCase(), kind: "pause", turnVersion },
        },
      }, actionId);
      return storedDynamicJourneyResponse(saved);
    },

    async finishDynamic(userId: string, caseId: string, actionId: string, turnVersion: number) {
      const stored = await load(userId, caseId);
      const receipt = stored.dynamicControl.lastActionReceipt;
      if (replayedDynamicAction(stored, actionId, turnVersion, () => (
        (stored.dynamicTurnState.nextAction.kind === "present_low_result"
          || stored.dynamicTurnState.nextAction.kind === "present_medium_result")
        && receipt?.actionId === actionId.toLowerCase()
        && receipt.kind === "finish" && receipt.turnVersion === turnVersion
      ))) return storedDynamicJourneyResponse(stored);
      requireMutable(stored);
      if (stored.turnVersion !== turnVersion) throw stale(stored, turnVersion);
      const candidate = stored.candidateResult;
      const action = candidate?.confidence === "medium"
        ? { kind: "present_medium_result" as const, resultId: candidate.resultId }
        : { kind: "present_low_result" as const, resultId: candidate?.resultId ?? null };
      const updated = withDynamicAction(stored, action, stored.turnVersion + 1);
      const saved = await save(stored, {
        ...updated,
        snapshot: terminalSnapshot(stored),
        currentChoiceQuestion: null,
        dynamicControl: {
          ...stored.dynamicControl,
          lastActionReceipt: { actionId: actionId.toLowerCase(), kind: "finish", turnVersion },
        },
      }, actionId);
      return storedDynamicJourneyResponse(saved);
    },
  };
}
