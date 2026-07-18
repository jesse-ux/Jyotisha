import re
from pathlib import Path

MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "supabase"
    / "migrations"
    / "20260718090000_dynamic_choice_birth_time_rectification.sql"
)
TRANSITIONS_MIGRATION = MIGRATION.with_name(
    "20260718091000_dynamic_choice_birth_time_transitions.sql"
)


def _sql() -> str:
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in (MIGRATION, TRANSITIONS_MIGRATION)
    )
    return re.sub(r"\s+", " ", source.lower()).strip()


def _function(sql: str, name: str, next_name: str | None = None) -> str:
    body = sql.split(f"create or replace function public.{name}", 1)[1]
    return body.split(
        f"create or replace function public.{next_name}" if next_name else "$$;",
        1,
    )[0]


def test_private_dynamic_state_is_service_role_only_and_bounded() -> None:
    sql = _sql()
    assert "journey_protocol text not null default 'legacy-guided-v1'" in sql
    assert "check (journey_protocol in ('legacy-guided-v1', 'dynamic-choice-v2'))" in sql
    assert "create table if not exists public.birth_time_rectification_dynamic_state" in sql
    for definition in (
        "candidate_model jsonb",
        "current_choice_question jsonb",
        "choice_answers jsonb not null default '[]'::jsonb",
        "choice_evidence jsonb not null default '[]'::jsonb",
        "dynamic_control jsonb not null",
        "agent_context jsonb not null default '[]'::jsonb",
    ):
        assert definition in sql
    assert "jsonb_array_length(choice_answers) <= 50" in sql
    assert "jsonb_array_length(choice_evidence) <= 10" in sql
    assert "jsonb_array_length(agent_context) <= 10" in sql
    assert "birth_time_dynamic_agent_context_valid(agent_context)" in sql
    assert "pg_catalog.length(note) > 240" in sql
    assert "alter table public.birth_time_rectification_dynamic_state enable row level security" in sql
    assert "revoke all on table public.birth_time_rectification_dynamic_state from anon, authenticated" in sql
    assert "grant all on table public.birth_time_rectification_dynamic_state to service_role" in sql


def test_dynamic_case_creation_is_one_service_role_transaction() -> None:
    sql = _sql()
    body = _function(sql, "create_birth_time_dynamic_case", "save_birth_time_dynamic_turn")
    assert "security definer" in body
    assert "set search_path = ''" in body
    assert "insert into public.birth_time_rectification_cases" in body
    assert "perform public.persist_birth_time_dynamic_private_state" in body
    assert "update public.profiles" in body
    assert "raise exception 'birth_time_dynamic_profile_not_found'" in body
    assert "revoke all on function public.create_birth_time_dynamic_case" in sql
    assert "grant execute on function public.create_birth_time_dynamic_case" in sql


def test_dynamic_turn_rpc_is_versioned_private_and_replay_safe() -> None:
    sql = _sql()
    body = _function(sql, "save_birth_time_dynamic_turn", "upgrade_birth_time_legacy_case")
    for invariant in (
        "security definer",
        "set search_path = ''",
        "c.user_id = p_user_id",
        "v_case.journey_protocol is distinct from 'dynamic-choice-v2'",
        "p_action_id = any(v_case.processed_action_ids)",
        "v_case.turn_version is distinct from p_expected_version",
        "raise exception 'stale_birth_time_dynamic_turn'",
        "update public.birth_time_rectification_cases",
        "perform public.persist_birth_time_dynamic_private_state",
    ):
        assert invariant in body
    assert "revoke all on function public.save_birth_time_dynamic_turn" in sql
    assert "grant execute on function public.save_birth_time_dynamic_turn" in sql


def test_dynamic_scoring_rpcs_bind_job_identity_and_replay_state() -> None:
    sql = _sql()
    for function_name in (
        "complete_birth_time_dynamic_scoring_job",
        "fail_birth_time_dynamic_scoring_job",
    ):
        body = _function(sql, function_name)
        for invariant in (
            "security definer",
            "set search_path = ''",
            "j.case_id = p_case_id",
            "j.user_id = p_user_id",
            "v_job.evidence_fingerprint is distinct from p_evidence_fingerprint",
            "v_job.algorithm_version is distinct from p_algorithm_version",
            "v_case.turn_version is distinct from p_expected_version",
            "coalesce(v_case.turn_state #>> '{nextaction,kind}', '') not in",
            "p_job_id::text",
            "perform public.persist_birth_time_dynamic_private_state",
        ):
            assert invariant in body
        assert f"revoke all on function public.{function_name}" in sql
        assert f"grant execute on function public.{function_name}" in sql

    complete = _function(
        sql,
        "complete_birth_time_dynamic_scoring_job",
        "fail_birth_time_dynamic_scoring_job",
    )
    assert "v_job.status = 'completed'" in complete
    assert "v_job.result is distinct from p_candidate_result" in complete
    assert "p_candidate_result ->> 'algorithmversion'" in complete

    failed = _function(sql, "fail_birth_time_dynamic_scoring_job")
    assert "v_job.status = 'failed'" in failed
    assert "v_job.failure_code is distinct from p_failure_code" in failed


def test_private_state_upsert_has_one_internal_owner_only_implementation() -> None:
    sql = _sql()
    body = _function(
        sql,
        "persist_birth_time_dynamic_private_state",
        "create_birth_time_dynamic_case",
    )
    assert "insert into public.birth_time_rectification_dynamic_state" in body
    assert "on conflict (case_id) do update" in body
    assert sql.count("insert into public.birth_time_rectification_dynamic_state") == 1
    assert "revoke all on function public.persist_birth_time_dynamic_private_state" in sql
