import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "frontend" / "supabase" / "migrations"
SCHEMA = MIGRATIONS / "20260720010000_conversational_rectification_schema.sql"
BILLING = MIGRATIONS / "20260720020000_conversational_rectification_billing.sql"
TRANSITIONS = MIGRATIONS / "20260720030000_conversational_rectification_transitions.sql"
LEGACY_IMPORT = MIGRATIONS / "20260721010000_conversational_legacy_import_projection.sql"
UNCONFIRMED_REFUND = MIGRATIONS / "20260722190000_refund_unconfirmed_rectification.sql"


def _normalized(path: Path) -> str:
    assert path.exists(), f"missing migration: {path.name}"
    return re.sub(r"\s+", " ", path.read_text(encoding="utf-8").lower()).strip()


def _function(sql: str, name: str) -> str:
    marker = f"create or replace function public.{name}"
    assert marker in sql
    body = sql.split(marker, 1)[1]
    return body.split("$$;", 1)[0]


def test_v3_schema_is_account_scoped_bounded_and_service_role_only() -> None:
    sql = _normalized(SCHEMA)
    assert "'conversational-evidence-v3'" in sql
    for column in (
        "revision_of_case_id uuid",
        "imported_from_case_id uuid",
        "baseline_active_time time without time zone",
        "pending_consultation_question text",
        "declared_birth_input jsonb not null",
    ):
        assert column in sql

    for table in (
        "birth_time_rectification_cases",
        "birth_time_rectification_turns",
        "birth_time_rectification_event_evidence",
        "birth_time_rectification_action_receipts",
        "birth_time_rectification_billing",
    ):
        assert f"revoke all on table public.{table} from public, anon, authenticated" in sql
        assert f"grant all on table public.{table} to service_role" in sql
        assert not re.search(
            rf"grant\s+.+?on\s+table\s+public\.{table}\s+to\s+(?:anon|authenticated)",
            sql,
        )

    assert "primary key (case_id, turn_version)" in sql
    assert "conversational_rectification_text_utf16_length(narrative) between 1 and 12000" in sql
    assert "conversational_rectification_text_utf16_length(raw_text) between 1 and 4000" in sql
    assert "date_precision in ('day', 'month', 'year', 'range', 'unknown')" in sql
    assert "extraction_status in ('clear', 'needs_clarification', 'corrected')" in sql
    assert "primary key (case_id, action_id)" in sql
    assert "state in ('reserved', 'charged', 'released', 'migration_waived')" in sql
    assert "chat_session" not in sql


def test_public_turn_projection_rejects_private_candidate_material() -> None:
    sql = _normalized(SCHEMA)
    for forbidden_key in (
        "candidateweights",
        "candidatescores",
        "partitionid",
        "rawmodeloutput",
        "systemprompt",
    ):
        assert f"$.**.{forbidden_key}" in sql
    assert "technical_receipt jsonb not null" in sql
    assert "candidate_result jsonb" not in _function(
        _normalized(TRANSITIONS), "conversational_rectification_case_projection"
    )


def test_fixed_fee_reserve_is_bounded_locked_and_exactly_once() -> None:
    sql = _normalized(BILLING)
    body = _function(sql, "reserve_conversational_rectification_fee")
    for invariant in (
        "p_price between 1 and 1000000",
        "pg_advisory_xact_lock",
        "p_user_id::text || ':' || p_action_id::text",
        "profile.id = p_user_id",
        "for update",
        "p_expected_version is distinct from 0",
        "v_receipt.request_fingerprint is distinct from v_fingerprint",
        "raise exception 'conversational_action_conflict'",
        "set credits = profile.credits - p_price",
        "transaction_type, amount, balance_after, request_id",
        "'reserve', -p_price",
    ):
        assert invariant in body
    assert "returns table ( success boolean, credits integer, billing_state text, error_code text )" in body
    # Reservation may inspect competing unfinished cases, but it must not
    # require or lock the not-yet-created target case.
    assert "select c.* into v_case" not in body
    assert "r.user_id = p_user_id" in body
    assert "r.action_id = v_receipt_action_id" in body


