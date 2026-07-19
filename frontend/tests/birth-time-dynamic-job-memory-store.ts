import type {
  BirthTimeJourneyStore,
  DynamicStoredRectificationCase,
} from "../src/lib/birth-time-journey-service.ts";
import type { DynamicScoringJobSpec } from "../src/lib/birth-time-scoring-job.ts";
import { BirthTimeScoringJobError, scoringJobDurationMs, scoringProcessingLeaseMs } from "../src/lib/birth-time-scoring-job.ts";
import { StaleJourneyTurnError } from "../src/lib/birth-time-journey-turn-persistence.ts";

type DynamicMemoryJob = DynamicScoringJobSpec & {
  readonly caseId: string;
  readonly userId: string;
  readonly status: "pending" | "processing" | "completed" | "failed";
  readonly updatedAt: string;
};

export function dynamicJobStore(
  base: BirthTimeJourneyStore,
  read: () => DynamicStoredRectificationCase | null,
) {
  const jobs = new Map<string, DynamicMemoryJob>();
  const store: BirthTimeJourneyStore = {
    ...base,
    async createDynamicScoringJob(value, expectedVersion, actionId, _questionId, spec) {
      const current = read();
      if (!current) throw new BirthTimeScoringJobError("unavailable");
      const receipt = actionId.toLowerCase();
      if (current.processedActionIds.includes(receipt)) return current;
      if (current.turnVersion !== expectedVersion) {
        throw new StaleJourneyTurnError(value.id, expectedVersion, current.turnVersion);
      }
      jobs.set(spec.jobId, {
        ...spec,
        caseId: value.id,
        userId: value.userId,
        status: "pending",
        updatedAt: new Date(Date.parse(spec.expiresAt) - scoringJobDurationMs).toISOString(),
      });
      return base.saveDynamicTurn(value, expectedVersion, receipt);
    },
    async claimDynamicScoringJob(identity) {
      const job = jobs.get(identity.jobId);
      if (!job || job.caseId !== identity.caseId || job.userId !== identity.userId
        || job.evidenceFingerprint !== identity.evidenceFingerprint) {
        throw new BirthTimeScoringJobError("unavailable");
      }
      if (job.algorithmVersion !== identity.algorithmVersion) {
        throw new BirthTimeScoringJobError("algorithm_mismatch");
      }
      if (job.status === "completed") {
        return { kind: "completed", algorithmVersion: job.algorithmVersion };
      }
      if (job.status === "processing") {
        const leaseEnds = Date.parse(job.updatedAt) + scoringProcessingLeaseMs;
        if (Date.parse(identity.now) < leaseEnds) {
          return { kind: "processing", algorithmVersion: job.algorithmVersion };
        }
      }
      jobs.set(job.jobId, { ...job, status: "processing", updatedAt: identity.now });
      return { kind: "claimed", algorithmVersion: job.algorithmVersion };
    },
    async completeDynamicScoringJob(value, command) {
      const job = jobs.get(command.jobId);
      if (!job || job.status !== "processing") {
        throw new BirthTimeScoringJobError("invalid_turn");
      }
      const saved = await base.completeDynamicScoringJob(value, command);
      jobs.set(job.jobId, { ...job, status: "completed" });
      return saved;
    },
    async failDynamicScoringJob(value, command) {
      const job = jobs.get(command.jobId);
      if (!job || job.status !== "processing") {
        throw new BirthTimeScoringJobError("invalid_turn");
      }
      const saved = await base.failDynamicScoringJob(value, command);
      jobs.set(job.jobId, { ...job, status: "failed" });
      return saved;
    },
  };
  return {
    store,
    count: () => jobs.size,
  };
}
