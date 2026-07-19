import { createHash } from "node:crypto";
import { z } from "zod";
import type { LifeEvent } from "./birth-time-evidence.ts";
import type { ServerChoiceEvidence } from "./birth-time-dynamic-choice-internal.ts";

export const birthTimeScoringAlgorithmVersion = "birth-time-event-scoring-v1" as const;
export const dynamicChoiceScoringAlgorithmVersion = "birth-time-choice-scoring-v2" as const;
export const scoringJobDurationMs = 15 * 60_000;
export const scoringProcessingLeaseMs = 60_000;

export const scoringJobStatusSchema = z.enum([
  "pending",
  "processing",
  "completed",
  "failed",
]);

export type ScoringJobStatus = z.infer<typeof scoringJobStatusSchema>;

export type ScoringJobSpec = {
  readonly jobId: string;
  readonly evidenceFingerprint: string;
  readonly algorithmVersion: typeof birthTimeScoringAlgorithmVersion;
  readonly expiresAt: string;
};

export type ScoringJobIdentity = {
  readonly userId: string;
  readonly caseId: string;
  readonly jobId: string;
  readonly evidenceFingerprint: string;
  readonly algorithmVersion: typeof birthTimeScoringAlgorithmVersion;
  readonly now: string;
};

export type DynamicScoringJobSpec = {
  readonly jobId: string;
  readonly evidenceFingerprint: string;
  readonly algorithmVersion: typeof dynamicChoiceScoringAlgorithmVersion;
  readonly expiresAt: string;
};

export type DynamicScoringJobIdentity = Omit<ScoringJobIdentity, "algorithmVersion"> & {
  readonly algorithmVersion: typeof dynamicChoiceScoringAlgorithmVersion;
};

export type ScoringJobClaim =
  | { readonly kind: "claimed"; readonly algorithmVersion: string }
  | { readonly kind: "processing"; readonly algorithmVersion: string }
  | { readonly kind: "completed"; readonly algorithmVersion: string };

export class BirthTimeScoringJobError extends Error {
  readonly name = "BirthTimeScoringJobError";
  readonly reason: "unavailable" | "invalid_turn" | "invalid_result" | "algorithm_mismatch";

  constructor(reason: "unavailable" | "invalid_turn" | "invalid_result" | "algorithm_mismatch") {
    super(`Birth-time scoring job ${reason}`);
    this.reason = reason;
  }
}

function canonicalEvidence(events: readonly LifeEvent[]): string {
  return JSON.stringify([...events]
    .sort((left, right) => left.id.localeCompare(right.id))
    .map((event) => ({
      id: event.id,
      domain: event.domain,
      precision: event.precision,
      date: event.date,
    })));
}

export function evidenceFingerprint(events: readonly LifeEvent[]): string {
  return createHash("sha256")
    .update(birthTimeScoringAlgorithmVersion)
    .update("\u0000")
    .update(canonicalEvidence(events))
    .digest("hex");
}

export function createScoringJobSpec(
  jobId: string,
  events: readonly LifeEvent[],
  now: Date,
): ScoringJobSpec {
  return {
    jobId,
    evidenceFingerprint: evidenceFingerprint(events),
    algorithmVersion: birthTimeScoringAlgorithmVersion,
    expiresAt: new Date(now.getTime() + scoringJobDurationMs).toISOString(),
  };
}

function canonicalChoiceEvidence(evidence: readonly ServerChoiceEvidence[]): string {
  return JSON.stringify([...evidence]
    .sort((left, right) => left.questionId.localeCompare(right.questionId))
    .map((item) => ({
      questionId: item.questionId,
      opportunityId: item.opportunityId,
      partitionId: item.partitionId,
      dimensionCode: item.dimensionCode,
      informationGain: item.informationGain,
      candidateScores: Object.fromEntries(
        Object.entries(item.candidateScores).sort(([left], [right]) => left.localeCompare(right)),
      ),
    })));
}

export function dynamicEvidenceFingerprint(
  evidence: readonly ServerChoiceEvidence[],
): string {
  return createHash("sha256")
    .update(dynamicChoiceScoringAlgorithmVersion)
    .update("\u0000")
    .update(canonicalChoiceEvidence(evidence))
    .digest("hex");
}

export function createDynamicScoringJobSpec(
  jobId: string,
  evidence: readonly ServerChoiceEvidence[],
  now: Date,
): DynamicScoringJobSpec {
  return {
    jobId,
    evidenceFingerprint: dynamicEvidenceFingerprint(evidence),
    algorithmVersion: dynamicChoiceScoringAlgorithmVersion,
    expiresAt: new Date(now.getTime() + scoringJobDurationMs).toISOString(),
  };
}