def test_complete_never_debits_and_release_refunds_at_most_once() -> None:
    sql = _normalized(BILLING)
    complete = _function(sql, "complete_conversational_rectification_fee")
    release = _function(sql, "release_conversational_rectification_fee")

    assert "set state = 'charged'" in complete
    assert "profile.credits -" not in complete
    assert "insert into public.credit_transactions" not in complete
    assert "v_billing.state = 'charged'" in complete

    assert "v_billing.state = 'released'" in release
    assert "set credits = profile.credits + v_billing.price" in release
    assert "'refund', v_billing.price" in release
    assert "v_billing.price is distinct from p_price" not in release
    assert "set state = 'released'" in release
    assert "if v_billing.state = 'charged'" in release
    assert "'already_charged'" in release


def test_range_only_completion_and_abandonment_refund_in_the_terminal_transaction() -> None:
    sql = _normalized(UNCONFIRMED_REFUND)
    refund = _function(sql, "conversational_rectification_refund_unconfirmed_case")
    completion = _function(sql, "complete_conversational_rectification_with_range")
    abandonment = _function(sql, "abandon_conversational_rectification_without_result")

    for invariant in (
        "v_case.status not in ('completed', 'abandoned')",
        "v_case.turn_state #>> '{candidate,status}' = 'confirmed'",
        "v_billing.state = 'charged'",
        "set credits = profile.credits + v_billing.price",
        "'refund', v_billing.price",
        "set state = 'released'",
    ):
        assert invariant in refund
    assert "save_conversational_rectification_turn" in completion
    assert "conversational_rectification_refund_unconfirmed_case" in completion
    assert "abandon_conversational_rectification_case" in abandonment
    assert "conversational_rectification_refund_unconfirmed_case" in abandonment
    assert "active_birth_time" not in sql


def test_release_terminalizes_a_created_reserved_case() -> None:
    release = _function(_normalized(BILLING), "release_conversational_rectification_fee")

    assert "update public.birth_time_rectification_cases" in release
    assert "set status = 'abandoned'" in release
    assert "status in ('starting', 'active', 'paused', 'confirming')" in release
    assert "turn_version = p_expected_version" in release


def test_all_billing_rpcs_are_service_role_only() -> None:
    sql = _normalized(BILLING)
    for name in (
        "reserve_conversational_rectification_fee",
        "complete_conversational_rectification_fee",
        "release_conversational_rectification_fee",
    ):
        assert f"revoke all on function public.{name}" in sql
        assert f"grant execute on function public.{name}" in sql
    assert not re.search(r"grant execute on function .+ to (?:anon|authenticated)", sql)


def test_fingerprints_do_not_depend_on_the_pgcrypto_extension_schema() -> None:
    sql = f"{_normalized(BILLING)} {_normalized(TRANSITIONS)}"
    assert "public.digest" not in sql
    assert "pg_catalog.sha256" in sql


def test_case_mutations_lock_owner_check_version_and_replay_exact_receipts() -> None:
    sql = _normalized(TRANSITIONS)
    for name in (
        "create_conversational_rectification_case",
        "save_conversational_rectification_turn",
        "pause_conversational_rectification_case",
        "abandon_conversational_rectification_case",
        "confirm_conversational_rectification_candidate",
        "import_legacy_conversational_rectification_case",
    ):
        body = _function(sql, name)
        assert "p_action_id" in body
        assert "p_expected_version" in body
        assert "request_fingerprint" in body
        assert "conversational_action_conflict" in body
        assert "for update" in body
        assert "p_user_id" in body
        assert "conversational_stale_turn" in body
        assert "insert into public.birth_time_rectification_action_receipts" in body
        assert f"revoke all on function public.{name}" in sql
        assert f"grant execute on function public.{name}" in sql


