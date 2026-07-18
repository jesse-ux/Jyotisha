import re
from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "supabase"
    / "migrations"
    / "20260717020000_birth_time_journey.sql"
)
FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
EVIDENCE_MIGRATION = (
    MIGRATION.parent / "20260718010000_birth_time_evidence_rectification.sql"
)
AGENT_GUIDED_MIGRATION = (
    MIGRATION.parent / "20260718020000_agent_guided_birth_time_rectification.sql"
)
SCORING_JOB_MIGRATION = (
    MIGRATION.parent / "20260718030000_birth_time_scoring_job_lifecycle.sql"
)


def _sql() -> str:
    return re.sub(r"\s+", " ", MIGRATION.read_text(encoding="utf-8").lower()).strip()


def test_birth_time_service_role_can_update_journey_profile_columns() -> None:
    migrations = sorted(MIGRATION.parent.glob("*.sql"))
    sql = re.sub(
        r"\s+",
        " ",
        "\n".join(path.read_text(encoding="utf-8") for path in migrations).lower(),
    ).strip()

    assert (
        "grant update ( reported_birth_time, active_birth_time, birth_time, "
        "birth_time_source, birth_time_period, birth_time_clue, "
        "uncertainty_before_minutes, uncertainty_after_minutes, "
        "birth_time_status, rectification_confidence, rectification_case_id "
        ") on table public.profiles to service_role"
    ) in sql


def test_birth_time_profile_contract_separates_reported_and_active_times() -> None:
    sql = _sql()

    for definition in (
        "reported_birth_time time without time zone",
        "active_birth_time time without time zone",
        "birth_time_source text",
        "birth_time_period text",
        "birth_time_clue text",
        "uncertainty_before_minutes integer",
        "uncertainty_after_minutes integer",
        "birth_time_status text",
        "rectification_confidence numeric(5, 2)",
        "rectification_case_id uuid",
    ):
        assert f"add column if not exists {definition}" in sql

    assert "reported_birth_time = coalesce(reported_birth_time, birth_time)" in sql
    assert "active_birth_time = coalesce(active_birth_time, birth_time)" in sql
    assert "birth_time_source = coalesce(birth_time_source, 'legacy_import')" in sql
    assert "birth_time_status = coalesce(birth_time_status, 'confirmed')" in sql
    assert "old.reported_birth_time is not null" in sql
    assert "new.reported_birth_time is distinct from old.reported_birth_time" in sql
    assert "raise exception 'reported_birth_time_is_immutable'" in sql
    assert "new.birth_time := new.active_birth_time" in sql
    assert "revoke update (birth_time) on table public.profiles from authenticated" in sql
    client_grant = sql.split("grant update ( reported_birth_time", 1)[1]
    client_grant = client_grant.split(") on table public.profiles to authenticated", 1)[0]
    assert "active_birth_time" not in client_grant
    assert "birth_time_status" not in client_grant
    assert "rectification_case_id" not in client_grant


def test_birth_time_profile_contract_constrains_deterministic_states() -> None:
    sql = _sql()

    for value in (
        "hospital_record",
        "family_exact",
        "approximate",
        "period_only",
        "unknown",
        "legacy_import",
    ):
        assert f"'{value}'" in sql

    for value in ("reported", "assessing", "rectifying", "candidate", "confirmed"):
        assert f"'{value}'" in sql

    assert "uncertainty_before_minutes between 0 and 720" in sql
    assert "uncertainty_after_minutes between 0 and 720" in sql
    assert "rectification_confidence between 0 and 100" in sql


