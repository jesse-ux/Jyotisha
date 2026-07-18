import type { LifeEvent } from "./birth-time-evidence.ts";
import {
  deriveJourneyPermissions,
  type EvidenceDraft,
  type JourneyProgress,
  type JourneyTurnState,
  type NextAction,
} from "./birth-time-journey-turn.ts";
import {
  evidenceDomains,
  planEvidenceQuestion,
  type EvidenceDomain,
  type EvidenceQuestionPhase,
  type QuestionSpec,
} from "./birth-time-question-planner.ts";
import {
  questionJourneySnapshot,
  terminalJourneySnapshot,
} from "./birth-time-journey-response.ts";
import type { StoredRectificationCase } from "./birth-time-journey-service.ts";

type PlannedTurnInput = {
  readonly stored: StoredRectificationCase;
  readonly phase: EvidenceQuestionPhase;
  readonly askedDomains: readonly EvidenceDomain[];
  readonly adaptiveRound: number;
  readonly turnVersion: number;
};

export type EvidenceQuestionIdentity = Pick<QuestionSpec, "questionId" | "phase" | "domain">;

function coveredDomains(events: readonly LifeEvent[]): readonly EvidenceDomain[] {
  return evidenceDomains.filter((domain) => events.some((event) => event.domain === domain));
}

export function canonicalAskedDomains(domains: readonly EvidenceDomain[]): readonly EvidenceDomain[] {
  return evidenceDomains.filter((domain) => domains.includes(domain));
}

function progress(
  stored: StoredRectificationCase,
  phase: JourneyProgress["phase"],
  adaptiveRound: number,
): JourneyProgress {
  const events = stored.lifeEvents ?? [];
  return {
    phase,
    baselineDomainCount: coveredDomains(events).length,
    confirmedEvidenceCount: events.length,
    adaptiveRound,
    maxAdaptiveRounds: 3,
  };
}

function plannedTurn(input: PlannedTurnInput): JourneyTurnState | null {
  if (!input.stored.questionnaire) return null;
  const plannerRound = input.phase === "adaptive"
    ? Math.max(0, input.adaptiveRound - 1)
    : input.adaptiveRound;
  const question = planEvidenceQuestion({
    phase: input.phase,
    samples: input.stored.questionnaire.samples,
    askedDomains: input.askedDomains,
    coveredDomains: coveredDomains(input.stored.lifeEvents ?? []),
    adaptiveRound: plannerRound,
  });
  if (!question) return null;
  const nextAction: NextAction = input.phase === "baseline"
    ? { kind: "ask_baseline_evidence", question }
    : { kind: "ask_adaptive_evidence", question };
  return {
    turnVersion: input.turnVersion,
    nextAction,
    progress: progress(input.stored, input.phase, input.adaptiveRound),
    permissions: deriveJourneyPermissions(input.stored.candidateResult ?? null, null),
    evidenceDraft: null,
  };
}

function terminalTurn(
  stored: StoredRectificationCase,
  turnVersion: number,
  adaptiveRound: number,
): JourneyTurnState {
  const resultId = stored.candidateResult?.confidence === "low"
    ? stored.candidateResult.resultId
    : null;
  return {
    turnVersion,
    nextAction: { kind: "present_low_result", resultId },
    progress: progress(stored, "result", adaptiveRound),
    permissions: { canConfirmCandidate: false },
    evidenceDraft: null,
  };
}

export function questionFromTurn(turn: JourneyTurnState): QuestionSpec | null {
  return turn.nextAction.kind === "ask_baseline_evidence"
    || turn.nextAction.kind === "ask_adaptive_evidence"
    ? turn.nextAction.question
    : null;
}

export function draftMatchesQuestion(draft: EvidenceDraft, adaptiveRound: number): boolean {
  const phase = adaptiveRound > 0 ? "adaptive" : "baseline";
  const round = adaptiveRound > 0 ? adaptiveRound : 1;
  return draft.questionId === `${phase}_${draft.domain}_${round}`;
}

export function reviewDraftTransition(input: {
  readonly stored: StoredRectificationCase;
  readonly current: JourneyTurnState;
  readonly question: EvidenceQuestionIdentity;
  readonly draft: EvidenceDraft;
  readonly nextVersion: number;
}): StoredRectificationCase {
  const adaptiveRound = input.question.phase === "adaptive"
    ? Math.max(1, input.current.progress.adaptiveRound)
    : input.current.progress.adaptiveRound;
  return {
    ...input.stored,
    snapshot: {
      ...input.stored.snapshot,
      state: "rectifying",
      assistantIntent: "collect_dated_life_events",
      input: "life_events",
      route: "rectification",
      canApply: false,
      activeTime: null,
    },
    turnState: {
      turnVersion: input.nextVersion,
      nextAction: { kind: "review_evidence_draft", draftId: input.draft.draftId },
      progress: { ...input.current.progress, phase: "review", adaptiveRound },
      permissions: deriveJourneyPermissions(input.stored.candidateResult ?? null, null),
      evidenceDraft: input.draft,
    },
    evidenceDraft: input.draft,
    persistedProgress: {
      adaptiveRound,
      askedDomains: input.stored.persistedProgress?.askedDomains ?? [],
    },
  };
}