def test_case_creation_and_turn_save_are_atomic_public_history_units() -> None:
    sql = _normalized(TRANSITIONS)
    create = _function(sql, "create_conversational_rectification_case")
    save = _function(sql, "save_conversational_rectification_turn")

    assert "insert into public.birth_time_rectification_cases" in create
    assert "insert into public.birth_time_rectification_turns" in create
    assert "p_first_turn ->> 'journeyprotocol' is distinct from 'conversational-evidence-v3'" in create
    assert "active_birth_time" in create
    assert "update public.profiles" not in create
    assert "from public.birth_time_rectification_billing" in create
    assert "v_billing.state not in ('reserved', 'charged')" in create
    assert "declared_birth_input" in create
    assert "p_declared_birth_input" in create

    assert "insert into public.birth_time_rectification_turns" in save
    assert "insert into public.birth_time_rectification_event_evidence" in save
    assert "rawtext" in save
    assert "p_expected_version + 1" in save


def test_legacy_import_is_waived_without_changing_credits() -> None:
    body = _function(
        _normalized(TRANSITIONS), "import_legacy_conversational_rectification_case"
    )
    assert "imported_from_case_id" in body
    assert "'migration_waived'" in body
    assert "insert into public.birth_time_rectification_billing" in body
    assert "set credits = profile.credits -" not in body
    assert "'reserve', -" not in body
    assert "update public.birth_time_rectification_cases" not in body
    for preserved_profile_field in (
        "birth_time_clue",
        "country_code",
        "province_code",
        "city_code",
        "district_code",
        "latitude",
        "longitude",
        "timezone_offset",
    ):
        assert f"v_profile.{preserved_profile_field}" in body


def test_forward_legacy_import_projects_only_trusted_facts_into_v3() -> None:
    sql = _normalized(LEGACY_IMPORT)
    body = _function(sql, "import_legacy_conversational_rectification_case")
    projection = _function(
        sql, "conversational_rectification_project_legacy_event_evidence"
    )

    assert "drop function if exists public.import_legacy_conversational_rectification_case" in sql
    assert "birth_time_rectification_cases_one_v3_import_per_legacy" in sql
    assert "p_declared_birth_input jsonb" in body
    assert "p_evidence jsonb" in body
    assert "p_declared_birth_input is distinct from v_expected_declared" in body
    assert "p_evidence is distinct from v_expected_evidence" in body
    assert "conversational_rectification_valid_life_event_evidence_array" in body
    assert "insert into public.birth_time_rectification_event_evidence" in body
    assert "'{}'::jsonb, '{}'::jsonb, '[]'::jsonb, '{}'::jsonb" in body
    assert "v_legacy.questionnaire" not in body
    assert "v_legacy.answers" not in body
    assert "v_legacy.candidate_scan" not in body
    assert "update public.birth_time_rectification_cases" not in body
    assert "'migration_waived'" in body
    assert "set credits =" not in body
    assert "for update" in body
    assert "pg_advisory_xact_lock" in body
    assert "v_legacy.status not in ('assessing', 'rectifying', 'candidate', 'confirming')" in body
    assert "v_profile.rectification_case_id is distinct from p_legacy_case_id" in body
    assert "rectification_case_id = p_case_id" in body
    assert "rectification_case_id = p_legacy_case_id" in body
    assert "v_legacy.turn_version is distinct from p_expected_version" in body
    assert "current_date" in body

    assert "v_date < pg_catalog.to_char(p_birth_date, 'yyyy')" in projection
    assert "v_date > pg_catalog.to_char(p_as_of_date, 'yyyy')" in projection
    assert "when v_domain in ('finance', 'health_pressure') then 'other'" in projection
    assert "current_choice_question" not in projection
    assert "choice_answers" not in projection


