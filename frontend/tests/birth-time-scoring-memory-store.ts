import {
  BirthTimeScoringJobError,
  scoringJobDurationMs,
  scoringProcessingLeaseMs,
} from "../src/lib/birth-time-scoring-job.ts";
import type { CandidateResult } from "../src/lib/birth-time-evidence.ts";
import type {
  BirthTimeJourneyStore,
  StoredRectificationCase,
} from "../src/lib/birth-time-journey-service.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";

type MemoryJob = {
  readonly id: string;
  readonly caseId: string;
  readonly userId: string;
  readonly evidenceFingerprint: string;
  readonly algorithmVersion: string;
  readonly expiresAt: string;
  readonly updatedAt: string;
  readonly status: "pending" | "processing" | "completed" | "failed";
  readonly result: CandidateResult | null;
};

type MemoryContext = {
  readonly read: () => StoredRectificationCase | null;
  readonly write: (value: StoredRectificationCase) => void;
  readonly committed: () => void;
};

type ScoringMethods = Pick<BirthTimeJourneyStore,
  | "createScoringJob"
  | "claimScoringJob"
  | "completeScoringJob"
  | "failScoringJob"
>;

class MissingMemoryCaseError extends Error {
  readonly name = "MissingMemoryCaseError";
}

function currentCase(context: MemoryContext): StoredRectificationCase {
  const current = context.read();
  if (!current) throw new MissingMemoryCaseError();
  return current;
}

export function createMemoryScoringJobs(context: MemoryContext) {
  const jobs = new Map<string, MemoryJob>();
  let createdCase: StoredRectificationCase | null = null;
  const methods: ScoringMethods = {
    async createScoringJob(value, expectedVersion, actionId, spec) {
      const current = currentCase(context);
      if (current.processedActionIds?.includes(actionId.toLowerCase())) return current;
      if (current.turnVersion !== expectedVersion) {
        throw new StaleJourneyTurnError(value.id, expectedVersion, current.turnVersion ?? 0);
      }
      if ([...jobs.values()].some((job) => job.caseId === value.id
        && job.evidenceFingerprint === spec.evidenceFingerprint
        && job.algorithmVersion === spec.algorithmVersion)) {
        throw new BirthTimeScoringJobError("unavailable");
      }
      const saved = {
        ...value,
        turnVersion: expectedVersion + 1,
        processedActionIds: [...(current.processedActionIds ?? []), actionId],
      } satisfies StoredRectificationCase;
      jobs.set(spec.jobId, {
        id: spec.jobId,
        caseId: value.id,
        userId: value.userId,
        evidenceFingerprint: spec.evidenceFingerprint,
        algorithmVersion: spec.algorithmVersion,
        expiresAt: spec.expiresAt,
        updatedAt: new Date(
          new Date(spec.expiresAt).getTime() - scoringJobDurationMs,
        ).toISOString(),
        status: "pending",
        result: null,
      });
      context.write(saved);
      context.committed();
      createdCase = saved;
      return saved;
    },

    async claimScoringJob(identity) {
      const job = jobs.get(identity.jobId);
      if (!job || job.userId !== identity.userId || job.caseId !== identity.caseId) {
        throw new BirthTimeScoringJobError("unavailable");
      }
      if (job.evidenceFingerprint !== identity.evidenceFingerprint) {
        throw new BirthTimeScoringJobError("unavailable");
      }
      if (job.algorithmVersion !== identity.algorithmVersion) {
        throw new BirthTimeScoringJobError("algorithm_mismatch");
      }
      const current = currentCase(context);
      if (job.status === "completed") {
        if (!completedStateMatches(current, job)) {
          throw new BirthTimeScoringJobError("algorithm_mismatch");
        }
        return { kind: "completed", algorithmVersion: job.algorithmVersion };
      }
      const action = current.turnState?.nextAction;
      if ((action?.kind !== "score_pending" && action?.kind !== "retry_scoring")
        || action.jobId !== job.id) {
        throw new BirthTimeScoringJobError("invalid_turn");
      }
      if (job.status === "processing"
        && new Date(job.updatedAt).getTime()
          > new Date(identity.now).getTime() - scoringProcessingLeaseMs) {
        return { kind: "processing", algorithmVersion: job.algorithmVersion };
      }
      jobs.set(job.id, {
        ...job,
        status: "processing",
        updatedAt: identity.now,
        expiresAt: new Date(
          new Date(identity.now).getTime() + scoringJobDurationMs,
        ).toISOString(),
      });
      return { kind: "claimed", algorithmVersion: job.algorithmVersion };
    },

    async completeScoringJob(value, expectedVersion, jobId, fingerprint) {
      const current = currentCase(context);
      const job = jobs.get(jobId);
      if (!job || job.status !== "processing" || job.evidenceFingerprint !== fingerprint) {
        throw new BirthTimeScoringJobError("unavailable");
      }
      if (current.turnVersion !== expectedVersion) {
        throw new StaleJourneyTurnError(value.id, expectedVersion, current.turnVersion ?? 0);
      }
      const saved = { ...value, turnVersion: expectedVersion + 1 } satisfies StoredRectificationCase;
      jobs.set(job.id, {
        ...job,
        status: "completed",
        result: value.candidateResult ?? null,
      });
      context.write(saved);
      return saved;
    },

    async failScoringJob(value, expectedVersion, jobId, fingerprint) {
      const current = currentCase(context);
      const job = jobs.get(jobId);
      if (!job || job.status !== "processing" || job.evidenceFingerprint !== fingerprint) {
        throw new BirthTimeScoringJobError("unavailable");
      }
      if (current.turnVersion !== expectedVersion) {
        throw new StaleJourneyTurnError(value.id, expectedVersion, current.turnVersion ?? 0);
      }
      const saved = { ...value, turnVersion: expectedVersion + 1 } satisfies StoredRectificationCase;
      jobs.set(job.id, { ...job, status: "failed" });
      context.write(saved);
      return saved;
    },
  };
  return {
    methods,
    status: (jobId: string) => jobs.get(jobId)?.status ?? null,
    count: () => jobs.size,
    setAlgorithm: (jobId: string, algorithmVersion: string) => {
      const job = jobs.get(jobId);
      if (!job) throw new BirthTimeScoringJobError("unavailable");
      jobs.set(jobId, { ...job, algorithmVersion });
    },
    createdCase: () => {
      if (!createdCase) throw new MissingMemoryCaseError();
      return createdCase;
    },
  };
}

function completedStateMatches(
  stored: StoredRectificationCase,
  job: MemoryJob,
): boolean {
  const result = stored.candidateResult ?? null;
  if (!job.result || !result || JSON.stringify(job.result) !== JSON.stringify(result)) return false;
  const turn = stored.turnState;
  if (!turn || result.algorithmVersion !== job.algorithmVersion
    || turn.turnVersion !== stored.turnVersion) return false;
  const action = turn.nextAction;
  switch (result.confidence) {
    case "low":
      return action.kind === "ask_adaptive_evidence"
        || action.kind === "review_evidence_draft"
        || action.kind === "paused"
        || (action.kind === "present_low_result" && action.resultId === result.resultId);
    case "medium":
      return (action.kind === "present_medium_result" || action.kind === "candidate_saved")
        && action.resultId === result.resultId;
    case "high":
      return (action.kind === "request_candidate_confirmation" && action.resultId === result.resultId)
        || action.kind === "ready";
    default: {
      const exhaustive: never = result.confidence;
      return exhaustive;
    }
  }
}
