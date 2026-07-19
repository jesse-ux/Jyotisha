from pathlib import Path


MIGRATION = (
    Path(__file__).resolve().parents[1]
    / "frontend"
    / "supabase"
    / "migrations"
    / "20260718095000_dynamic_choice_exact_action_receipts.sql"
)


def _sql() -> str:
    assert MIGRATION.exists()
    return " ".join(MIGRATION.read_text(encoding="utf-8").lower().split())


def test_duplicate_turn_replay_requires_exact_private_receipt() -> None:
    sql = _sql()
    for invariant in (
        "create or replace function public.save_birth_time_dynamic_turn",
        "p_action_id = any(v_case.processed_action_ids)",
        "v_case.turn_version is distinct from p_expected_version + 1",
        "v_private.dynamic_control -> 'lastactionreceipt' is distinct from v_receipt",
        "v_private.dynamic_control #>> '{lastactionreceipt,actionid}'",
        "is distinct from p_action_id::text",
        "raise exception 'stale_birth_time_dynamic_turn'",
    ):
        assert invariant in sql


def test_turn_save_locks_case_then_private_state() -> None:
    sql = _sql()
    case_lock = sql.index("from public.birth_time_rectification_cases c")
    private_lock = sql.index("from public.birth_time_rectification_dynamic_state s")
    assert case_lock < private_lock
    assert "for update" in sql[case_lock:private_lock]
    assert "for update" in sql[private_lock:]


def test_receipt_replacement_is_private_and_service_role_only() -> None:
    sql = _sql()
    assert "p_private_state #> '{dynamiccontrol,lastactionreceipt}'" in sql
    assert "jsonb_typeof(v_receipt) is distinct from 'object'" in sql
    assert "revoke all on function public.save_birth_time_dynamic_turn" in sql
    assert "grant execute on function public.save_birth_time_dynamic_turn" in sql
    pure_lines = [
        line for line in MIGRATION.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("--")
    ]
    assert len(pure_lines) <= 250