def test_forward_legacy_import_rpc_is_service_role_only() -> None:
    sql = _normalized(LEGACY_IMPORT)
    assert "revoke all on function public.import_legacy_conversational_rectification_case" in sql
    assert "from public, anon, authenticated" in sql
    assert "grant execute on function public.import_legacy_conversational_rectification_case" in sql
    assert "to service_role" in sql


def test_imported_legacy_sources_are_immutable_history() -> None:
    sql = _normalized(TRANSITIONS)
    assert "create or replace function public.guard_imported_rectification_history" in sql
    assert "before update on public.birth_time_rectification_cases" in sql
    assert "conversational_imported_case_read_only" in sql


def test_mutations_require_a_paid_or_waived_case() -> None:
    sql = _normalized(TRANSITIONS)
    for name in (
        "save_conversational_rectification_turn",
        "pause_conversational_rectification_case",
        "abandon_conversational_rectification_case",
        "confirm_conversational_rectification_candidate",
    ):
        body = _function(sql, name)
        assert "from public.birth_time_rectification_billing" in body
        assert "v_billing.state not in ('charged', 'migration_waived')" in body


def test_account_resume_projection_contains_private_working_state_only_for_service_rpc() -> None:
    sql = _normalized(TRANSITIONS)
    load = _function(sql, "load_conversational_rectification_case")
    for key in (
        "declared_birth_input",
        "private_candidate",
        "event_evidence",
        "validation_receipts",
    ):
        assert f"'{key}'" in load
    assert "c.declared_birth_input" in load
    public_projection = _function(sql, "conversational_rectification_case_projection")
    assert "candidateweights" not in public_projection
    assert "private_candidate" not in public_projection


def test_historical_action_replay_is_owner_scoped_exact_bounded_and_read_only() -> None:
    schema = _normalized(SCHEMA)
    transitions = _normalized(TRANSITIONS)
    request = _function(schema, "conversational_rectification_valid_action_request")
    replay = _function(
        transitions, "replay_conversational_rectification_action"
    )

    assert "'commandfingerprint'" in request
    assert "requestfingerprint" in request
    assert "^[0-9a-f]{64}$" in request
    for invariant in (
        "r.user_id = p_user_id",
        "r.case_id = p_case_id",
        "r.action_id = p_action_id",
        "v_receipt.action_kind is distinct from p_action_kind",
        "v_receipt.expected_turn_version is distinct from p_expected_version",
        "not (v_receipt.request ? 'commandfingerprint')",
        "v_receipt.request ->> 'commandfingerprint' is distinct from p_command_fingerprint",
        "return v_receipt.response",
        "raise exception 'conversational_action_conflict'",
    ):
        assert invariant in replay
    assert "insert into" not in replay
    assert "update public." not in replay
    assert "delete from" not in replay
    assert (
        "revoke all on function public.replay_conversational_rectification_action"
        in transitions
    )
    assert (
        "grant execute on function public.replay_conversational_rectification_action"
        in transitions
    )
    assert not re.search(
        r"grant execute on function public\.replay_conversational_rectification_action"
        r".+?to (?:anon|authenticated)",
        transitions,
    )

    for name in (
        "save_conversational_rectification_turn",
        "pause_conversational_rectification_case",
        "abandon_conversational_rectification_case",
        "confirm_conversational_rectification_candidate",
    ):
        body = _function(transitions, name)
        assert "p_command_fingerprint text" in body
        assert "p_command_fingerprint !~ '^[0-9a-f]{64}$'" in body
        assert "'commandfingerprint', p_command_fingerprint" in body
        assert (
            "case when v_receipt.request ? 'commandfingerprint' then "
            "v_receipt.request ->> 'commandfingerprint' is distinct from "
            "p_command_fingerprint else v_receipt.request_fingerprint is "
            "distinct from v_fingerprint end"
        ) in body


