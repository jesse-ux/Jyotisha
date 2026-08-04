import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const migration = readFileSync(
  new URL("../supabase/migrations/20260804010000_agentic_rectification_candidate_acceptance.sql", import.meta.url),
  "utf8",
);

const preservationMigration = readFileSync(
  new URL("../supabase/migrations/20260804020000_preserve_reported_birth_time_on_candidate_acceptance.sql", import.meta.url),
  "utf8",
);

test("candidate acceptance migration adds accepted status and durable result ownership", () => {
  assert.match(migration, /birth_time_status in \([\s\S]*'reported'[\s\S]*'assessing'[\s\S]*'rectifying'[\s\S]*'candidate'[\s\S]*'accepted'[\s\S]*'confirmed'[\s\S]*\)/);
  assert.match(migration, /create table public\.agentic_rectification_results/);
  assert.match(migration, /user_id uuid not null references auth\.users\(id\)/);
  assert.match(migration, /session_id uuid not null references public\.chat_sessions\(id\)/);
  assert.match(migration, /expires_at timestamptz not null/);
  assert.match(migration, /invalidated_at timestamptz/);
});

test("candidate acceptance RPC validates ownership, freshness, gate, membership, and profile baseline", () => {
  assert.match(migration, /where id = p_result_id[\s\S]*user_id = p_user_id[\s\S]*session_id = p_session_id/);
  assert.match(migration, /invalidated_at is not null or v_result\.expires_at <= pg_catalog\.now\(\)/);
  assert.match(migration, /if not v_result\.selection_allowed/);
  assert.match(migration, /jsonb_array_elements\(v_result\.candidates\)[\s\S]*candidate ->> 'time'/);
  assert.match(migration, /v_profile\.birth_date is distinct from v_result\.baseline_birth_date/);
  assert.match(migration, /v_profile\.reported_birth_time is distinct from v_result\.baseline_reported_birth_time/);
  assert.match(migration, /v_profile\.active_birth_time is distinct from v_result\.baseline_active_birth_time/);
  assert.match(migration, /v_profile\.birth_time_period is distinct from v_result\.baseline_birth_time_period/);
  assert.match(migration, /v_profile\.latitude is distinct from v_result\.baseline_latitude/);
  assert.match(migration, /v_profile\.longitude is distinct from v_result\.baseline_longitude/);
  assert.match(migration, /v_profile\.timezone_offset is distinct from v_result\.baseline_timezone_offset/);
});

test("candidate acceptance is idempotent before baseline checks and separates accepted from confirmed", () => {
  const idempotent = migration.indexOf("if v_result.selected_time is not null");
  const baseline = migration.indexOf("select * into v_profile");
  assert.ok(idempotent >= 0 && baseline > idempotent);
  assert.match(migration, /v_result\.confirmation_allowed[\s\S]*v_result\.representative_time is not distinct from p_time[\s\S]*then 'engine_confirmed'[\s\S]*else 'user_accepted'/);
  assert.match(migration, /v_status := case when v_selection_kind = 'engine_confirmed' then 'confirmed' else 'accepted' end/);
  assert.match(migration, /agentic_rectification_candidate_superseded/);
  assert.match(migration, /v_profile\.active_birth_time is distinct from v_result\.selected_time/);
});

test("candidate acceptance writes the active chart time without replacing reported time", () => {
  const profileUpdate = migration.slice(
    migration.indexOf("update public.profiles"),
    migration.indexOf("update public.agentic_rectification_results", migration.indexOf("update public.profiles")),
  );
  assert.match(profileUpdate, /active_birth_time = p_time/);
  assert.match(profileUpdate, /birth_time = p_time/);
  assert.match(profileUpdate, /birth_time_status = v_status/);
  assert.doesNotMatch(profileUpdate, /reported_birth_time\s*=/);
});

test("candidate acceptance RPC is service-role only", () => {
  assert.match(migration, /revoke all on function public\.accept_agentic_rectification_candidate[\s\S]*from public, anon, authenticated/);
  assert.match(migration, /grant execute on function public\.accept_agentic_rectification_candidate[\s\S]*to service_role/);
  assert.doesNotMatch(migration, /grant execute on function public\.accept_agentic_rectification_candidate[\s\S]*to authenticated/);
});


test("profile declaration changes invalidate restored Agentic candidate results", () => {
  assert.match(migration, /create trigger profiles_invalidate_agentic_rectification_results/);
  assert.match(migration, /old\.birth_time_period is distinct from new\.birth_time_period/);
  assert.match(migration, /old\.latitude is distinct from new\.latitude/);
  assert.match(migration, /set invalidated_at = pg_catalog\.now\(\)/);
  assert.match(migration, /coalesce\(new\.birth_time_status, ''\) not in \('accepted', 'confirmed'\)/);
});


test("forward repair separates original declaration from the active chart time", () => {
  const profileUpdate = preservationMigration.slice(
    preservationMigration.indexOf("update public.profiles\n  set active_birth_time"),
    preservationMigration.indexOf("update public.agentic_rectification_results", preservationMigration.indexOf("update public.profiles\n  set active_birth_time")),
  );
  assert.match(profileUpdate, /active_birth_time = p_time/);
  assert.match(profileUpdate, /birth_time_status = v_status/);
  assert.doesNotMatch(profileUpdate, /^\s*birth_time = p_time/m);
  assert.doesNotMatch(profileUpdate, /reported_birth_time\s*=/);
  assert.doesNotMatch(preservationMigration, /v_profile\.birth_time is distinct from v_result\.selected_time/);
});

test("forward repair removes legacy field mirroring and repairs already selected Agentic profiles", () => {
  const guard = preservationMigration.slice(
    preservationMigration.indexOf("create or replace function public.guard_birth_time_journey"),
    preservationMigration.indexOf("update public.profiles", preservationMigration.indexOf("create or replace function public.guard_birth_time_journey")),
  );
  assert.doesNotMatch(guard, /new\.birth_time := new\.active_birth_time/);
  assert.doesNotMatch(guard, /new\.active_birth_time := new\.birth_time/);
  assert.match(preservationMigration, /p\.birth_time_status in \('accepted', 'confirmed'\)/);
  assert.match(preservationMigration, /p\.active_birth_time is not distinct from selected\.selected_time/);
});


test("forward repair lets the user change a previously adopted candidate", () => {
  assert.doesNotMatch(preservationMigration, /agentic_rectification_candidate_already_selected/);
  assert.match(preservationMigration, /v_profile\.active_birth_time is distinct from v_result\.selected_time/);
  assert.match(preservationMigration, /update public\.agentic_rectification_results[\s\S]*selected_time = p_time/);
});
