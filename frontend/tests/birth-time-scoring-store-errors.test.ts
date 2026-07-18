import assert from "node:assert/strict";
import test from "node:test";
import { BirthTimeScoringJobError } from "../src/lib/birth-time-scoring-job.ts";
import { mapScoringRpcError } from "../src/lib/birth-time-scoring-job-store.ts";
import { BirthTimeJourneyStoreError } from "../src/lib/birth-time-journey-turn-persistence.ts";

const domainErrors = [
  ["birth_time_scoring_algorithm_mismatch", "algorithm_mismatch"],
  ["birth_time_scoring_result_inconsistent", "algorithm_mismatch"],
  ["birth_time_scoring_turn_invalid", "invalid_turn"],
  ["birth_time_scoring_turn_stale", "invalid_turn"],
  ["birth_time_scoring_job_not_processing", "invalid_turn"],
  ["birth_time_scoring_job_not_found", "unavailable"],
  ["birth_time_scoring_fingerprint_mismatch", "unavailable"],
  ["birth_time_scoring_job_expired", "unavailable"],
] as const;

test("allowlisted P0001 scoring conflicts keep their exact domain semantics", () => {
  for (const [message, reason] of domainErrors) {
    const mapped = mapScoringRpcError(message, "P0001");

    assert.ok(mapped instanceof BirthTimeScoringJobError, message);
    assert.equal(mapped.reason, reason, message);
  }
});

test("the scoring-job composite unique violation is a domain conflict", () => {
  const mapped = mapScoringRpcError(
    "duplicate key value violates unique constraint \"birth_time_rectification_scoring_jobs_case_id_evidence_fingerprint_algorithm_version_key\"",
    "23505",
  );

  assert.ok(mapped instanceof BirthTimeScoringJobError);
  assert.equal(mapped.reason, "invalid_turn");
});

test("RPC lookup and database failures cannot impersonate domain conflicts", () => {
  const failures = [
    ["Could not find public.claim_birth_time_scoring_job(uuid)", "PGRST202"],
    ["function public.claim_birth_time_scoring_job(uuid) does not exist", "42883"],
    ["birth_time_scoring_unrecognized_failure", "P0001"],
    ["birth_time_scoring_algorithm_mismatch", "08006"],
    ["connection reset while calling birth_time_scoring_job", undefined],
    ["duplicate key", "23505"],
  ] as const;

  for (const [message, code] of failures) {
    const mapped = mapScoringRpcError(message, code);
    assert.equal(mapped instanceof BirthTimeJourneyStoreError, true, `${code}: ${message}`);
  }
});