def test_start_identity_and_account_concurrency_are_server_guarded() -> None:
    schema = _normalized(SCHEMA)
    transitions = _normalized(TRANSITIONS)
    assert "unique (user_id, reserve_action_id)" in schema
    assert "on public.birth_time_rectification_action_receipts (user_id, action_id)" in schema
    assert "where action_kind = 'reserve_fee'" in schema
    assert "conversational_rectification_billing_receipt_action_id" in schema
    reserve = _function(_normalized(BILLING), "reserve_conversational_rectification_fee")
    assert "p_case_id is distinct from p_action_id" in reserve
    create = _function(transitions, "create_conversational_rectification_case")
    assert "p_case_id is distinct from p_action_id" in create
    assert "conversational-rectification-case" in create
    assert "status in ('starting', 'active', 'paused', 'confirming')" in create
    assert "raise exception 'conversational_action_conflict'" in create


def test_new_account_start_recovers_a_committed_pre_case_reservation() -> None:
    billing = _normalized(BILLING)
    reserve = _function(billing, "reserve_conversational_rectification_fee")
    recovery = _function(
        billing, "recover_conversational_rectification_orphan_reservations"
    )

    assert "orphan_billing.state = 'reserved'" in recovery
    assert "orphan_case.id is null" in recovery
    assert "set credits = profile.credits + v_orphan.price" in recovery
    assert "'refund', v_orphan.price" in recovery
    assert "set state = 'released'" in recovery
    assert "'recover_fee'" in recovery
    assert "v_orphan.case_id" in recovery
    assert "recover_conversational_rectification_orphan_reservations" in reserve
    assert reserve.index("recover_conversational_rectification_orphan_reservations") < reserve.index(
        "set credits = profile.credits - p_price"
    )


def test_durable_json_columns_have_byte_and_field_shape_guards() -> None:
    sql = _normalized(SCHEMA)
    for validator in (
        "conversational_rectification_valid_candidate",
        "conversational_rectification_valid_technical_receipt",
        "conversational_rectification_valid_evidence_recap",
        "conversational_rectification_valid_validation_receipt",
        "conversational_rectification_valid_private_candidate",
        "conversational_rectification_valid_action_request",
        "conversational_rectification_valid_action_response",
    ):
        assert f"create or replace function public.{validator}" in sql
        assert "octet_length" in _function(sql, validator)

    assert "request jsonb not null" in sql
    assert "conversational_rectification_valid_candidate(candidate)" in sql
    assert "conversational_rectification_valid_technical_receipt(technical_receipt)" in sql
    assert "conversational_rectification_valid_evidence_recap(evidence_recap)" in sql
    assert "conversational_rectification_valid_validation_receipt(output_validation_receipt)" in sql
    assert "conversational_rectification_valid_action_request(request)" in sql
    assert "conversational_rectification_valid_action_response(response, action_kind)" in sql
    assert "conversational_rectification_valid_private_candidate(candidate_result)" in sql


def test_durable_json_numbers_and_evidence_recap_share_postgres_bounds() -> None:
    sql = _normalized(SCHEMA)

    assert "create or replace function public.conversational_rectification_numbers_are_stable" in sql
    numeric = _function(sql, "conversational_rectification_numbers_are_stable")
    for invariant in (
        "abs(v_number) <= 9007199254740991",
        "abs(v_number) between 0.000001 and 1000000",
        "v_number = pg_catalog.trunc(v_number, 6)",
    ):
        assert invariant in numeric
    for validator in (
        "conversational_rectification_valid_declared_birth_input",
        "conversational_rectification_valid_private_candidate",
        "conversational_rectification_valid_public_turn",
        "conversational_rectification_valid_action_request",
        "conversational_rectification_valid_action_response",
    ):
        assert "conversational_rectification_numbers_are_stable" in _function(sql, validator)
    recap = _function(sql, "conversational_rectification_valid_evidence_recap")
    assert "octet_length(p_value::text) <= 24576" in recap