export function confirmDraftTransition(input: {
  readonly stored: StoredRectificationCase;
  readonly current: JourneyTurnState;
  readonly event: LifeEvent;
  readonly scoreJobId: string;
  readonly nextVersion: number;
}): StoredRectificationCase {
  const events = [...(input.stored.lifeEvents ?? []), input.event];
  const withEvidence = { ...input.stored, lifeEvents: events };
  const domains = coveredDomains(events);
  const askedDomains = canonicalAskedDomains([
    ...(input.stored.persistedProgress?.askedDomains ?? []),
    input.event.domain,
  ]);
  const adaptiveRound = input.current.progress.adaptiveRound;
  const readyToScore = adaptiveRound > 0 || (events.length >= 3 && domains.length >= 2);
  if (readyToScore) {
    return {
      ...withEvidence,
      snapshot: {
        ...questionJourneySnapshot(withEvidence),
        assistantIntent: "collect_dated_life_events",
        input: "life_events",
      },
      turnState: {
        turnVersion: input.nextVersion,
        nextAction: { kind: "score_pending", jobId: input.scoreJobId },
        progress: progress(withEvidence, "scoring", adaptiveRound),
        permissions: { canConfirmCandidate: false },
        evidenceDraft: null,
      },
      evidenceDraft: null,
      persistedProgress: { adaptiveRound, askedDomains },
    };
  }
  const next = plannedTurn({
    stored: withEvidence,
    phase: "baseline",
    askedDomains,
    adaptiveRound,
    turnVersion: input.nextVersion,
  });
  return {
    ...withEvidence,
    snapshot: next ? questionJourneySnapshot(withEvidence) : terminalJourneySnapshot(withEvidence),
    turnState: next ?? terminalTurn(withEvidence, input.nextVersion, adaptiveRound),
    evidenceDraft: null,
    persistedProgress: { adaptiveRound, askedDomains },
  };
}

export function skipQuestionTransition(input: {
  readonly stored: StoredRectificationCase;
  readonly question: EvidenceQuestionIdentity;
  readonly nextVersion: number;
}): StoredRectificationCase {
  const currentRound = input.stored.turnState?.progress.adaptiveRound
    ?? input.stored.persistedProgress?.adaptiveRound
    ?? 0;
  const askedDomains = canonicalAskedDomains([
    ...(input.stored.persistedProgress?.askedDomains ?? []),
    input.question.domain,
  ]);
  const displayedRound = input.question.phase === "adaptive" ? Math.max(1, currentRound) : currentRound;
  const nextRound = input.question.phase === "adaptive" ? Math.min(3, displayedRound + 1) : displayedRound;
  const next = input.question.phase === "adaptive" && displayedRound >= 3
    ? null
    : plannedTurn({
      stored: input.stored,
      phase: input.question.phase,
      askedDomains,
      adaptiveRound: nextRound,
      turnVersion: input.nextVersion,
    });
  return {
    ...input.stored,
    snapshot: next ? questionJourneySnapshot(input.stored) : terminalJourneySnapshot(input.stored),
    turnState: next ?? terminalTurn(input.stored, input.nextVersion, displayedRound),
    evidenceDraft: null,
    persistedProgress: { adaptiveRound: next ? nextRound : displayedRound, askedDomains },
  };
}

export function pauseTransition(
  stored: StoredRectificationCase,
  current: JourneyTurnState,
  nextVersion: number,
): StoredRectificationCase {
  return {
    ...stored,
    turnState: {
      ...current,
      turnVersion: nextVersion,
      nextAction: { kind: "paused" },
      progress: { ...current.progress, phase: "paused" },
    },
  };
}

export function finishTransition(
  stored: StoredRectificationCase,
  adaptiveRound: number,
  nextVersion: number,
): StoredRectificationCase {
  const candidateResult = stored.candidateResult?.confidence === "low" ? stored.candidateResult : null;
  const terminalStored = { ...stored, candidateResult };
  return {
    ...terminalStored,
    snapshot: terminalJourneySnapshot(terminalStored),
    turnState: terminalTurn(terminalStored, nextVersion, adaptiveRound),
    evidenceDraft: null,
  };
}
