import { completeScoreTransition } from "./birth-time-journey-score-transition.ts";
import { assertNotDynamicJourneyMutation } from "./birth-time-evidence-service.ts";
import { currentJourneyTurn, storedJourneyResponse } from "./birth-time-journey-response.ts";
import {
  birthTimeScoringAlgorithmVersion,
  BirthTimeScoringJobError,
  evidenceFingerprint,
} from "./birth-time-scoring-job.ts";
import type {
  BirthTimeJourneyPorts,
  LegacyStoredRectificationCase as StoredRectificationCase,
} from "./birth-time-journey-service.ts";
import type { CandidateResult } from "./birth-time-evidence.ts";

function requireMatchingEvidenceCounts(
  stored: StoredRectificationCase,
  candidate: CandidateResult,
): void {
  const events = stored.lifeEvents ?? [];
  const domainCount = new Set(events.map((event) => event.domain)).size;
  if (candidate.eventCount !== events.length || candidate.domainCount !== domainCount) {
    throw new BirthTimeScoringJobError("invalid_result");
  }
}

function retryTransition(
  stored: StoredRectificationCase,
  jobId: string,
): StoredRectificationCase {
  const current = currentJourneyTurn(stored);
  if (
    (current.nextAction.kind !== "score_pending"
      && current.nextAction.kind !== "retry_scoring")
    || current.nextAction.jobId !== jobId
  ) {
    throw new BirthTimeScoringJobError("invalid_turn");
  }
  return {
    ...stored,
    turnState: {
      ...current,
      turnVersion: current.turnVersion + 1,
      nextAction: { kind: "retry_scoring", jobId },
      progress: { ...current.progress, phase: "scoring" },
      permissions: { canConfirmCandidate: false },
    },
  };
}

function requireEventContext(stored: StoredRectificationCase) {
  const context = stored.eventContext;
  const { startTime, endTime } = stored.snapshot.reportedRange;
  if (!context || !startTime || !endTime) {
    throw new BirthTimeScoringJobError("invalid_turn");
  }
  return { ...context, startTime, endTime, events: stored.lifeEvents ?? [] };
}

export function createBirthTimeScoringService(ports: BirthTimeJourneyPorts) {
  return {
    async pollScoringJob(userId: string, caseId: string, jobId: string) {
      const stored = await ports.store.loadCase(userId, caseId);
      if (!stored) throw new BirthTimeScoringJobError("unavailable");
      assertNotDynamicJourneyMutation(stored);
      const fingerprint = evidenceFingerprint(stored.lifeEvents ?? []);
      const claim = await ports.store.claimScoringJob({
        userId,
        caseId,
        jobId,
        evidenceFingerprint: fingerprint,
        algorithmVersion: birthTimeScoringAlgorithmVersion,
        now: (ports.now?.() ?? new Date()).toISOString(),
      });
      if (claim.kind === "processing") return storedJourneyResponse(stored);
      if (claim.kind === "completed") {
        const completed = await ports.store.loadCase(userId, caseId);
        if (!completed) throw new BirthTimeScoringJobError("unavailable");
        return storedJourneyResponse(completed);
      }
      if (claim.algorithmVersion !== birthTimeScoringAlgorithmVersion) {
        throw new BirthTimeScoringJobError("algorithm_mismatch");
      }
      let candidateResult: CandidateResult;
      try {
        candidateResult = await ports.engine.scoreEvents(requireEventContext(stored));
        if (candidateResult.algorithmVersion !== claim.algorithmVersion) {
          throw new BirthTimeScoringJobError("algorithm_mismatch");
        }
        requireMatchingEvidenceCounts(stored, candidateResult);
      } catch (error) {
        if (!(error instanceof Error)) throw error;
        const failed = retryTransition(stored, jobId);
        const saved = await ports.store.failScoringJob(
          failed,
          stored.turnVersion ?? 0,
          jobId,
          fingerprint,
          error instanceof BirthTimeScoringJobError
            ? error.reason
            : "engine_error",
        );
        return storedJourneyResponse(saved);
      }
      const completed = completeScoreTransition({
        stored,
        candidateResult,
        nextVersion: (stored.turnVersion ?? 0) + 1,
      });
      const saved = await ports.store.completeScoringJob(
        completed,
        stored.turnVersion ?? 0,
        jobId,
        fingerprint,
      );
      return storedJourneyResponse(saved);
    },
  };
}