def test_sql_json_strings_and_enum_arrays_reject_null_and_non_string_values() -> None:
    sql = _normalized(SCHEMA)
    assert "jsonb_array_elements_text" not in sql

    candidate = _function(sql, "conversational_rectification_valid_candidate")
    assert "jsonb_typeof(p_value -> 'status') is distinct from 'string'" in candidate

    request = _function(sql, "conversational_rectification_valid_evidence_request")
    assert "jsonb_typeof(p_value -> 'dateprecision') = 'string'" in request
    assert "jsonb_array_elements(p_value -> 'domains')" in request
    assert "jsonb_typeof(domain) is distinct from 'string'" in request

    actions = _function(sql, "conversational_rectification_valid_actions")
    assert "jsonb_array_elements(p_value)" in actions
    assert "jsonb_typeof(action) is distinct from 'string'" in actions

    private = _function(sql, "conversational_rectification_valid_private_candidate")
    assert "jsonb_array_elements(p_value -> 'suggesteddomains')" in private
    assert "jsonb_typeof(domain) is distinct from 'string'" in private

    public_turn = _function(sql, "conversational_rectification_valid_public_turn")
    for key in ("caseid", "journeyprotocol", "status"):
        assert f"jsonb_typeof(p_value -> '{key}') = 'string'" in public_turn


def test_sql_uuid_text_matches_zod_canonical_hyphenated_syntax_at_all_json_boundaries() -> None:
    sql = _normalized(SCHEMA)
    uuid = _function(sql, "conversational_rectification_valid_uuid_text")
    assert "^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$" in uuid
    assert "perform p_value::uuid" in uuid

    for validator in (
        "conversational_rectification_valid_evidence_recap",
        "conversational_rectification_valid_life_event_evidence",
        "conversational_rectification_valid_private_candidate",
        "conversational_rectification_valid_public_turn",
        "conversational_rectification_valid_action_request",
        "conversational_rectification_valid_action_response",
    ):
        assert "conversational_rectification_valid_uuid_text" in _function(sql, validator)


def test_sql_nonblank_and_maximum_text_rules_match_ecmascript_and_utf16() -> None:
    sql = _normalized(SCHEMA)
    assert "create or replace function public.conversational_rectification_text_utf16_length" in sql

    for validator, minimum_nonblank_calls, minimum_utf16_calls in (
        ("conversational_rectification_text_array_is_bounded", 1, 1),
        ("conversational_rectification_valid_technical_receipt", 1, 1),
        ("conversational_rectification_valid_evidence_recap", 2, 2),
        ("conversational_rectification_valid_validation_receipt", 2, 3),
        ("conversational_rectification_valid_life_event_evidence", 3, 3),
        ("conversational_rectification_valid_private_candidate", 2, 2),
        ("conversational_rectification_valid_declared_birth_input", 2, 2),
        ("conversational_rectification_valid_public_turn", 2, 2),
        ("conversational_rectification_valid_action_response", 2, 2),
    ):
        body = _function(sql, validator)
        assert body.count("conversational_rectification_text_is_nonblank") >= minimum_nonblank_calls
        assert body.count("conversational_rectification_text_utf16_length") >= minimum_utf16_calls

    for durable_column in ("narrative", "raw_text", "event_summary", "date_value"):
        assert f"conversational_rectification_text_utf16_length({durable_column})" in sql


