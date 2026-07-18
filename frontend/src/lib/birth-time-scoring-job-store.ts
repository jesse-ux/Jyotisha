import type { SupabaseClient } from "@supabase/supabase-js";
import { z } from "zod";
import { BirthTimeScoringJobError } from "./birth-time-scoring-job.ts";
import type {
  BirthTimeJourneyStore,
  StoredRectificationCase,
} from "./birth-time-journey-service.ts";
import { BirthTimeJourneyStoreError } from "./birth-time-journey-turn-persistence.ts";

const claimSchema = z.object({
  claim_state: z.enum(["claimed", "processing", "completed"]),
  algorithm_version: z.string().trim().min(1),
}).strict().readonly();

type ScoringJobFailureReason = BirthTimeScoringJobError["reason"];

const p0001ScoringErrors: Readonly<Record<string, ScoringJobFailureReason>> = {
  birth_time_scoring_algorithm_mismatch: "algorithm_mismatch",
  birth_time_scoring_result_inconsistent: "algorithm_mismatch",
  birth_time_scoring_turn_invalid: "invalid_turn",
  birth_time_scoring_turn_stale: "invalid_turn",
  birth_time_scoring_job_not_processing: "invalid_turn",
  birth_time_scoring_job_not_found: "unavailable",
  birth_time_scoring_fingerprint_mismatch: "unavailable",
  birth_time_scoring_job_expired: "unavailable",
};

const scoringJobUniqueConstraint =
  "birth_time_rectification_scoring_jobs_case_id_evidence_fingerprint_algorithm_version_key";

export function mapScoringRpcError(message: string, code?: string): Error {
  const p0001Reason = code === "P0001" ? p0001ScoringErrors[message] : undefined;
  if (p0001Reason) return new BirthTimeScoringJobError(p0001Reason);
  if (code === "23505" && message.includes(scoringJobUniqueConstraint)) {
    return new BirthTimeScoringJobError("invalid_turn");
  }
  return new BirthTimeJourneyStoreError("update_case");
}

type ScoringStoreMethods = Pick<BirthTimeJourneyStore,
  | "createScoringJob"
  | "claimScoringJob"
  | "completeScoringJob"
  | "failScoringJob"
>;

async function requireReloaded(
  loadCase: (userId: string, caseId: string) => Promise<StoredRectificationCase | null>,
  userId: string,
  caseId: string,
): Promise<StoredRectificationCase> {
  const stored = await loadCase(userId, caseId);
  if (!stored) throw new BirthTimeJourneyStoreError("load_case");
  return stored;
}

export function createSupabaseScoringJobStore(
  supabase: SupabaseClient,
  loadCase: (userId: string, caseId: string) => Promise<StoredRectificationCase | null>,
): ScoringStoreMethods {
  return {
    async createScoringJob(value, expectedVersion, actionId, job) {
      if (!value.turnState) throw new BirthTimeJourneyStoreError("update_case");
      const { error } = await supabase.rpc("create_birth_time_scoring_job", {
        p_user_id: value.userId,
        p_case_id: value.id,
        p_job_id: job.jobId,
        p_expected_version: expectedVersion,
        p_action_id: actionId,
        p_evidence_fingerprint: job.evidenceFingerprint,
        p_algorithm_version: job.algorithmVersion,
        p_expires_at: job.expiresAt,
        p_snapshot: value.snapshot,
        p_turn_state: value.turnState,
        p_life_events: value.lifeEvents ?? [],
        p_adaptive_round: value.persistedProgress?.adaptiveRound ?? 0,
        p_asked_domains: value.persistedProgress?.askedDomains ?? [],
      });
      if (error) {
        const current = await loadCase(value.userId, value.id);
        if (current?.processedActionIds?.includes(actionId.toLowerCase())) return current;
        throw mapScoringRpcError(error.message, error.code);
      }
      return requireReloaded(loadCase, value.userId, value.id);
    },

    async claimScoringJob(identity) {
      const { data, error } = await supabase
        .rpc("claim_birth_time_scoring_job", {
          p_user_id: identity.userId,
          p_case_id: identity.caseId,
          p_job_id: identity.jobId,
          p_evidence_fingerprint: identity.evidenceFingerprint,
          p_algorithm_version: identity.algorithmVersion,
          p_now: identity.now,
        })
        .single();
      if (error) throw mapScoringRpcError(error.message, error.code);
      const parsed = claimSchema.safeParse(data);
      if (!parsed.success) throw new BirthTimeJourneyStoreError("load_case");
      return {
        kind: parsed.data.claim_state,
        algorithmVersion: parsed.data.algorithm_version,
      };
    },

    async completeScoringJob(value, expectedVersion, jobId, fingerprint) {
      if (!value.turnState || !value.candidateResult) {
        throw new BirthTimeJourneyStoreError("update_case");
      }
      const winner = value.candidateResult.winningSegment;
      const { error } = await supabase.rpc("complete_birth_time_scoring_job", {
        p_user_id: value.userId,
        p_case_id: value.id,
        p_job_id: jobId,
        p_expected_version: expectedVersion,
        p_evidence_fingerprint: fingerprint,
        p_snapshot: value.snapshot,
        p_turn_state: value.turnState,
        p_candidate_result: value.candidateResult,
        p_candidate_start: winner?.startTime ?? null,
        p_candidate_end: winner?.endTime ?? null,
        p_adaptive_round: value.persistedProgress?.adaptiveRound ?? 0,
        p_asked_domains: value.persistedProgress?.askedDomains ?? [],
      });
      if (error) throw mapScoringRpcError(error.message, error.code);
      return requireReloaded(loadCase, value.userId, value.id);
    },

    async failScoringJob(value, expectedVersion, jobId, fingerprint, failureCode) {
      if (!value.turnState) throw new BirthTimeJourneyStoreError("update_case");
      const { error } = await supabase.rpc("fail_birth_time_scoring_job", {
        p_user_id: value.userId,
        p_case_id: value.id,
        p_job_id: jobId,
        p_expected_version: expectedVersion,
        p_evidence_fingerprint: fingerprint,
        p_failure_code: failureCode,
        p_turn_state: value.turnState,
      });
      if (error) throw mapScoringRpcError(error.message, error.code);
      return requireReloaded(loadCase, value.userId, value.id);
    },
  };
}
