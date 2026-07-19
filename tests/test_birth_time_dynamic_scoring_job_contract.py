from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "supabase"
    / "migrations"
    / "20260718094000_dynamic_choice_scoring_job_lifecycle.sql"
)


def _sql() -> str:
    assert MIGRATION.exists(), "dynamic scoring lifecycle migration is required"
    return " ".join(MIGRATION.read_text(encoding="utf-8").lower().split())


def _function(sql: str, name: str, next_name: str | None = None) -> str:
    body = sql.split(f"create function public.{name}", 1)[1]
    marker = f"create function public.{next_name}" if next_name else "commit;"
    return body.split(marker, 1)[0]


def test_dynamic_job_creation_is_atomic_private_and_replay_safe() -> None:
    sql = _sql()
    body = _function(
        sql,
        "create_birth_time_dynamic_scoring_job",
        "claim_birth_time_dynamic_scoring_job",
    )
    for invariant in (
        "security definer",
        "set search_path = ''",
        "journey_protocol = 'dynamic-choice-v2'",
        "for update",
        "p_action_id = any(v_case.processed_action_ids)",
        "p_question_id",
        "p_evidence_fingerprint",
        "p_algorithm_version",
        "insert into public.birth_time_rectification_scoring_jobs",
        "update public.birth_time_rectification_cases",
        "perform public.persist_birth_time_dynamic_private_state",
    ):
        assert invariant in body
    assert "processed_action_ids" in body
    assert "'score_pending'" in body


def test_dynamic_job_claim_locks_v2_and_validates_completed_replay() -> None:
    sql = _sql()
    body = _function(sql, "claim_birth_time_dynamic_scoring_job")
    for invariant in (
        "security definer",
        "set search_path = ''",
        "journey_protocol = 'dynamic-choice-v2'",
        "for update",
        "v_job.evidence_fingerprint is distinct from p_evidence_fingerprint",
        "v_job.algorithm_version is distinct from p_algorithm_version",
        "v_job.status = 'completed'",
        "v_case.candidate_result is distinct from v_job.result",
        "v_case.turn_state #>> '{nextaction,kind}'",
        "'processing'",
        "interval '60 seconds'",
    ):
        assert invariant in body
    assert "claim_state text" in body
    assert "algorithm_version text" in body


def test_dynamic_job_functions_are_service_role_only_and_reviewable() -> None:
    sql = _sql()
    for name in (
        "create_birth_time_dynamic_scoring_job",
        "claim_birth_time_dynamic_scoring_job",
    ):
        assert f"revoke all on function public.{name}" in sql
        assert f"grant execute on function public.{name}" in sql
    pure_lines = [
        line for line in MIGRATION.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("--")
    ]
    assert len(pure_lines) <= 250
