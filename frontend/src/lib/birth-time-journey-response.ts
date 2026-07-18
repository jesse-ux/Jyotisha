import {
  projectJourneyTurn,
  type JourneyTurnState,
} from "./birth-time-journey-turn.ts";
import type { PersistedJourneyProgress } from "./birth-time-journey-turn-persistence.ts";
import type {
  DynamicStoredRectificationCase,
  DynamicVersionedJourneyResponse,
  JourneyResponseBase,
  StoredRectificationCase,
  VersionedJourneyResponse,
} from "./birth-time-journey-service.ts";
import type { JourneySnapshot } from "./birth-time-journey.ts";

export function questionJourneySnapshot(stored: StoredRectificationCase): JourneySnapshot {
  return {
    ...stored.snapshot,
    state: "rectifying",
    assistantIntent: "continue_rectification_questions",
    input: "rectification_questions",
    route: "rectification",
    confidence: stored.candidateResult?.confidence === "low" ? "low" : null,
    canApply: false,
    activeTime: null,
  };
}

export function terminalJourneySnapshot(stored: StoredRectificationCase): JourneySnapshot {
  return {
    ...stored.snapshot,
    state: "candidate",
    assistantIntent: "present_saved_candidate_range",
    input: "candidate_actions",
    route: "rectification",
    confidence: "low",
    canApply: false,
    activeTime: null,
  };
}

export function projectJourneyResponse(
  response: JourneyResponseBase,
  turnVersion: number,
  persistedProgress?: PersistedJourneyProgress | null,
): VersionedJourneyResponse {
  return {
    ...response,
    ...projectJourneyTurn({
      turnVersion,
      snapshot: response.snapshot,
      questionnaire: response.questionnaire,
      persistedProgress,
      candidateResult: response.candidateResult,
      lifeEvents: response.lifeEvents,
    }),
  };
}

export function currentJourneyTurn(
  stored: StoredRectificationCase,
): JourneyTurnState {
  const turnVersion = stored.turnVersion ?? 0;
  if (stored.turnState) {
    const evidenceDraft = stored.evidenceDraft ?? stored.turnState.evidenceDraft;
    if (stored.turnState.nextAction.kind === "paused") {
      if (evidenceDraft) {
        return {
          ...stored.turnState,
          turnVersion,
          nextAction: { kind: "review_evidence_draft", draftId: evidenceDraft.draftId },
          progress: { ...stored.turnState.progress, phase: "review" },
          evidenceDraft,
        };
      }
      return legacyScorePending(stored, projectStoredTurn(stored, turnVersion));
    }
    return {
      ...stored.turnState,
      turnVersion,
      evidenceDraft,
    };
  }
  return legacyScorePending(stored, projectStoredTurn(stored, turnVersion));
}

function projectStoredTurn(
  stored: StoredRectificationCase,
  turnVersion: number,
): JourneyTurnState {
  return projectJourneyTurn({
    turnVersion,
    snapshot: stored.snapshot,
    questionnaire: stored.questionnaire,
    persistedProgress: stored.persistedProgress,
    candidateResult: stored.candidateResult ?? null,
    lifeEvents: stored.lifeEvents ?? [],
  });
}

function legacyScorePending(
  stored: StoredRectificationCase,
  projected: JourneyTurnState,
): JourneyTurnState {
  const events = stored.lifeEvents ?? [];
  const domainCount = new Set(events.map((event) => event.domain)).size;
  const acceptsEvidence = stored.snapshot.route === "rectification"
    && (stored.snapshot.input === "life_events" || stored.snapshot.input === "rectification_questions");
  if (
    projected.nextAction.kind !== "paused"
    || stored.candidateResult
    || events.length < 3
    || domainCount < 2
    || !acceptsEvidence
  ) return projected;
  return {
    ...projected,
    nextAction: { kind: "score_pending", jobId: stored.id },
    progress: { ...projected.progress, phase: "scoring" },
  };
}

export function storedJourneyResponse(
  stored: StoredRectificationCase,
): VersionedJourneyResponse {
  return {
    caseId: stored.id,
    snapshot: stored.snapshot,
    questionnaire: stored.questionnaire,
    scoring: stored.scoring ?? null,
    answers: stored.answers,
    lifeEvents: stored.lifeEvents ?? [],
    candidateResult: stored.candidateResult ?? null,
    ...currentJourneyTurn(stored),
  };
}

export function storedDynamicJourneyResponse(
  stored: DynamicStoredRectificationCase,
): DynamicVersionedJourneyResponse {
  return {
    caseId: stored.id,
    snapshot: stored.snapshot,
    questionnaire: stored.questionnaire,
    scoring: stored.scoring ?? null,
    answers: stored.answers,
    lifeEvents: stored.lifeEvents ?? [],
    candidateResult: stored.candidateResult ?? null,
    evidenceDraft: null,
    ...stored.dynamicTurnState,
  };
}

export function persistedJourneyResponse(
  stored: StoredRectificationCase,
): VersionedJourneyResponse {
  if (!stored.turnState) return storedJourneyResponse(stored);
  return {
    caseId: stored.id,
    snapshot: stored.snapshot,
    questionnaire: stored.questionnaire,
    scoring: stored.scoring ?? null,
    answers: stored.answers,
    lifeEvents: stored.lifeEvents ?? [],
    candidateResult: stored.candidateResult ?? null,
    ...stored.turnState,
    turnVersion: stored.turnVersion ?? stored.turnState.turnVersion,
    evidenceDraft: stored.evidenceDraft ?? stored.turnState.evidenceDraft,
  };
}