def test_life_event_evidence_is_strictly_validated_before_insert() -> None:
    schema = _normalized(SCHEMA)
    transitions = _normalized(TRANSITIONS)
    validator = _function(schema, "conversational_rectification_valid_life_event_evidence")
    save = _function(transitions, "save_conversational_rectification_turn")

    for invariant in (
        "conversational_rectification_has_only_keys",
        "jsonb_typeof(p_value -> 'id')",
        "conversational_rectification_valid_uuid_text",
        "p_value ->> 'id' !~* '^[0-9a-f]{8}-",
        "conversational_rectification_text_is_nonblank( p_value ->> 'rawtext'",
        "conversational_rectification_text_is_nonblank( p_value ->> 'eventsummary'",
        "conversational_rectification_text_is_nonblank( p_value ->> 'datevalue'",
        "jsonb_typeof(p_value -> 'scoreable')",
    ):
        assert invariant in validator
    for key in (
        "id",
        "rawtext",
        "domain",
        "eventsummary",
        "datevalue",
        "dateprecision",
        "extractionstatus",
        "scoreable",
    ):
        assert f"'{key}'" in validator
    evidence_array_validator = "conversational_rectification_valid_life_event_evidence_array"
    assert evidence_array_validator in save
    assert save.index(evidence_array_validator) < save.index(
        "insert into public.birth_time_rectification_event_evidence"
    )
    assert "coalesce((item ->> 'scoreable')::boolean, false)" not in save
    assert "nullif(item ->> 'datevalue', '')" not in save


def test_evidence_correction_lineage_is_bounded_projected_and_validated_atomically() -> None:
    schema = _normalized(SCHEMA)
    transitions = _normalized(TRANSITIONS)
    validator = _function(schema, "conversational_rectification_valid_life_event_evidence")
    load = _function(transitions, "load_conversational_rectification_case")
    limits = _function(transitions, "conversational_rectification_case_fits_load_limits")
    save = _function(transitions, "save_conversational_rectification_turn")

    assert "corrects_evidence_ids uuid[] not null default '{}'::uuid[]" in schema
    assert "'correctsevidenceids'" in validator
    assert "jsonb_array_length(p_value -> 'correctsevidenceids') > 1" in validator
    assert "p_value ->> 'extractionstatus' = 'corrected'" in validator
    assert "p_value ->> 'extractionstatus' = 'clear'" in validator
    assert "'correctsevidenceids', pg_catalog.to_jsonb(evidence.corrects_evidence_ids)" in load
    assert "'correctsevidenceids', pg_catalog.to_jsonb(evidence.corrects_evidence_ids)" in limits
    assert "corrects_evidence_ids" in save
    assert "item -> 'correctsevidenceids'" in save
    assert "pg_catalog.unnest( evidence.corrects_evidence_ids )" in save
    assert save.index("pg_catalog.unnest( evidence.corrects_evidence_ids )") < save.index(
        "insert into public.birth_time_rectification_event_evidence"
    )
    assert "where evidence.case_id = p_case_id" in save
    assert "group by correction.value::uuid having pg_catalog.count(*) > 1" in save
    assert save.index("group by correction.value::uuid having pg_catalog.count(*) > 1") < save.index(
        "insert into public.birth_time_rectification_turns"
    )


def test_case_mutations_enforce_cumulative_load_limits_under_the_case_lock() -> None:
    transitions = _normalized(TRANSITIONS)
    helper = _function(transitions, "conversational_rectification_case_fits_load_limits")

    assert "count(*)" in helper
    assert "<= 2000" in helper
    assert "octet_length(v_projection::text) <= 4194304" in helper
    for name in (
        "save_conversational_rectification_turn",
        "pause_conversational_rectification_case",
        "abandon_conversational_rectification_case",
        "confirm_conversational_rectification_candidate",
    ):
        body = _function(transitions, name)
        assert body.index("for update") < body.index(
            "conversational_rectification_case_fits_load_limits"
        )
        assert body.index("conversational_rectification_case_fits_load_limits") < body.index(
            "insert into public.birth_time_rectification_turns"
        )


