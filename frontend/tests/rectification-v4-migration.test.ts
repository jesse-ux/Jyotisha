import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

const sql = readFileSync(new URL("../supabase/migrations/20260726020000_birth_time_rectification_v4.sql", import.meta.url), "utf8");

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
