import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "frontend" / "supabase" / "migrations"
V3_MIGRATIONS = (MIGRATIONS / "20260717020000_birth_time_journey.sql",) + tuple(
    sorted(MIGRATIONS.glob("2026072*conversational*.sql"))
) + (
    MIGRATIONS / "20260720040000_rectification_question_handoff.sql",
)


def _sql() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in V3_MIGRATIONS)


def _function_body(name: str) -> str:
    matches = re.findall(
        rf"create or replace function public\.{re.escape(name)}\([\s\S]*?\)\s*"
        rf"returns[\s\S]*?\bas \$\$([\s\S]*?)\$\$;",
        _sql().lower(),
    )
    assert matches, f"missing function body: {name}"
    return matches[-1]


def test_v3_tables_and_mutation_rpcs_are_service_role_only() -> None:
    sql = _sql().lower()
    tables = (
        "birth_time_rectification_cases",
        "birth_time_rectification_turns",
        "birth_time_rectification_event_evidence",
        "birth_time_rectification_billing",
        "birth_time_rectification_action_receipts",
        "birth_time_rectification_question_handoffs",
        "birth_time_rectification_handoff_attach_receipts",
        "birth_time_rectification_handoff_settlements",
    )
    for table in tables:
        assert f"alter table public.{table} enable row level security" in sql
        assert re.search(rf"revoke all on table public\.{table}\s+from (?:public, )?anon, authenticated", sql)

    public_rpcs = (
        "reserve_conversational_rectification_fee",
        "complete_conversational_rectification_fee",
        "release_conversational_rectification_fee",
        "create_conversational_rectification_case",
        "load_conversational_rectification_case",
        "replay_conversational_rectification_action",
        "save_conversational_rectification_turn",
        "pause_conversational_rectification_case",
        "abandon_conversational_rectification_case",
        "confirm_conversational_rectification_candidate",
        "import_legacy_conversational_rectification_case",
        "attach_conversational_rectification_question",
        "load_conversational_rectification_handoff",
        "claim_conversational_rectification_handoff",
        "begin_conversational_rectification_handoff_execution",
        "settle_conversational_rectification_handoff",
    )
    for function in public_rpcs:
        assert re.search(rf"revoke all on function public\.{function}\(", sql)
        assert not re.search(rf"grant execute on function public\.{function}\([\s\S]{{0,800}}?to (?:anon|authenticated)", sql)


def test_mutations_bind_owner_version_action_and_fingerprint_before_writes() -> None:
    # This is an explicit per-RPC guard matrix.  It prevents an unrelated
    # function elsewhere in the migration bundle from satisfying a global
    # keyword search.  Runtime adversarial/no-side-effect behavior is covered
    # by test_conversational_rectification_postgres_runtime.py.
    guard_matrix = {
        "reserve_conversational_rectification_fee": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "for update",
        ),
        "complete_conversational_rectification_fee": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "for update",
        ),
        "release_conversational_rectification_fee": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "for update",
        ),
        "create_conversational_rectification_case": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "v_fingerprint", "for update",
        ),
        "save_conversational_rectification_turn": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "p_command_fingerprint", "for update",
        ),
        "pause_conversational_rectification_case": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "p_command_fingerprint", "for update",
        ),
        "abandon_conversational_rectification_case": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "p_command_fingerprint", "for update",
        ),
        "confirm_conversational_rectification_candidate": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "p_command_fingerprint", "for update",
        ),
        "import_legacy_conversational_rectification_case": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "p_legacy_case_id", "for update",
        ),
        "attach_conversational_rectification_question": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "p_question_fingerprint", "for update",
        ),
        "claim_conversational_rectification_handoff": (
            "p_user_id", "p_case_id", "p_expected_version", "p_action_id", "p_question_fingerprint", "for update",
        ),
        "begin_conversational_rectification_handoff_execution": (
            "p_user_id", "p_case_id", "p_expected_version", "p_claim_action_id", "p_request_id", "p_question_fingerprint", "for update",
        ),
        "settle_conversational_rectification_handoff": (
            "p_user_id", "p_case_id", "p_claim_action_id", "p_request_id", "for update",
        ),
    }
    for function, guards in guard_matrix.items():
        body = _function_body(function)
        for guard in guards:
            assert guard in body, f"{function} is missing guard {guard}"


def test_public_projection_excludes_private_weights() -> None:
    contracts = (ROOT / "frontend/src/lib/conversational-rectification/contracts.ts").read_text(encoding="utf-8")
    projection = (ROOT / "frontend/src/lib/conversational-rectification/technical-packet.ts").read_text(encoding="utf-8")

    public_region = contracts[contracts.index("const candidateSchema"):contracts.index("export type ConversationalRectificationTurn")]
    assert "candidateWeights" not in public_region
    assert "partitionIds" not in public_region
    assert "candidateWeights" not in projection[projection.index("export function projectRectificationTechnicalPacket"):]


def test_synthetic_fixtures_contain_no_secret_or_token_shapes() -> None:
    fixture = (ROOT / "frontend/tests/conversational-rectification-e2e.test.ts").read_text(encoding="utf-8")
    forbidden = (
        r"sb-[a-z0-9]{16,}",
        r"eyj[a-z0-9_-]+\.[a-z0-9_-]+\.[a-z0-9_-]+",
        r"bearer\s+[a-z0-9._-]{20,}",
        r"supabase_service_role_key\s*=",
        r"openai_api_key\s*=\s*[\"'](?:sk-|[a-z0-9]{32})",
        r"refresh_token",
        r"auth-token",
    )
    for pattern in forbidden:
        assert re.search(pattern, fixture, re.IGNORECASE) is None