def test_rectification_cases_are_owner_scoped_and_auditable() -> None:
    sql = _sql()

    assert "create table if not exists public.birth_time_rectification_cases" in sql
    for definition in (
        "id uuid primary key default gen_random_uuid()",
        "user_id uuid not null references auth.users(id) on delete cascade",
        "questionnaire jsonb not null default '{}'::jsonb",
        "journey_snapshot jsonb not null default '{}'::jsonb",
        "answers jsonb not null default '{}'::jsonb",
        "candidate_scan jsonb not null default '{}'::jsonb",
        "scoring_result jsonb not null default '{}'::jsonb",
        "algorithm_version text not null default 'birth-time-journey-v1'",
        "ayanamsa text not null default 'lahiri'",
        "node_mode text not null default 'true'",
        "confirmed_at timestamptz",
    ):
        assert definition in sql

    assert "alter table public.birth_time_rectification_cases enable row level security" in sql
    assert "birth_time_cases_select_own" in sql
    assert "birth_time_cases_insert_own" in sql
    assert "birth_time_cases_update_own" in sql
    assert "using ((select auth.uid()) = user_id)" in sql
    assert "with check ((select auth.uid()) = user_id)" in sql
    assert "grant select on table public.birth_time_rectification_cases to authenticated" in sql
    assert "grant insert" in sql
    assert "grant update" in sql
    assert "grant delete" not in sql


def test_web_onboarding_uses_the_deterministic_free_journey() -> None:
    page = (FRONTEND / "src" / "app" / "page.tsx").read_text(encoding="utf-8")
    route = (
        FRONTEND / "src" / "app" / "api" / "birth-time-journey" / "route.ts"
    ).read_text(encoding="utf-8")
    mastra = (FRONTEND / "src" / "mastra" / "index.ts").read_text(encoding="utf-8")

    assert "<BirthTimeIntakeFields" in page
    assert "requestBirthTimeAssessment" in page
    assert "<BirthTimeRectification" in page
    assert "reported_birth_time" in page
    assert "active_birth_time" in page
    assert "birthTimeStatus" in page
    assert "consultation-billing" not in route
    assert 'entry_mode: entryMode' in mastra
    assert 'entry_mode: "direct_chart"' not in mastra


def test_evidence_rectification_persists_server_owned_results() -> None:
    sql = re.sub(
        r"\s+",
        " ",
        EVIDENCE_MIGRATION.read_text(encoding="utf-8").lower(),
    ).strip()

    for definition in (
        "life_events jsonb not null default '[]'::jsonb",
        "candidate_result jsonb not null default '{}'::jsonb",
        "event_scoring_version text",
        "candidate_result_id uuid",
        "candidate_saved_at timestamptz",
    ):
        assert f"add column if not exists {definition}" in sql

    assert "'confirming'" in sql
    assert (
        "revoke update ( life_events, candidate_result, event_scoring_version, "
        "candidate_result_id, candidate_saved_at, confirmed_time, confirmed_at "
        ") on table public.birth_time_rectification_cases from authenticated"
    ) in sql
    assert "grant all on table public.birth_time_rectification_cases to service_role" in sql


def test_agent_guided_rectification_migration_versions_turns_and_jobs() -> None:
    sql = re.sub(
        r"\s+", " ", AGENT_GUIDED_MIGRATION.read_text(encoding="utf-8").lower()
    ).strip()

    for definition in (
        "turn_version bigint not null default 0",
        "turn_state jsonb not null default '{}'::jsonb",
        "evidence_draft jsonb",
        "processed_action_ids uuid[] not null default '{}'::uuid[]",
        "adaptive_round integer not null default 0",
        "asked_domains text[] not null default '{}'::text[]",
    ):
        assert f"add column if not exists {definition}" in sql

    assert "jsonb_typeof(turn_state) = 'object'" in sql
    assert "evidence_draft is null or jsonb_typeof(evidence_draft) = 'object'" in sql
    assert "cardinality(processed_action_ids) <= 100" in sql
    assert "adaptive_round between 0 and 3" in sql
    assert "birth_time_rectification_scoring_jobs" in sql
    assert "id uuid primary key default gen_random_uuid()" in sql
    assert "case_id uuid not null references public.birth_time_rectification_cases(id) on delete cascade" in sql
    assert "status text not null default 'pending'" in sql
    assert "expires_at timestamptz not null" in sql
    assert "unique (case_id, evidence_fingerprint, algorithm_version)" in sql
    assert "revoke all on table public.birth_time_rectification_scoring_jobs from anon, authenticated" in sql
    assert "grant all on table public.birth_time_rectification_scoring_jobs to service_role" in sql


