import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

const sql = readFileSync(new URL("../supabase/migrations/20260726020000_birth_time_rectification_v4.sql", import.meta.url), "utf8");
const conversationalSql = readFileSync(new URL("../supabase/migrations/20260727010000_rectification_v4_conversational_turns.sql", import.meta.url), "utf8");
const regenerationSql = readFileSync(new URL("../supabase/migrations/20260729020000_rectification_v4_current_question_regeneration.sql", import.meta.url), "utf8");
const pendingResolutionSql = readFileSync(new URL("../supabase/migrations/20260730020000_pending_evidence_resolution.sql", import.meta.url), "utf8");

test("v4 migration creates canonical append-only storage and leased jobs", () => {
  for (const table of [
    "birth_time_rectification_v4_cases", "birth_time_rectification_v4_turns",
    "birth_time_rectification_v4_events", "birth_time_rectification_v4_event_revisions",
    "birth_time_rectification_v4_candidate_snapshots", "birth_time_rectification_v4_jobs",
  ]) assert.match(sql, new RegExp(`create table public\\.${table}`));
  assert.match(sql, /for update skip locked/);
  assert.match(sql, /lease_expires_at/);
  assert.match(sql, /stale_rectification_v4_job/);
  assert.match(sql, /can_confirm_exact_minute = false/);
  assert.match(sql, /question_target_event_id uuid/);
  assert.match(sql, /foreign key \(case_id, question_target_event_id\)/);
  assert.match(sql, /domain not in \('family', 'other'\) or scoreability = 'context_only'/);
});

test("v4 conversational migration persists the selected model with each turn", () => {
  assert.match(conversationalSql, /add column model_id text/i);
  assert.match(conversationalSql, /p_model_id text/i);
  assert.match(conversationalSql, /question, answer, model_id, action_id/i);
  assert.match(conversationalSql, /grant execute on function public\.submit_birth_time_rectification_v4_answer/i);
});

test("v4 handoff SQL enforces range acceptance, leases, idempotent settlement, and no profile time write", () => {
  for (const functionName of [
    "attach_birth_time_rectification_v4_question",
    "load_birth_time_rectification_v4_handoff",
    "claim_birth_time_rectification_v4_handoff",
    "begin_birth_time_rectification_v4_handoff_execution",
    "settle_birth_time_rectification_v4_handoff",
  ]) {
    assert.match(sql, new RegExp(`create function public\\.${functionName}\\(`, "i"));
    assert.match(sql, new RegExp(`grant execute on function public\\.${functionName}\\([\\s\\S]*?to service_role`, "i"));
  }
  assert.match(sql, /accepted_range_start is null[\s\S]*accepted_range_end is null[\s\S]*rectification_v4_handoff_conflict/i);
  assert.match(sql, /lease_expires_at > pg_catalog\.now\(\)[\s\S]*'in_progress'/i);
  assert.match(sql, /state in \('claimed', 'executing'\)[\s\S]*lease_expires_at > pg_catalog\.now\(\)/i);
  assert.match(sql, /birth_time_rectification_v4_handoff_settlements/i);
  assert.doesNotMatch(sql, /update\s+public\.profiles[\s\S]*active_birth_time/i);
});


test("current-question regeneration is service-role-only, atomic, idempotent, and preserves the semantic target", () => {
  assert.match(regenerationSql, /create or replace function public\.replace_birth_time_rectification_v4_current_question/i);
  assert.match(regenerationSql, /where value\.id = p_case_id and value\.user_id = p_user_id[\s\S]*for update/i);
  assert.match(regenerationSql, /where action\.user_id = p_user_id and action\.action_id = p_action_id[\s\S]*return v_case_id/i);
  assert.match(regenerationSql, /v_case\.version <> p_expected_version[\s\S]*stale_rectification_v4_case/i);
  assert.match(regenerationSql, /v_case\.deployment_mode <> 'v5_agent'/i);
  assert.match(regenerationSql, /'domain', v_case\.current_question->'domain'[\s\S]*'targetEventId', v_case\.current_question->'targetEventId'/i);
  assert.match(regenerationSql, /grant execute on function public\.replace_birth_time_rectification_v4_current_question\([\s\S]*to service_role/i);
  assert.doesNotMatch(regenerationSql, /insert into public\.birth_time_rectification_v4_(?:turns|events|jobs|candidate_snapshots)/i);
  assert.doesNotMatch(regenerationSql, /update\s+public\.profiles/i);
});


test("pending evidence resolution is atomic, ownership-checked, target-safe, and replay-consistent", () => {
  assert.match(pendingResolutionSql, /update public\.birth_time_rectification_v4_cases[\s\S]*set latest_snapshot_id = null[\s\S]*birth_time_rectification_v4_event_revisions[\s\S]*event_kind = 'relationship_end'[\s\S]*scoreability = 'scoreable'/i);
  assert.match(pendingResolutionSql, /p_resolved_pending_evidence jsonb/i);
  assert.match(pendingResolutionSql, /jsonb_typeof\(p_resolved_pending_evidence\)[\s\S]*'array'/i);
  assert.match(pendingResolutionSql, /case_id is distinct from v_case\.id[\s\S]*user_id is distinct from v_case\.user_id/i);
  assert.match(pendingResolutionSql, /target_event_id is not null[\s\S]*target_event_id is distinct from v_resolved_event_id/i);
  assert.match(pendingResolutionSql, /resolved_at is not null[\s\S]*rectification_v5_pending_evidence_already_resolved/i);
  assert.match(pendingResolutionSql, /birth_time_rectification_v4_events[\s\S]*case_id = v_case\.id[\s\S]*user_id = v_case\.user_id/i);
  assert.match(pendingResolutionSql, /update public\.birth_time_rectification_pending_evidence[\s\S]*resolved_event_id = v_resolved_event_id[\s\S]*resolved_at = p_now/i);
  assert.match(pendingResolutionSql, /v_was_completed[\s\S]*rectification_v5_replay_payload_mismatch/i);
  assert.match(pendingResolutionSql, /revoke all on function public\.complete_birth_time_rectification_v5_job\([\s\S]*grant execute[\s\S]*to service_role/i);
});
