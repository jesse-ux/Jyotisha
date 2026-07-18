import { createHash } from "node:crypto";
import { z } from "zod";
import type { LifeEvent } from "./birth-time-evidence.ts";

export const birthTimeScoringAlgorithmVersion = "birth-time-event-scoring-v1" as const;
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
