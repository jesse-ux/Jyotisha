import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const migration = readFileSync(new URL(
  "../supabase/migrations/20260728020000_rectification_agent_v5.sql",
  import.meta.url,
), "utf8");

test("V5 migration freezes protocol and deployment mode per case", () => {
  assert.match(migration, /protocol in \('rectification-evidence-v4', 'rectification-evidence-v5'\)/);
  assert.match(migration, /p_deployment_mode text/);
  assert.match(migration, /deployment_mode in \('v4_legacy', 'v5_shadow', 'v5_agent'\)/);
  assert.match(migration, /An in-flight Case keeps the deployment mode and protocol it was created with/);
  assert.match(migration, /v_protocol := case when p_deployment_mode = 'v4_legacy'/);
  assert.match(migration, /if found and v_case\.calculation_spec_hash = p_calculation_spec_hash/);
});

test("V5 migration owns all durable artifacts and indexes", () => {
  for (const table of [
    "birth_time_rectification_candidate_feature_snapshots",
    "birth_time_rectification_diagnostics",
    "birth_time_rectification_agent_runs",
    "birth_time_rectification_public_messages",
    "birth_time_rectification_pending_evidence",
  ]) assert.match(migration, new RegExp(`create table if not exists public\\.${table}`));
  for (const indexFragment of [
    "feature_snapshots_case_created_idx", "feature_snapshots_user_created_idx",
    "diagnostics_case_created_idx", "diagnostics_user_created_idx", "diagnostics_snapshot_idx",
    "agent_runs_case_created_idx", "agent_runs_user_created_idx", "public_messages_case_created_idx",
  ]) assert.match(migration, new RegExp(indexFragment));
  assert.match(migration, /birth_time_rectification_v5_feature_snapshot_fk[\s\S]*candidate_feature_snapshots/);
  assert.match(migration, /birth_time_rectification_v5_latest_diagnostics_fk[\s\S]*birth_time_rectification_diagnostics/);
  assert.match(migration, /alter table public\.birth_time_rectification_agent_runs[\s\S]*add column if not exists deployment_mode/);
  assert.match(migration, /alter column deployment_mode set not null/);
  assert.match(migration, /birth_time_rectification_v5_agent_runs_tool_count_check/);
  assert.match(migration, /birth_time_rectification_v5_agent_runs_token_count_check/);
  assert.match(migration, /birth_time_rectification_pending_evidence_target_event_idx/);
  assert.match(migration, /birth_time_rectification_v5_pending_resolution_check/);
});

test("V5 migration replaces every V4-only worker and evidence constraint", () => {
  assert.match(migration, /birth_time_rectification_v5_jobs_phase_check[\s\S]*'reasoning', 'rendering'/);
  assert.match(migration, /birth_time_rectification_v5_candidate_snapshots_algorithm_check[\s\S]*rectification-v4-range-scoring-1[\s\S]*rectification-v5-matrix-scoring-1/);
  assert.match(migration, /birth_time_rectification_v5_event_revisions_scoreability_check[\s\S]*'pending_review', 'unsupported'/);
  assert.match(migration, /birth_time_rect_v5_event_revision_domain_score_check[\s\S]*scoreability <> 'scoreable'/);
  assert.match(migration, /birth_time_rect_v5_event_revision_relationship_kind_check[\s\S]*'relationship_change'/);
});

test("V5 completion is lease-bound, hash-bound, ownership-bound and replay-safe", () => {
  for (const fragment of [
    "rectification_v4_job_lease_lost",
    "stale_rectification_v4_job",
    "rectification_v5_snapshot_mismatch",
    "rectification_v5_feature_snapshot_mismatch",
    "rectification_v5_diagnostics_mismatch",
    "invalid_rectification_v5_agent_run",
    "rectification_v5_replay_payload_mismatch",
    "rectification_v5_pending_target_event_mismatch",
    "rectification_v5_pending_resolved_event_mismatch",
    "rectification_v5_artifact_set_incomplete",
    "exact_minute_confirmation_forbidden",
  ]) assert.match(migration, new RegExp(fragment));
  assert.match(migration, /if v_job\.status = 'completed'[\s\S]*return v_case\.id/);
  assert.match(migration, /jsonb_array_length\(p_agent_run->'toolCalls'\) > 8/);
  assert.match(migration, /p_agent_run->>'deploymentMode' is distinct from v_case\.deployment_mode/);
  assert.match(migration, /p_completion_payload_hash text/);
  assert.match(migration, /v_job\.completion_payload_hash is distinct from p_completion_payload_hash/);
  assert.match(migration, /completion_payload_hash = p_completion_payload_hash/);
});

test("V5 inserts use explicit columns and never mutate the profile birth minute", () => {
  for (const table of [
    "birth_time_rectification_v4_events",
    "birth_time_rectification_v4_event_revisions",
    "birth_time_rectification_v4_candidate_snapshots",
    "birth_time_rectification_candidate_feature_snapshots",
    "birth_time_rectification_diagnostics",
    "birth_time_rectification_agent_runs",
    "birth_time_rectification_public_messages",
  ]) assert.match(migration, new RegExp(`insert into public\\.${table}\\s*\\(`));
  assert.doesNotMatch(migration, /profiles\.active_birth_time|update\s+public\.profiles/i);
});
