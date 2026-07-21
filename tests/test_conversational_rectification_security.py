import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "frontend" / "supabase" / "migrations"
V3_MIGRATIONS = tuple(sorted(MIGRATIONS.glob("2026072*conversational*.sql"))) + (
    MIGRATIONS / "20260720040000_rectification_question_handoff.sql",
)


def _sql() -> str:
    return "\n".join(path.read_text(encoding="utf-8") for path in V3_MIGRATIONS)


def test_v3_tables_and_mutation_rpcs_are_service_role_only() -> None:
    sql = _sql().lower()
    tables = (
        "birth_time_rectification_turns",
        "birth_time_rectification_event_evidence",
        "birth_time_rectification_billing",
        "birth_time_rectification_question_handoffs",
        "birth_time_rectification_handoff_attach_receipts",
        "birth_time_rectification_handoff_settlements",
    )
    for table in tables:
        assert f"alter table public.{table} enable row level security" in sql
        assert re.search(rf"revoke all on table public\.{table}\s+from (?:public, )?anon, authenticated", sql)
        assert not re.search(rf"grant (?:select|insert|update|delete|all).+public\.{table}.+to authenticated", sql)

    mutation_rpcs = (
        "create_conversational_rectification_case",
        "save_conversational_rectification_turn",
        "pause_conversational_rectification_case",
        "abandon_conversational_rectification_case",
        "confirm_conversational_rectification_candidate",
        "import_legacy_conversational_rectification_case",
        "attach_conversational_rectification_question",
        "claim_conversational_rectification_handoff",
        "settle_conversational_rectification_handoff",
    )
    for function in mutation_rpcs:
        assert re.search(rf"revoke all on function public\.{function}\(", sql)
        assert not re.search(rf"grant execute on function public\.{function}\([\s\S]{{0,800}}?to (?:anon|authenticated)", sql)


def test_mutations_bind_owner_version_action_and_fingerprint_before_writes() -> None:
    sql = _sql().lower()
    for field in ("p_user_id", "p_case_id", "p_expected_version", "p_action_id"):
        assert field in sql
    assert "p_command_fingerprint" in sql
    assert "p_question_fingerprint" in sql
    assert "for update" in sql
    assert "conversational_stale_turn" in sql
    assert "conversational_action_conflict" in sql
    assert "question_fingerprint" in sql


def test_public_projection_excludes_private_weights_and_future_evidence_is_not_scored() -> None:
    contracts = (ROOT / "frontend/src/lib/conversational-rectification/contracts.ts").read_text(encoding="utf-8")
    projection = (ROOT / "frontend/src/lib/conversational-rectification/technical-packet.ts").read_text(encoding="utf-8")
    route = (ROOT / "frontend/src/app/api/birth-time-conversation/route.ts").read_text(encoding="utf-8")
    orchestrator = (ROOT / "frontend/src/lib/conversational-rectification/orchestrator.ts").read_text(encoding="utf-8")

    public_region = contracts[contracts.index("const candidateSchema"):contracts.index("export type ConversationalRectificationTurn")]
    assert "candidateWeights" not in public_region
    assert "partitionIds" not in public_region
    assert "candidateWeights" not in projection[projection.index("export function projectRectificationTechnicalPacket"):]
    assert "item.scoreable !== true" in route
    assert "futureWindows" in orchestrator
    assert "scoreable: false" in orchestrator


def test_synthetic_fixtures_contain_no_secret_or_token_shapes() -> None:
    fixture = (ROOT / "frontend/tests/conversational-rectification-e2e.test.ts").read_text(encoding="utf-8")
    forbidden = (
        r"sb-[a-z0-9]{16,}",
        r"eyj[a-z0-9_-]+\.[a-z0-9_-]+\.[a-z0-9_-]+",
        r"bearer\s+[a-z0-9._-]{20,}",
        r"supabase_service_role_key\s*=",
        r"openai_api_key\s*=",
        r"refresh_token",
        r"auth-token",
    )
    for pattern in forbidden:
        assert re.search(pattern, fixture, re.IGNORECASE) is None
