import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const guidedMigration = readFileSync(
  new URL("../supabase/migrations/20260718040000_guided_candidate_actions.sql", import.meta.url),
  "utf8",
);
const scoringMigration = readFileSync(
  new URL("../supabase/migrations/20260718030000_birth_time_scoring_job_lifecycle.sql", import.meta.url),
  "utf8",
);

test("guided save and confirm RPCs are service-role-only and version/receipt guarded", () => {
  assert.match(guidedMigration, /security definer/g);
  assert.match(guidedMigration, /where id = p_case_id\s+and user_id = p_user_id/g);
  assert.match(guidedMigration, /p_action_id = any\(receipts\)/g);
  assert.match(guidedMigration, /current_version <> p_expected_version/g);
  assert.match(guidedMigration, /and turn_version = p_expected_version/g);
  assert.match(guidedMigration, /revoke all on function public\.save_guided_birth_time_candidate/);
  assert.match(guidedMigration, /revoke all on function public\.confirm_guided_birth_time_candidate/);
  assert.match(guidedMigration, /grant execute[\s\S]*to service_role/g);
  assert.doesNotMatch(guidedMigration, /to authenticated/);
});

test("only high confirmation atomically updates the profile active time", () => {
  const saveBody = guidedMigration.split("create or replace function public.confirm_guided_birth_time_candidate")[0];
  assert.doesNotMatch(saveBody, /active_birth_time/);
  assert.match(guidedMigration, /update public\.birth_time_rectification_cases[\s\S]*update public\.profiles\s+set active_birth_time = p_time/);
});

test("completed medium scoring remains consistent after candidate_saved", () => {
  assert.match(scoringMigration, /v_result_confidence = 'medium'[\s\S]*present_medium_result[\s\S]*candidate_saved/);
  assert.match(scoringMigration, /v_action_kind in \('present_low_result', 'present_medium_result', 'candidate_saved', 'request_candidate_confirmation'\)/);
});

test("legacy projected candidate actions execute only from empty persisted turns", () => {
  const emptyTurnFallbacks = guidedMigration.match(/or turn_state is null\s+or turn_state = '\{\}'::jsonb/g) ?? [];
  assert.equal(emptyTurnFallbacks.length, 2);
  assert.match(guidedMigration, /present_medium_result[\s\S]*or turn_state is null\s+or turn_state = '\{\}'::jsonb/);
  assert.match(guidedMigration, /request_candidate_confirmation[\s\S]*or turn_state is null\s+or turn_state = '\{\}'::jsonb/);
  assert.match(guidedMigration, /candidate_result ->> 'confidence' = 'medium'/);
  assert.match(guidedMigration, /candidate_result ->> 'confidence' = 'high'/);
  assert.match(guidedMigration, /winningSegment,representativeTime/);
});