def test_legacy_import_recovers_orphan_reservations_without_a_paid_start() -> None:
    billing = _normalized(BILLING)
    transitions = _normalized(TRANSITIONS)
    recovery = _function(
        billing, "recover_conversational_rectification_orphan_reservations"
    )
    imported = _function(
        transitions, "import_legacy_conversational_rectification_case"
    )

    for invariant in (
        "conversational-rectification-case",
        "for update",
        "orphan_billing.state = 'reserved'",
        "orphan_case.id is null",
        "set credits = profile.credits + v_orphan.price",
        "'refund', v_orphan.price",
        "set state = 'released'",
        "'recover_fee'",
    ):
        assert invariant in recovery
    assert "recover_conversational_rectification_orphan_reservations" in imported
    assert imported.index("recover_conversational_rectification_orphan_reservations") < imported.index(
        "'migration_waived'"
    )
    assert "set credits = profile.credits -" not in imported


def test_declared_birth_input_is_strict_source_aware_and_location_complete() -> None:
    sql = _normalized(SCHEMA)
    body = _function(sql, "conversational_rectification_valid_declared_birth_input")

    for invariant in (
        "octet_length",
        "birthdate",
        "birthtimeclue",
        "birthplace",
        "timezoneoffset",
        "latitude",
        "longitude",
        "citycode",
        "reportedtime",
        "reportedperiod",
        "uncertaintybeforeminutes",
        "uncertaintyafterminutes",
        "hospital_record",
        "family_exact",
        "approximate",
        "period_only",
        "unknown",
        "legacy_import",
    ):
        assert invariant in body
    assert "conversational_rectification_has_only_keys" in body
    assert "conversational_rectification_valid_declared_birth_input(declared_birth_input)" in sql


def test_one_public_start_action_has_noncolliding_internal_billing_receipts() -> None:
    billing = _normalized(BILLING)
    for name, kind in (
        ("reserve_conversational_rectification_fee", "reserve_fee"),
        ("complete_conversational_rectification_fee", "complete_fee"),
        ("release_conversational_rectification_fee", "release_fee"),
    ):
        body = _function(billing, name)
        assert "conversational_rectification_billing_receipt_action_id" in body
        assert f"'{kind}'" in body
        assert "r.action_id = v_receipt_action_id" in body
        assert "p_case_id, v_receipt_action_id, p_user_id" in body

    create = _function(
        _normalized(TRANSITIONS), "create_conversational_rectification_case"
    )
    assert "p_case_id, p_action_id, p_user_id, 'create'" in create


def test_validation_receipts_are_private_parameters_not_public_turn_fields() -> None:
    sql = _normalized(TRANSITIONS)
    for name in (
        "create_conversational_rectification_case",
        "save_conversational_rectification_turn",
        "pause_conversational_rectification_case",
        "abandon_conversational_rectification_case",
        "confirm_conversational_rectification_candidate",
        "import_legacy_conversational_rectification_case",
    ):
        body = _function(sql, name)
        assert "p_validation_receipt jsonb" in body
        assert "p_validation_receipt" in body.split(
            "insert into public.birth_time_rectification_turns", 1
        )[1]


def test_only_atomic_confirm_changes_the_active_birth_time() -> None:
    sql = _normalized(TRANSITIONS)
    confirm = _function(sql, "confirm_conversational_rectification_candidate")
    for invariant in (
        "v_case.status is distinct from 'confirming'",
        "v_case.candidate_result_id is distinct from p_result_id",
        "representativetime",
        "p_time",
        "calculationversion",
        "p_calculation_version",
        "update public.profiles",
        "active_birth_time = p_time",
        "birth_time_status = 'confirmed'",
        "set status = 'completed'",
        "pending_consultation_question",
        "extract(second from p_time) is distinct from 0",
    ):
        assert invariant in confirm

    without_confirm = sql.replace(confirm, "")
    assert "active_birth_time =" not in without_confirm


def test_transition_rpcs_are_service_role_only() -> None:
    sql = _normalized(TRANSITIONS)
    assert not re.search(r"grant execute on function .+ to (?:anon|authenticated)", sql)
    assert not re.search(r"grant\s+.+?on\s+table\s+.+?to\s+(?:anon|authenticated)", sql)
