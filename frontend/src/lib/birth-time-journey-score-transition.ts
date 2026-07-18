import {
  withCandidateResult,
  type CandidateResult,
} from "./birth-time-evidence.ts";
import { terminalJourneySnapshot } from "./birth-time-journey-response.ts";
import {
  projectJourneyTurn,
  type JourneyTurnState,
} from "./birth-time-journey-turn.ts";
import type { LegacyStoredRectificationCase as StoredRectificationCase } from "./birth-time-journey-service.ts";

type CompleteScoreTransitionInput = {
  readonly stored: StoredRectificationCase;
  readonly candidateResult: CandidateResult;
  readonly nextVersion: number;
};

function completedTurn(
  stored: StoredRectificationCase,
  candidateResult: CandidateResult,
  nextVersion: number,
): JourneyTurnState {
  return projectJourneyTurn({
    turnVersion: nextVersion,
    snapshot: stored.snapshot,
    questionnaire: stored.questionnaire,
    persistedProgress: stored.persistedProgress,
    candidateResult,
    lifeEvents: stored.lifeEvents ?? [],
  });
}

function terminalLowTurn(turn: JourneyTurnState): JourneyTurnState {
  if (turn.nextAction.kind !== "present_low_result") return turn;
  return {
    ...turn,
    progress: { ...turn.progress, phase: "result" },
  };
}

export function completeScoreTransition(
  input: CompleteScoreTransitionInput,
): StoredRectificationCase {
  const scoredSnapshot = withCandidateResult(
    input.stored.snapshot,
    input.candidateResult,
  );
  const scored = {
    ...input.stored,
    snapshot: scoredSnapshot,
    candidateResult: input.candidateResult,
    evidenceDraft: null,
  } satisfies StoredRectificationCase;
  const turnState = terminalLowTurn(completedTurn(
    scored,
    input.candidateResult,
    input.nextVersion,
  ));
  const snapshot = turnState.nextAction.kind === "present_low_result"
    ? terminalJourneySnapshot(scored)
    : scoredSnapshot;
  return {
    ...scored,
    snapshot,
    turnState,
    persistedProgress: {
      adaptiveRound: turnState.progress.adaptiveRound,
      askedDomains: scored.persistedProgress?.askedDomains ?? [],
    },
  };
}
