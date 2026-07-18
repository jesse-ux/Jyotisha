import type { CandidateResult, LifeEvent } from "./birth-time-evidence.ts";
import { evidenceDomains, planEvidenceQuestion, type CandidateVargaSample, type EvidenceDomain, type QuestionSpec } from "./birth-time-question-planner.ts";
import type { JourneySnapshot } from "./birth-time-journey.ts";
import type {
  EvidenceDraft,
  JourneyPermissions,
  JourneyProgress,
  JourneyTurnState,
  NextAction,
} from "./birth-time-journey-turn-protocol.ts";

export {
  evidenceDraftSchema,
  journeyPermissionsSchema,
  journeyProgressSchema,
  journeyTurnStateSchema,
  nextActionSchema,
  questionSpecSchema,
} from "./birth-time-journey-turn-protocol.ts";
export type {
  EvidenceDraft,
  JourneyPermissions,
  JourneyProgress,
  JourneyTurnState,
  NextAction,
} from "./birth-time-journey-turn-protocol.ts";

export type DeriveNextActionInput = {
  readonly progress: JourneyProgress;
  readonly candidateResult?: CandidateResult | null;
  readonly nextQuestion?: QuestionSpec | null;
  readonly confirmedTime?: string | null;
  readonly evidenceDraft?: EvidenceDraft | null;
  readonly scoringJobId?: string | null;
  readonly scoringRetry?: boolean;
};

export class JourneyTurnInvariantError extends Error {
  readonly name = "JourneyTurnInvariantError";
}

function assertNever(value: never): never {
  throw new JourneyTurnInvariantError(`Unexpected journey turn variant: ${String(value)}`);
}

function hasBaselineEvidence(progress: JourneyProgress): boolean {
  return progress.confirmedEvidenceCount >= 3 && progress.baselineDomainCount >= 2;
}

function requireQuestion(question: QuestionSpec | null, phase: QuestionSpec["phase"]): QuestionSpec {
  if (question?.phase === phase) return question;
  throw new JourneyTurnInvariantError(`A ${phase} question is required for this journey turn`);
}

function resultAction(input: DeriveNextActionInput): NextAction | null {
  const result = input.candidateResult ?? null;
  if (!result) return null;
  const confirmedTime = input.confirmedTime ?? null;
  if (confirmedTime !== null) {
    switch (result.confidence) {
      case "high":
        if (result.winningSegment?.representativeTime === confirmedTime) {
          return { kind: "ready", activeTime: confirmedTime };
        }
        throw new JourneyTurnInvariantError("A confirmed time must match the high-confidence candidate");
      case "low":
      case "medium":
        throw new JourneyTurnInvariantError("Only a high-confidence candidate can be confirmed");
      default:
        return assertNever(result.confidence);
    }
  }
  switch (result.confidence) {
    case "low":
      return input.progress.adaptiveRound < input.progress.maxAdaptiveRounds && input.nextQuestion
        ? { kind: "ask_adaptive_evidence", question: requireQuestion(input.nextQuestion, "adaptive") }
        : { kind: "present_low_result", resultId: result.resultId };
    case "medium":
      return { kind: "present_medium_result", resultId: result.resultId };
    case "high":
      return { kind: "request_candidate_confirmation", resultId: result.resultId };
    default:
      return assertNever(result.confidence);
  }
}

export function deriveNextAction(input: DeriveNextActionInput): NextAction {
  const fromResult = resultAction(input);
  if (fromResult) return fromResult;
  switch (input.progress.phase) {
    case "baseline":
      return !hasBaselineEvidence(input.progress)
        ? { kind: "ask_baseline_evidence", question: requireQuestion(input.nextQuestion ?? null, "baseline") }
        : input.evidenceDraft
          ? { kind: "review_evidence_draft", draftId: input.evidenceDraft.draftId }
          : { kind: "present_low_result", resultId: null };
    case "adaptive":
      return input.progress.adaptiveRound < input.progress.maxAdaptiveRounds
        ? { kind: "ask_adaptive_evidence", question: requireQuestion(input.nextQuestion ?? null, "adaptive") }
        : { kind: "present_low_result", resultId: null };
    case "review":
      if (!input.evidenceDraft) throw new JourneyTurnInvariantError("An evidence draft is required for review");
      return { kind: "review_evidence_draft", draftId: input.evidenceDraft.draftId };
    case "scoring":
      if (!input.scoringJobId) throw new JourneyTurnInvariantError("A scoring job is required while scoring");
      return input.scoringRetry
        ? { kind: "retry_scoring", jobId: input.scoringJobId }
        : { kind: "score_pending", jobId: input.scoringJobId };
    case "result":
      return { kind: "present_low_result", resultId: null };
    case "ready":
      if (input.confirmedTime === null || input.confirmedTime === undefined) {
        throw new JourneyTurnInvariantError("A confirmed time is required when ready");
      }
      return { kind: "ready", activeTime: input.confirmedTime };
    case "paused":
      return { kind: "paused" };
    default:
      return assertNever(input.progress.phase);
  }
}

