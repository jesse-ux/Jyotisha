import re
from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "supabase"
    / "migrations"
    / "20260717020000_birth_time_journey.sql"
)


def _sql() -> str:
    return re.sub(r"\s+", " ", MIGRATION.read_text(encoding="utf-8").lower()).strip()


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
