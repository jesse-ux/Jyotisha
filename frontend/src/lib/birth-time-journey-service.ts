import { assessBirthTime, withRectificationScoring, type BirthTimeAssessment, type JourneySnapshot, type RectificationScoring } from "./birth-time-journey.ts";
import { createJourneyTurnActions } from "./birth-time-journey-actions.ts";
import {
  assertLegacyJourneyMutation,
  createBirthTimeEvidenceActions,
} from "./birth-time-evidence-service.ts";
import type { CandidateResult, LifeEvent } from "./birth-time-evidence.ts";
import type { CandidateVargaSample } from "./birth-time-question-planner.ts";
import { projectJourneyResponse, storedJourneyResponse } from "./birth-time-journey-response.ts";
import type { JourneyTurnState } from "./birth-time-journey-turn.ts";
import type { PersistedJourneyTurn } from "./birth-time-journey-turn-persistence.ts";
import type { ScoringJobClaim, ScoringJobIdentity, ScoringJobSpec } from "./birth-time-scoring-job.ts";
import { createBirthTimeScoringService } from "./birth-time-scoring-service.ts";
import { scanAssessment } from "./birth-time-journey-assessment.ts";
import type { GuidedCandidateCommit } from "./birth-time-guided-candidate.ts";
import { createGuidedCandidateActions } from "./birth-time-guided-candidate.ts";
import { createGuidedDraftRevisionActions } from "./birth-time-guided-draft-revision.ts";

export type RectificationAnswer = "A" | "B" | "C" | "D";

export type RectificationQuestion = {
  readonly id: string;
  readonly prompt: string;
  readonly round?: number;
  readonly options?: readonly {
    readonly key: RectificationAnswer;
    readonly label: string;
  }[];
};

export type RectificationQuestionnaire = {
  readonly questions: readonly RectificationQuestion[];
  readonly samples: readonly (CandidateVargaSample & {
    readonly ascendantSign: string | null;
  })[];
  readonly raw: Readonly<Record<string, unknown>>;
};

export type RectificationScoringResult = RectificationScoring & {
  readonly nextRound: number | null;
  readonly nextRoundQuestions: readonly RectificationQuestion[];
  readonly raw: Readonly<Record<string, unknown>>;
};

export type JourneyScanInput = {
  readonly birthTime: string;
  readonly uncertaintyMinutes: number;
  readonly lat: number;
  readonly lon: number;
  readonly tz: number;
  readonly ayanamsa: "lahiri";
};

export type JourneyScoreInput = {
  readonly questionnaire: RectificationQuestionnaire;
  readonly answers: Readonly<Record<string, RectificationAnswer>>;
};

export type JourneyEventScoreInput = {
  readonly birthDate: string;
  readonly startTime: string;
  readonly endTime: string;
  readonly lat: number;
  readonly lon: number;
  readonly tz: number;
  readonly events: readonly LifeEvent[];
};

export interface BirthTimeJourneyEngine {
  scan(input: JourneyScanInput): Promise<{ readonly questionnaire: RectificationQuestionnaire }>;
  score(input: JourneyScoreInput): Promise<RectificationScoringResult>;
  scoreEvents(input: JourneyEventScoreInput): Promise<CandidateResult>;
}

export type PersistedJourneyAssessment = {
  readonly userId: string;
  readonly assessment: BirthTimeAssessment;
  readonly snapshot: JourneySnapshot;
  readonly questionnaire: RectificationQuestionnaire | null;
  readonly candidateScan: RectificationQuestionnaire | null;
};

export type StoredRectificationCase = {
  readonly id: string;
  readonly userId: string;
  readonly snapshot: JourneySnapshot;
  readonly questionnaire: RectificationQuestionnaire | null;
  readonly answers: Readonly<Record<string, RectificationAnswer>>;
  readonly scoring?: RectificationScoringResult;
  readonly eventContext?: {
    readonly birthDate: string;
    readonly lat: number;
    readonly lon: number;
    readonly tz: number;
  };
  readonly lifeEvents?: readonly LifeEvent[];
  readonly candidateResult?: CandidateResult | null;
} & Partial<PersistedJourneyTurn>;

export interface BirthTimeJourneyStore {
  saveAssessment(value: PersistedJourneyAssessment): Promise<string>;
  loadCase(userId: string, caseId: string): Promise<StoredRectificationCase | null>;
  saveScoring(value: StoredRectificationCase): Promise<void>;
  saveTurn(value: StoredRectificationCase, expectedVersion: number, actionId: string): Promise<StoredRectificationCase>;
  createScoringJob(value: StoredRectificationCase, expectedVersion: number, actionId: string, job: ScoringJobSpec): Promise<StoredRectificationCase>;
  claimScoringJob(identity: ScoringJobIdentity): Promise<ScoringJobClaim>;
  completeScoringJob(value: StoredRectificationCase, expectedVersion: number, jobId: string, evidenceFingerprint: string): Promise<StoredRectificationCase>;
  failScoringJob(value: StoredRectificationCase, expectedVersion: number, jobId: string, evidenceFingerprint: string, failureCode: string): Promise<StoredRectificationCase>;
  saveCandidateResult(value: StoredRectificationCase): Promise<void>;
  saveCandidate(value: StoredRectificationCase): Promise<void>;
  confirmCandidate(value: StoredRectificationCase): Promise<void>;
  commitGuidedCandidate(value: StoredRectificationCase, command: GuidedCandidateCommit): Promise<StoredRectificationCase>;
}