export function deriveJourneyPermissions(
  candidateResult: CandidateResult | null,
  confirmedTime: string | null,
): JourneyPermissions {
  return {
    canConfirmCandidate: candidateResult?.confidence === "high"
      && candidateResult.winningSegment !== null
      && confirmedTime === null,
  };
}

export function createInitialJourneyTurn(
  question: QuestionSpec,
  turnVersion = 0,
): JourneyTurnState {
  const progress: JourneyProgress = {
    phase: "baseline",
    baselineDomainCount: 0,
    confirmedEvidenceCount: 0,
    adaptiveRound: 0,
    maxAdaptiveRounds: 3,
  };
  return {
    turnVersion,
    nextAction: deriveNextAction({
      progress,
      candidateResult: null,
      nextQuestion: question,
      confirmedTime: null,
      evidenceDraft: null,
      scoringJobId: null,
      scoringRetry: false,
    }),
    progress,
    permissions: deriveJourneyPermissions(null, null),
    evidenceDraft: null,
  };
}

export type JourneyTurnProjectionInput = {
  readonly turnVersion: number;
  readonly snapshot: JourneySnapshot;
  readonly questionnaire: { readonly samples: readonly CandidateVargaSample[] } | null;
  readonly persistedProgress?: {
    readonly adaptiveRound: number;
    readonly askedDomains: readonly EvidenceDomain[];
  } | null;
  readonly candidateResult: CandidateResult | null;
  readonly lifeEvents: readonly LifeEvent[];
};

function projectionPhase(input: JourneyTurnProjectionInput, progress: JourneyProgress): JourneyProgress["phase"] {
  if (input.snapshot.state === "ready") return "ready";
  if (input.candidateResult) {
    switch (input.candidateResult.confidence) {
      case "low":
        return "adaptive";
      case "medium":
      case "high":
        return "result";
      default:
        return assertNever(input.candidateResult.confidence);
    }
  }
  const acceptsEvidence = input.snapshot.input === "rectification_questions"
    || input.snapshot.input === "life_events";
  if (!input.questionnaire || input.snapshot.route !== "rectification" || !acceptsEvidence) {
    return "paused";
  }
  return hasBaselineEvidence(progress) ? "paused" : "baseline";
}

export function projectJourneyTurn(input: JourneyTurnProjectionInput): JourneyTurnState {
  const confirmedTime = input.snapshot.state === "ready" ? input.snapshot.activeTime : null;
  const coveredDomains = [...new Set(input.lifeEvents.map((event) => event.domain))];
  const adaptiveRound = input.persistedProgress?.adaptiveRound ?? 0;
  const askedDomains = evidenceDomains.filter((domain) => coveredDomains.includes(domain) || input.persistedProgress?.askedDomains.includes(domain) === true);
  const displayedAdaptiveRound = input.candidateResult?.confidence === "low"
    && adaptiveRound < 3
    ? adaptiveRound + 1
    : adaptiveRound;
  const progress: JourneyProgress = {
    phase: "paused",
    baselineDomainCount: coveredDomains.length,
    confirmedEvidenceCount: input.lifeEvents.length,
    adaptiveRound: displayedAdaptiveRound,
    maxAdaptiveRounds: 3,
  };
  const phase = projectionPhase(input, progress);
  const projectedProgress = { ...progress, phase } satisfies JourneyProgress;
  const decisionProgress = input.candidateResult?.confidence === "low"
    ? { ...projectedProgress, adaptiveRound }
    : projectedProgress;
  const nextQuestion = phase === "baseline" || phase === "adaptive"
    ? planEvidenceQuestion({
      phase,
      samples: input.questionnaire?.samples ?? [],
      askedDomains,
      coveredDomains,
      adaptiveRound,
    })
    : null;
  return {
    turnVersion: input.turnVersion,
    nextAction: deriveNextAction({
      progress: decisionProgress,
      candidateResult: input.candidateResult,
      nextQuestion,
      confirmedTime,
      evidenceDraft: null,
    }),
    progress: projectedProgress,
    permissions: deriveJourneyPermissions(input.candidateResult, confirmedTime),
    evidenceDraft: null,
  };
}