def test_scoring_job_lifecycle_is_atomic_and_service_role_only() -> None:
    sql = re.sub(
        r"\s+", " ", SCORING_JOB_MIGRATION.read_text(encoding="utf-8").lower()
    ).strip()

    for function_name in (
        "create_birth_time_scoring_job",
        "claim_birth_time_scoring_job",
        "complete_birth_time_scoring_job",
        "fail_birth_time_scoring_job",
    ):
        assert f"create or replace function public.{function_name}" in sql
        assert f"revoke all on function public.{function_name}" in sql
        assert f"grant execute on function public.{function_name}" in sql

    create_body = sql.split("create or replace function public.create_birth_time_scoring_job", 1)[1]
    create_body = create_body.split("create or replace function public.claim_birth_time_scoring_job", 1)[0]
    assert "update public.birth_time_rectification_cases" in create_body
    assert "insert into public.birth_time_rectification_scoring_jobs" in create_body
    assert "and user_id = p_user_id" in create_body
    assert "and turn_version = p_expected_version" in create_body

    claim_body = sql.split("create or replace function public.claim_birth_time_scoring_job", 1)[1]
    claim_body = claim_body.split("create or replace function public.complete_birth_time_scoring_job", 1)[0]
    assert "j.case_id = p_case_id" in claim_body
    assert "j.user_id = p_user_id" in claim_body
    assert "v_job.evidence_fingerprint is distinct from p_evidence_fingerprint" in claim_body
    assert "v_job.algorithm_version is distinct from p_algorithm_version" in claim_body
    assert claim_body.index(
        "v_job.algorithm_version is distinct from p_algorithm_version"
    ) < claim_body.index("update public.birth_time_rectification_scoring_jobs")
    assert "#>> '{nextaction,jobid}' is distinct from p_job_id::text" in claim_body
    assert "#>> '{nextaction,kind}' is distinct from" in claim_body
    assert "status in ('pending', 'failed', 'processing')" in claim_body
    assert "status = 'processing'" in claim_body
    assert "v_job.updated_at <= p_now - interval '60 seconds'" in claim_body
    assert "expires_at = p_now + interval '15 minutes'" in claim_body
    assert "birth_time_scoring_job_expired" not in claim_body
    assert "v_candidate_result is distinct from v_job.result" in claim_body
    assert "birth_time_scoring_result_inconsistent" in claim_body

    complete_body = sql.split("create or replace function public.complete_birth_time_scoring_job", 1)[1]
    complete_body = complete_body.split("create or replace function public.fail_birth_time_scoring_job", 1)[0]
    assert "update public.birth_time_rectification_scoring_jobs" in complete_body
    assert "update public.birth_time_rectification_cases" in complete_body

    fail_body = sql.split("create or replace function public.fail_birth_time_scoring_job", 1)[1]
    assert "update public.birth_time_rectification_scoring_jobs" in fail_body
    assert "update public.birth_time_rectification_cases" in fail_body
    assert "security definer" in sql
    assert "to service_role" in sql


def test_poll_scoring_route_authenticates_before_parsing() -> None:
    route = (
        FRONTEND / "src" / "app" / "api" / "birth-time-journey" / "route.ts"
    ).read_text(encoding="utf-8")

    assert route.index("supabase.auth.getUser()") < route.index(
        "birthTimeJourneyRequestSchema.safeParse"
    )
    assert 'case "poll_scoring"' in route
    assert "service.pollScoringJob(" in route