export type BirthTimeJourneyPorts = {
  readonly store: BirthTimeJourneyStore;
  readonly engine: BirthTimeJourneyEngine;
  readonly now?: () => Date;
};

export type JourneyResponseBase = {
  readonly caseId: string;
  readonly snapshot: JourneySnapshot;
  readonly questionnaire: RectificationQuestionnaire | null;
  readonly scoring: RectificationScoringResult | null;
  readonly answers: Readonly<Record<string, RectificationAnswer>>;
  readonly lifeEvents: readonly LifeEvent[];
  readonly candidateResult: CandidateResult | null;
};

export type VersionedJourneyResponse = JourneyResponseBase & JourneyTurnState;

export type LegacyJourneyResponse = JourneyResponseBase & { readonly turnVersion?: undefined; readonly nextAction?: undefined; readonly progress?: undefined; readonly permissions?: undefined; readonly evidenceDraft?: undefined; };

export type JourneyResponse = LegacyJourneyResponse | VersionedJourneyResponse;

export class RectificationCaseNotFoundError extends Error {
  readonly name = "RectificationCaseNotFoundError";
  readonly caseId: string;

  constructor(caseId: string) {
    super(`Rectification case ${caseId} was not found`);
    this.caseId = caseId;
  }
}

export class RectificationQuestionsUnavailableError extends Error { readonly name = "RectificationQuestionsUnavailableError"; }

export function createBirthTimeJourneyService(ports: BirthTimeJourneyPorts) {
  const evidenceActions = createBirthTimeEvidenceActions(ports);
  const turnActions = createJourneyTurnActions(ports);
  const scoringActions = createBirthTimeScoringService(ports);
  const guidedCandidates = createGuidedCandidateActions(ports);
  const draftRevisions = createGuidedDraftRevisionActions(ports, turnActions.proposeEvidenceDraft);
  return {
    async assess(userId: string, assessment: BirthTimeAssessment): Promise<VersionedJourneyResponse> {
      const scan = await scanAssessment(ports.engine, assessment);
      const snapshot = assessBirthTime(assessment, scan.stability);
      const persisted = {
        userId,
        assessment,
        snapshot,
        questionnaire: scan.questionnaire,
        candidateScan: scan.questionnaire,
      } satisfies PersistedJourneyAssessment;
      const caseId = await ports.store.saveAssessment(persisted);
      return projectJourneyResponse({
        caseId,
        snapshot,
        questionnaire: scan.questionnaire,
        scoring: null,
        answers: {},
        lifeEvents: [],
        candidateResult: null,
      }, 0);
    },

    async resume(userId: string, caseId: string): Promise<VersionedJourneyResponse> {
      const stored = await ports.store.loadCase(userId, caseId);
      if (!stored) throw new RectificationCaseNotFoundError(caseId);
      const completedLegacyQuestionnaire = stored.snapshot.input === "rectification_questions"
        && stored.scoring?.nextRound === null
        && stored.scoring.nextRoundQuestions.length === 0
        && stored.scoring.answeredCount > 0;
      const snapshot = completedLegacyQuestionnaire
        ? withRectificationScoring(stored.snapshot, stored.scoring)
        : stored.snapshot;
      const normalized = snapshot === stored.snapshot ? stored : { ...stored, snapshot };
      if (normalized !== stored) await ports.store.saveScoring(normalized);
      return storedJourneyResponse(normalized);
    },

    async answerQuestion(
      userId: string,
      caseId: string,
      questionId: string,
      answer: RectificationAnswer,
    ): Promise<VersionedJourneyResponse> {
      const stored = await ports.store.loadCase(userId, caseId);
      if (!stored) throw new RectificationCaseNotFoundError(caseId);
      assertLegacyJourneyMutation(stored);
      if (!stored.questionnaire) throw new RectificationQuestionsUnavailableError();
      const answers = { ...stored.answers, [questionId]: answer };
      const scoring = await ports.engine.score({ questionnaire: stored.questionnaire, answers });
      const snapshot = withRectificationScoring(stored.snapshot, scoring);
      const updated = { ...stored, answers, scoring, snapshot } satisfies StoredRectificationCase;
      await ports.store.saveScoring(updated);
      return projectJourneyResponse({
        caseId,
        snapshot,
        questionnaire: stored.questionnaire,
        scoring,
        answers,
        lifeEvents: stored.lifeEvents ?? [],
        candidateResult: stored.candidateResult ?? null,
      }, stored.turnVersion ?? 0, stored.persistedProgress);
    },
    async submitLifeEvents(...args: Parameters<typeof evidenceActions.submitLifeEvents>) { return projectJourneyResponse(await evidenceActions.submitLifeEvents(...args), 0); },
    async saveCandidate(...args: Parameters<typeof evidenceActions.saveCandidate>) { return projectJourneyResponse(await evidenceActions.saveCandidate(...args), 0); },
    async confirmCandidate(...args: Parameters<typeof evidenceActions.confirmCandidate>) { return projectJourneyResponse(await evidenceActions.confirmCandidate(...args), 0); },
    proposeEvidenceDraft: turnActions.proposeEvidenceDraft,
    confirmEvidenceDraft: turnActions.confirmEvidenceDraft,
    skipEvidenceQuestion: turnActions.skipEvidenceQuestion,
    pause: turnActions.pause,
    finishWithCurrentRange: turnActions.finishWithCurrentRange,
    reviseEvidenceDraft: draftRevisions.revise,
    saveGuidedCandidate: guidedCandidates.save,
    confirmGuidedCandidate: guidedCandidates.confirm,
    pollScoringJob: scoringActions.pollScoringJob,
  };
}
