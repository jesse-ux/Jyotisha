import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = ROOT / "frontend" / "supabase" / "migrations"
PG14_BIN_CANDIDATES = (
    Path(os.environ.get("PG14_BIN", "/path/that/does/not/exist")),
    Path("/opt/homebrew/opt/postgresql@14/bin"),
    Path("/usr/local/opt/postgresql@14/bin"),
)


def _postgres_14_bin() -> Path | None:
    for candidate in PG14_BIN_CANDIDATES:
        initdb = candidate / "initdb"
        if not initdb.is_file():
            continue
        version = subprocess.run(
            [str(initdb), "--version"],
            check=False,
            capture_output=True,
            text=True,
        )
        if version.returncode == 0 and " 14." in version.stdout:
            return candidate
    return None


PG14_BIN = _postgres_14_bin()
pytestmark = pytest.mark.skipif(PG14_BIN is None, reason="PostgreSQL 14 binaries are unavailable")


@dataclass(frozen=True)
class PgDatabase:
    bin_dir: Path
    socket_dir: Path
    port: int

    def command(self, *extra: str) -> list[str]:
        return [
            str(self.bin_dir / "psql"),
            "-X",
            "-v",
            "ON_ERROR_STOP=1",
            "-h",
            str(self.socket_dir),
            "-p",
            str(self.port),
            "-U",
            "postgres",
            "-d",
            "postgres",
            *extra,
        ]

    def sql(self, statement: str) -> str:
        completed = subprocess.run(
            self.command("-A", "-t", "-q", "-c", statement),
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
        )
        assert completed.returncode == 0, completed.stderr
        return completed.stdout.strip()

    def rejects(self, statement: str) -> bool:
        completed = subprocess.run(
            self.command("-A", "-t", "-q", "-c", statement),
            check=False,
            capture_output=True,
            text=True,
            errors="replace",
        )
        return completed.returncode != 0


@pytest.fixture(scope="module")
def pg14_database() -> PgDatabase:
    assert PG14_BIN is not None
    with tempfile.TemporaryDirectory(
        prefix="rectification-pg14-",
        dir="/private/tmp",
    ) as temporary_root:
        root = Path(temporary_root)
        data_dir = root / "data"
        socket_dir = root / "socket"
        socket_dir.mkdir()
        port = 55439

        init = subprocess.run(
            [
                str(PG14_BIN / "initdb"),
                "-D",
                str(data_dir),
                "-A",
                "trust",
                "-U",
                "postgres",
                "--no-locale",
                "-E",
                "UTF8",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert init.returncode == 0, f"{init.stdout}\n{init.stderr}"
        start = subprocess.run(
            [
                str(PG14_BIN / "pg_ctl"),
                "-D",
                str(data_dir),
                "-l",
                str(root / "postgres.log"),
                "-o",
                f"-F -k {socket_dir} -p {port} -c listen_addresses=''",
                "-w",
                "start",
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        assert start.returncode == 0, f"{start.stdout}\n{start.stderr}"

        database = PgDatabase(PG14_BIN, socket_dir, port)
        try:
            database.sql(
            """
            create role anon nologin;
            create role authenticated nologin;
            create role service_role nologin;
            create schema auth;
            create table auth.users (
              id uuid primary key,
              email text
            );
            create function auth.uid() returns uuid
              language sql stable set search_path = ''
              as 'select null::uuid';
            create function auth.jwt() returns jsonb
              language sql stable set search_path = ''
              as 'select ''{}''::jsonb';
            """
            )
            for migration in sorted(MIGRATIONS.glob("*.sql")):
                applied = subprocess.run(
                    database.command("-q", "-f", str(migration)),
                    check=False,
                    capture_output=True,
                    text=True,
                )
                assert applied.returncode == 0, f"{migration.name}:\n{applied.stderr}"
            yield database
        finally:
            subprocess.run(
                [str(PG14_BIN / "pg_ctl"), "-D", str(data_dir), "-m", "fast", "-w", "stop"],
                check=False,
                capture_output=True,
                text=True,
            )


def _jsonb(value: object) -> str:
    encoded = json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("'", "''")
    return f"'{encoded}'::jsonb"


def _text(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _create_user(database: PgDatabase, user_id: str, credits: int = 20) -> None:
    database.sql(
        f"""
        insert into auth.users (id, email)
        values ('{user_id}'::uuid, 'synthetic@example.invalid');
        update public.profiles
        set credits = {credits},
            birth_date = '1990-01-01',
            active_birth_time = '04:58',
            birth_time = '04:58',
            country_code = 'TW',
            province_code = 'TPE',
            city_code = 'TPE-CITY',
            district_code = 'DAAN',
            latitude = 25.0268,
            longitude = 121.5434,
            timezone_offset = 8
        where id = '{user_id}'::uuid;
        """
    )


def _reserve(database: PgDatabase, user_id: str, action_id: str, price: int = 3) -> dict[str, object]:
    result = database.sql(
        f"""
        select row_to_json(reservation)::text
        from public.reserve_conversational_rectification_fee(
          '{user_id}'::uuid,
          '{action_id}'::uuid,
          0,
          '{action_id}'::uuid,
          {price}
        ) reservation;
        """
    )
    return json.loads(result)


def _valid_declared_birth_input() -> dict[str, object]:
    return {
        "birthDate": "1990-01-01",
        "reportedTime": "05:20",
        "source": "approximate",
        "birthTimeClue": "synthetic dawn clue",
        "uncertaintyBeforeMinutes": 30,
        "uncertaintyAfterMinutes": 30,
        "birthplace": {
            "countryCode": "TW",
            "provinceCode": "TPE",
            "cityCode": "TPE-CITY",
            "districtCode": "DAAN",
            "latitude": 25.0268,
            "longitude": 121.5434,
            "timezoneOffset": 8,
        },
    }


def _valid_turn(case_id: str) -> dict[str, object]:
    return {
        "caseId": case_id,
        "journeyProtocol": "conversational-evidence-v3",
        "status": "active",
        "turnVersion": 0,
        "narrative": "Synthetic public narrative.",
        "candidate": {
            "status": "pending_validation",
            "representativeTime": "05:21",
            "rangeStart": "05:10",
            "rangeEnd": "05:30",
        },
        "technicalReceipt": {
            "calculationVersion": "rectification-v3.1",
            "stableLayers": ["D1"],
            "sensitiveLayers": ["D9"],
            "candidateDifferenceRefs": ["difference-1"],
        },
        "evidenceRequest": {
            "domains": ["career", "relocation"],
            "datePrecision": "month_preferred",
            "freeTextAllowed": True,
        },
        "evidenceRecap": [],
        "actions": ["answer", "pause", "abandon"],
        "pendingConsultationQuestion": None,
    }


def _valid_private_candidate() -> dict[str, object]:
    return {
        "resultId": "00000000-0000-4000-8000-000000000991",
        "representativeTime": "05:21",
        "rangeStart": "05:10",
        "rangeEnd": "05:30",
        "calculationVersion": "rectification-v3.1",
        "candidateWeights": [0.6, 0.4],
        "candidateModelRefs": ["model-1"],
        "suggestedDomains": ["career", "relocation"],
    }


def _create_case(
    database: PgDatabase,
    user_id: str,
    action_id: str,
    declared_birth_input: dict[str, object],
    private_candidate: dict[str, object] | None = None,
) -> str:
    return database.sql(
        f"""
        select public.create_conversational_rectification_case(
          '{user_id}'::uuid,
          '{action_id}'::uuid,
          0,
          '{action_id}'::uuid,
          null,
          null,
          {_jsonb(declared_birth_input)},
          {_jsonb(_valid_turn(action_id))},
          {_jsonb({"modelId": "synthetic-model", "schemaValidated": True})},
          {_jsonb(private_candidate or _valid_private_candidate())}
        )::text;
        """
    )


def _complete(database: PgDatabase, user_id: str, action_id: str, version: int = 0) -> dict[str, object]:
    result = database.sql(
        f"""
        select row_to_json(completion)::text
        from public.complete_conversational_rectification_fee(
          '{user_id}'::uuid,
          '{action_id}'::uuid,
          {version},
          '{action_id}'::uuid
        ) completion;
        """
    )
    return json.loads(result)


def _save_statement(
    user_id: str,
    case_id: str,
    expected_version: int,
    action_id: str,
    evidence: list[dict[str, object]],
    *,
    turn: dict[str, object] | None = None,
    validation_receipt: dict[str, object] | None = None,
    private_candidate: dict[str, object] | None = None,
) -> str:
    next_turn = turn or {
        **_valid_turn(case_id),
        "turnVersion": expected_version + 1,
    }
    return f"""
    select public.save_conversational_rectification_turn(
      '{user_id}'::uuid,
      '{case_id}'::uuid,
      {expected_version},
      '{action_id}'::uuid,
      {_jsonb(next_turn)},
      {_jsonb(evidence)},
      {_jsonb(validation_receipt or {"modelId": "synthetic-model", "schemaValidated": True})},
      {_jsonb(private_candidate or _valid_private_candidate())}
    )::text;
    """


def _create_legacy_case(database: PgDatabase, user_id: str, legacy_case_id: str) -> None:
    database.sql(
        f"""
        insert into public.birth_time_rectification_cases (
          id, user_id, status, reported_date, reported_time, source,
          uncertainty_before_minutes, uncertainty_after_minutes, journey_protocol
        ) values (
          '{legacy_case_id}'::uuid, '{user_id}'::uuid, 'rectifying',
          '1990-01-01', '05:20', 'legacy_import', 0, 0, 'legacy-guided-v1'
        );
        """
    )


def test_committed_pre_case_reservation_is_recovered_by_a_fresh_account_action(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000000901"
    lost_action = "00000000-0000-4000-8000-000000000902"
    fresh_action = "00000000-0000-4000-8000-000000000903"
    _create_user(pg14_database, user_id, credits=10)

    first = _reserve(pg14_database, user_id, lost_action)
    assert first == {
        "success": True,
        "credits": 7,
        "billing_state": "reserved",
        "error_code": None,
    }
    assert pg14_database.sql(
        f"select public.load_conversational_rectification_case('{user_id}'::uuid, null) is null"
    ) == "t"

    recovered = _reserve(pg14_database, user_id, fresh_action)
    assert recovered == first
    accounting = json.loads(pg14_database.sql(
        f"""
        select jsonb_build_object(
          'credits', profile.credits,
          'oldState', old_billing.state,
          'newState', new_billing.state,
          'reserveCount', count(*) filter (where tx.transaction_type = 'reserve'),
          'refundCount', count(*) filter (where tx.transaction_type = 'refund')
        )::text
        from public.profiles profile
        join public.birth_time_rectification_billing old_billing
          on old_billing.case_id = '{lost_action}'::uuid
        join public.birth_time_rectification_billing new_billing
          on new_billing.case_id = '{fresh_action}'::uuid
        left join public.credit_transactions tx on tx.user_id = profile.id
        where profile.id = '{user_id}'::uuid
        group by profile.credits, old_billing.state, new_billing.state;
        """
    ))
    assert accounting == {
        "credits": 7,
        "oldState": "released",
        "newState": "reserved",
        "reserveCount": 2,
        "refundCount": 1,
    }

    assert _reserve(pg14_database, user_id, lost_action) == first
    assert pg14_database.sql(
        f"select count(*) from public.credit_transactions where user_id = '{user_id}'::uuid"
    ) == "3"


@pytest.mark.parametrize(
    ("user_id", "action_id", "declared"),
    [
        (
            "00000000-0000-4000-8000-000000000911",
            "00000000-0000-4000-8000-000000000912",
            {
                "birthDate": "1990-01-01",
                "reportedTime": "05:20",
                "source": "approximate",
                "birthTimeClue": None,
                "uncertaintyBeforeMinutes": 30,
                "uncertaintyAfterMinutes": 30,
            },
        ),
        (
            "00000000-0000-4000-8000-000000000921",
            "00000000-0000-4000-8000-000000000922",
            {**_valid_declared_birth_input(), "unknownField": True},
        ),
        (
            "00000000-0000-4000-8000-000000000931",
            "00000000-0000-4000-8000-000000000932",
            {
                **_valid_declared_birth_input(),
                "uncertaintyAfterMinutes": 60,
                "birthplace": {**_valid_declared_birth_input()["birthplace"], "latitude": 91},
            },
        ),
    ],
)
def test_invalid_declared_birth_input_is_rejected_before_case_persistence(
    pg14_database: PgDatabase,
    user_id: str,
    action_id: str,
    declared: dict[str, object],
) -> None:
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, action_id)
    assert pg14_database.rejects(
        f"""
        select public.create_conversational_rectification_case(
          '{user_id}'::uuid, '{action_id}'::uuid, 0, '{action_id}'::uuid,
          null, null, {_jsonb(declared)}, {_jsonb(_valid_turn(action_id))},
          {_jsonb({"modelId": "synthetic-model", "schemaValidated": True})},
          {_jsonb(_valid_private_candidate())}
        );
        """
    )
    assert pg14_database.sql(
        f"select count(*) from public.birth_time_rectification_cases where id = '{action_id}'::uuid"
    ) == "0"


def test_valid_declared_birth_input_round_trips_across_account_load(pg14_database: PgDatabase) -> None:
    user_id = "00000000-0000-4000-8000-000000000941"
    action_id = "00000000-0000-4000-8000-000000000942"
    declared = _valid_declared_birth_input()
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, action_id)
    _create_case(pg14_database, user_id, action_id, declared)

    loaded = json.loads(pg14_database.sql(
        f"select public.load_conversational_rectification_case('{user_id}'::uuid, null)::text"
    ))
    assert loaded["declared_birth_input"] == declared


def test_database_rejects_oversize_or_unknown_durable_json(pg14_database: PgDatabase) -> None:
    user_id = "00000000-0000-4000-8000-000000000951"
    action_id = "00000000-0000-4000-8000-000000000952"
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, action_id)
    _create_case(pg14_database, user_id, action_id, _valid_declared_birth_input())

    base_turn = _valid_turn(action_id)
    boundary_turn = {
        **base_turn,
        "turnVersion": 1,
        "technicalReceipt": {
            **base_turn["technicalReceipt"],
            "calculationVersion": "v" * 80,
        },
        "evidenceRecap": [
            {
                "id": "00000000-0000-4000-8000-000000000953",
                "summary": "事" * 1_000,
                "dateLabel": "d" * 80,
            }
        ],
    }
    pg14_database.sql(
        f"""
        begin;
        insert into public.birth_time_rectification_turns (
          case_id, turn_version, narrative, candidate, technical_receipt,
          evidence_request, evidence_recap, actions, output_validation_receipt
        ) values (
          '{action_id}'::uuid, 1, {_text(str(boundary_turn['narrative']))},
          {_jsonb(boundary_turn['candidate'])}, {_jsonb(boundary_turn['technicalReceipt'])},
          {_jsonb(boundary_turn['evidenceRequest'])}, {_jsonb(boundary_turn['evidenceRecap'])},
          {_jsonb(boundary_turn['actions'])},
          {_jsonb({'modelId': 'm' * 120, 'schemaValidated': True})}
        );
        update public.birth_time_rectification_cases
        set candidate_result = {_jsonb({
            **_valid_private_candidate(),
            'candidateWeights': [0.5] * 1_440,
        })}
        where id = '{action_id}'::uuid;
        rollback;
        """
    )
    invalid_turns = [
        {**base_turn, "turnVersion": 1, "candidate": {**base_turn["candidate"], "extra": True}},
        {
            **base_turn,
            "turnVersion": 1,
            "technicalReceipt": {
                **base_turn["technicalReceipt"],
                "calculationVersion": "v" * 81,
            },
        },
        {
            **base_turn,
            "turnVersion": 1,
            "technicalReceipt": {
                **base_turn["technicalReceipt"],
                "calculationVersion": "v" * 80 + " ",
            },
        },
        {
            **base_turn,
            "turnVersion": 1,
            "evidenceRecap": [{
                "id": "00000000-0000-4000-8000-000000000953",
                "summary": "事" * 1_001,
                "dateLabel": "2020-01",
            }],
        },
    ]
    for turn in invalid_turns:
        assert pg14_database.rejects(
            f"""
            begin;
            insert into public.birth_time_rectification_turns (
              case_id, turn_version, narrative, candidate, technical_receipt,
              evidence_request, evidence_recap, actions, output_validation_receipt
            ) values (
              '{action_id}'::uuid, 1, {_text(str(turn['narrative']))},
              {_jsonb(turn['candidate'])}, {_jsonb(turn['technicalReceipt'])},
              {_jsonb(turn['evidenceRequest'])}, {_jsonb(turn['evidenceRecap'])},
              {_jsonb(turn['actions'])},
              {_jsonb({"modelId": "synthetic-model", "schemaValidated": True})}
            );
            rollback;
            """
        )

    assert pg14_database.rejects(
        f"""
        update public.birth_time_rectification_cases
        set candidate_result = {_jsonb({
            **_valid_private_candidate(),
            "candidateWeights": [0.5] * 1_441,
        })}
        where id = '{action_id}'::uuid;
        """
    )
    assert pg14_database.rejects(
        f"""
        begin;
        insert into public.birth_time_rectification_turns (
          case_id, turn_version, narrative, candidate, technical_receipt,
          evidence_request, evidence_recap, actions, output_validation_receipt
        ) values (
          '{action_id}'::uuid, 1, 'Synthetic narrative',
          {_jsonb(base_turn['candidate'])}, {_jsonb(base_turn['technicalReceipt'])},
          {_jsonb(base_turn['evidenceRequest'])}, '[]'::jsonb,
          {_jsonb(base_turn['actions'])},
          {_jsonb({"modelId": "m" * 121, "schemaValidated": True})}
        );
        rollback;
        """
    )
    assert pg14_database.sql(
        f"""
        select public.conversational_rectification_valid_action_response(
          {_jsonb({
              "success": True,
              "credits": 7,
              "billing_state": "reserved",
              "error_code": None,
              "extra": "x" * 70_000,
          })},
          'reserve_fee'
        )::text;
        """
    ) == "false"
    assert pg14_database.rejects(
        f"""
        update public.birth_time_rectification_action_receipts
        set request = request - 'caseId'
        where user_id = '{user_id}'::uuid and action_kind = 'reserve_fee';
        """
    )
    assert pg14_database.rejects(
        f"""
        update public.birth_time_rectification_action_receipts
        set response = pg_catalog.jsonb_set(
          response, '{{error_code}}', {_jsonb('e' * 81)}, true
        )
        where user_id = '{user_id}'::uuid and action_kind = 'reserve_fee';
        """
    )


def test_postgres_uses_the_shared_stable_numeric_boundary_vectors(
    pg14_database: PgDatabase,
) -> None:
    stable_vector = {
        "zero": 0,
        "minFraction": 0.000001,
        "ieeeRoundingBoundary": 1.000001,
        "decimal": 0.123456,
        "maxSafe": 9_007_199_254_740_991,
    }
    numeric_result = pg14_database.sql(
        f"""
        select pg_catalog.jsonb_build_object(
          'valid', public.conversational_rectification_numbers_are_stable({_jsonb(stable_vector)}),
          'bytes', pg_catalog.octet_length(({_jsonb(stable_vector)})::text)
        )::text;
        """
    )
    assert json.loads(numeric_result) == {"valid": True, "bytes": 120}

    for invalid in (
        {"nested": [{"score": 1e-7}]},
        {"nested": [{"score": 1e-100}]},
        {"nested": [{"score": 0.0000012}]},
        {"nested": [{"score": 0.1234567}]},
        {"nested": [{"score": 1_000_000.000001}]},
        {"nested": [{"score": 9_007_199_254_740_992}]},
    ):
        assert pg14_database.sql(
            "select public.conversational_rectification_numbers_are_stable("
            f"{_jsonb(invalid)})::text"
        ) == "false"

    assert pg14_database.sql(
        "select public.conversational_rectification_valid_private_candidate("
        f"{_jsonb({**_valid_private_candidate(), 'candidateWeights': [1e-100]})})::text"
    ) == "false"
    unstable_declared_input = {
        **_valid_declared_birth_input(),
        "birthplace": {
            **_valid_declared_birth_input()["birthplace"],
            "latitude": 1e-100,
        },
    }
    assert pg14_database.sql(
        "select public.conversational_rectification_valid_declared_birth_input("
        f"{_jsonb(unstable_declared_input)})::text"
    ) == "false"


def test_json_text_validators_align_types_uuid_unicode_and_utf16(
    pg14_database: PgDatabase,
) -> None:
    case_id = "00000000-0000-4000-8000-000000000960"
    turn = _valid_turn(case_id)
    private_candidate = _valid_private_candidate()
    unicode_whitespace = "\u00a0\u2007\ufeff"
    canonical_uuid = "a9890e09-d535-46f0-9a36-86017515a5a1"
    compact_uuid = canonical_uuid.replace("-", "")

    uuid_result = json.loads(pg14_database.sql(
        f"""
        select pg_catalog.jsonb_build_object(
          'lower', public.conversational_rectification_valid_uuid_text({_text(canonical_uuid)}),
          'upper', public.conversational_rectification_valid_uuid_text({_text(canonical_uuid.upper())}),
          'compact', public.conversational_rectification_valid_uuid_text({_text(compact_uuid)}),
          'braced', public.conversational_rectification_valid_uuid_text({_text('{' + canonical_uuid + '}')})
        )::text;
        """
    ))
    assert uuid_result == {"lower": True, "upper": True, "compact": False, "braced": False}

    invalid_turns = (
        {**turn, "candidate": {**turn["candidate"], "status": None}},
        {
            **turn,
            "technicalReceipt": {**turn["technicalReceipt"], "stableLayers": [None]},
        },
        {
            **turn,
            "technicalReceipt": {**turn["technicalReceipt"], "sensitiveLayers": [42]},
        },
        {
            **turn,
            "evidenceRequest": {**turn["evidenceRequest"], "domains": ["career", None]},
        },
        {
            **turn,
            "evidenceRequest": {**turn["evidenceRequest"], "datePrecision": None},
        },
        {**turn, "actions": [None]},
        {**turn, "status": None},
        {**turn, "narrative": unicode_whitespace},
        {
            **turn,
            "evidenceRecap": [{
                "id": compact_uuid,
                "summary": "summary",
                "dateLabel": "2020-01",
            }],
        },
    )
    for invalid in invalid_turns:
        assert pg14_database.sql(
            "select public.conversational_rectification_valid_public_turn("
            f"{_jsonb(invalid)})::text"
        ) == "false"

    invalid_private_candidates = (
        {**private_candidate, "resultId": compact_uuid},
        {**private_candidate, "suggestedDomains": ["career", None]},
        {**private_candidate, "d1Stability": None},
        {**private_candidate, "calculationVersion": unicode_whitespace},
        {
            **private_candidate,
            "workingState": {"phase": "initial", "iteration": 0, "notes": [unicode_whitespace]},
        },
        {
            **private_candidate,
            "futureWindows": [{
                "label": unicode_whitespace,
                "startDate": "2020-01-01",
                "endDate": "2020-01-02",
                "scoreable": False,
            }],
        },
    )
    for invalid in invalid_private_candidates:
        assert pg14_database.sql(
            "select public.conversational_rectification_valid_private_candidate("
            f"{_jsonb(invalid)})::text"
        ) == "false"

    invalid_declared = {
        **_valid_declared_birth_input(),
        "birthTimeClue": unicode_whitespace,
        "birthplace": {
            **_valid_declared_birth_input()["birthplace"],
            "city": unicode_whitespace,
        },
    }
    assert pg14_database.sql(
        "select public.conversational_rectification_valid_declared_birth_input("
        f"{_jsonb(invalid_declared)})::text"
    ) == "false"

    assert pg14_database.sql(
        "select public.conversational_rectification_valid_validation_receipt("
        f"{_jsonb({'modelId': unicode_whitespace, 'schemaValidated': True})})::text"
    ) == "false"
    assert pg14_database.sql(
        "select public.conversational_rectification_valid_action_response("
        f"{_jsonb({'success': False, 'credits': 7, 'billing_state': None, 'error_code': unicode_whitespace})}, "
        "'reserve_fee')::text"
    ) == "false"

    assert pg14_database.sql(
        "select public.conversational_rectification_text_utf16_length("
        f"{_text('😀' * 40)})::text"
    ) == "80"
    for model_id, expected in (("😀" * 60, "true"), ("😀" * 61, "false")):
        assert pg14_database.sql(
            "select public.conversational_rectification_valid_validation_receipt("
            f"{_jsonb({'modelId': model_id, 'schemaValidated': True})})::text"
        ) == expected


def test_save_rejects_invalid_evidence_without_discarding_or_coercing_fields(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000000961"
    case_id = "00000000-0000-4000-8000-000000000962"
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, case_id)
    _create_case(pg14_database, user_id, case_id, _valid_declared_birth_input())
    _complete(pg14_database, user_id, case_id)

    evidence = {
        "id": "00000000-0000-4000-8000-000000000963",
        "rawText": "2019 年 7 月换工作",
        "domain": "career",
        "eventSummary": "换工作",
        "dateValue": "2019-07",
        "datePrecision": "month",
        "extractionStatus": "clear",
        "scoreable": True,
    }
    invalid_values = (
        {**evidence, "unknown": "must not be discarded"},
        {**evidence, "id": "not-a-uuid"},
        {**evidence, "id": "00000000000040008000000000000001"},
        {**evidence, "rawText": 42},
        {**evidence, "domain": "finance"},
        {**evidence, "eventSummary": " \t "},
        {**evidence, "eventSummary": "\u00a0\u2007\ufeff"},
        {**evidence, "dateValue": " \t "},
        {**evidence, "datePrecision": "quarter"},
        {**evidence, "extractionStatus": "guessed"},
        {**evidence, "scoreable": None},
        {**evidence, "scoreable": "true"},
    )
    for index, invalid in enumerate(invalid_values):
        action_id = f"00000000-0000-4000-8000-{970 + index:012d}"
        assert pg14_database.rejects(
            _save_statement(user_id, case_id, 0, action_id, [invalid])
        )

    assert pg14_database.sql(
        f"select count(*) from public.birth_time_rectification_event_evidence where case_id = '{case_id}'::uuid"
    ) == "0"
    valid_without_optional_scoreable = {key: value for key, value in evidence.items() if key != "scoreable"}
    pg14_database.sql(
        _save_statement(
            user_id,
            case_id,
            0,
            "00000000-0000-4000-8000-000000000999",
            [valid_without_optional_scoreable],
        )
    )
    assert pg14_database.sql(
        f"select scoreable::text from public.birth_time_rectification_event_evidence where case_id = '{case_id}'::uuid"
    ) == "false"


def test_save_rejects_cumulative_evidence_count_before_inserting(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000000981"
    case_id = "00000000-0000-4000-8000-000000000982"
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, case_id)
    _create_case(pg14_database, user_id, case_id, _valid_declared_birth_input())
    _complete(pg14_database, user_id, case_id)
    pg14_database.sql(
        f"""
        insert into public.birth_time_rectification_event_evidence (
          id, case_id, source_turn_id, raw_text, domain, event_summary,
          date_value, date_precision, extraction_status, scoreable
        )
        select pg_catalog.md5('evidence-count-' || series)::uuid,
          '{case_id}'::uuid, turn.id, 'event', 'career', 'summary',
          null, 'unknown', 'clear', false
        from pg_catalog.generate_series(1, 2000) series
        cross join public.birth_time_rectification_turns turn
        where turn.case_id = '{case_id}'::uuid and turn.turn_version = 0;
        """
    )
    extra = {
        "id": "00000000-0000-4000-8000-000000000983",
        "rawText": "one more",
        "domain": "career",
        "eventSummary": "one more",
        "dateValue": None,
        "datePrecision": "unknown",
        "extractionStatus": "clear",
        "scoreable": False,
    }

    assert pg14_database.rejects(
        _save_statement(
            user_id,
            case_id,
            0,
            "00000000-0000-4000-8000-000000000984",
            [extra],
        )
    )
    assert pg14_database.sql(
        f"select count(*) from public.birth_time_rectification_event_evidence where case_id = '{case_id}'::uuid"
    ) == "2000"
    assert pg14_database.sql(
        f"select count(*) from public.birth_time_rectification_turns where case_id = '{case_id}'::uuid"
    ) == "1"


def test_save_rejects_cumulative_validation_receipt_count_before_inserting(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000000985"
    case_id = "00000000-0000-4000-8000-000000000986"
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, case_id)
    _create_case(pg14_database, user_id, case_id, _valid_declared_birth_input())
    _complete(pg14_database, user_id, case_id)
    base_turn = _valid_turn(case_id)
    last_turn = {**base_turn, "turnVersion": 1999}
    pg14_database.sql(
        f"""
        insert into public.birth_time_rectification_turns (
          case_id, turn_version, narrative, candidate, technical_receipt,
          evidence_request, evidence_recap, actions, output_validation_receipt
        )
        select '{case_id}'::uuid, series, 'seeded turn',
          {_jsonb(base_turn['candidate'])}, {_jsonb(base_turn['technicalReceipt'])},
          {_jsonb(base_turn['evidenceRequest'])}, '[]'::jsonb,
          {_jsonb(base_turn['actions'])},
          {_jsonb({'modelId': 'synthetic-model', 'schemaValidated': True})}
        from pg_catalog.generate_series(1, 1999) series;
        update public.birth_time_rectification_cases
        set turn_version = 1999,
            turn_state = {_jsonb(last_turn)},
            journey_snapshot = {_jsonb(last_turn)}
        where id = '{case_id}'::uuid;
        """
    )

    assert pg14_database.rejects(
        _save_statement(
            user_id,
            case_id,
            1999,
            "00000000-0000-4000-8000-000000000987",
            [],
        )
    )
    assert pg14_database.sql(
        f"select count(*) from public.birth_time_rectification_turns where case_id = '{case_id}'::uuid"
    ) == "2000"


def test_save_rejects_a_projected_load_envelope_over_four_mib(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000000988"
    case_id = "00000000-0000-4000-8000-000000000989"
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, case_id)
    _create_case(pg14_database, user_id, case_id, _valid_declared_birth_input())
    _complete(pg14_database, user_id, case_id)
    pg14_database.sql(
        f"""
        insert into public.birth_time_rectification_event_evidence (
          id, case_id, source_turn_id, raw_text, domain, event_summary,
          date_value, date_precision, extraction_status, scoreable
        )
        select pg_catalog.md5('evidence-bytes-' || series)::uuid,
          '{case_id}'::uuid, turn.id, pg_catalog.repeat('事', 4000),
          'career', pg_catalog.repeat('事', 1000), null, 'unknown', 'clear', false
        from pg_catalog.generate_series(1, 275) series
        cross join public.birth_time_rectification_turns turn
        where turn.case_id = '{case_id}'::uuid and turn.turn_version = 0;
        """
    )
    before_bytes = int(pg14_database.sql(
        f"select pg_catalog.octet_length(public.load_conversational_rectification_case('{user_id}'::uuid, '{case_id}'::uuid)::text)"
    ))
    assert 4_194_304 - 16_384 < before_bytes <= 4_194_304
    extra = {
        "id": "00000000-0000-4000-8000-000000000990",
        "rawText": "事" * 4_000,
        "domain": "career",
        "eventSummary": "事" * 1_000,
        "dateValue": "d" * 80,
        "datePrecision": "range",
        "extractionStatus": "corrected",
        "scoreable": True,
    }

    assert pg14_database.rejects(
        _save_statement(
            user_id,
            case_id,
            0,
            "00000000-0000-4000-8000-000000000991",
            [extra],
        )
    )
    assert pg14_database.sql(
        f"select count(*) from public.birth_time_rectification_event_evidence where case_id = '{case_id}'::uuid"
    ) == "275"


def test_crash_then_legacy_import_refunds_orphan_without_an_unrelated_paid_start(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000000992"
    lost_action = "00000000-0000-4000-8000-000000000993"
    legacy_case_id = "00000000-0000-4000-8000-000000000994"
    import_action = "00000000-0000-4000-8000-000000000995"
    _create_user(pg14_database, user_id, credits=10)
    _create_legacy_case(pg14_database, user_id, legacy_case_id)
    assert _reserve(pg14_database, user_id, lost_action)["credits"] == 7

    statement = f"""
    select public.import_legacy_conversational_rectification_case(
      '{user_id}'::uuid, '{import_action}'::uuid, '{legacy_case_id}'::uuid,
      0, '{import_action}'::uuid, 3, null,
      {_jsonb(_valid_turn(import_action))},
      {_jsonb({'modelId': 'synthetic-model', 'schemaValidated': True})},
      {_jsonb(_valid_private_candidate())}
    )::text;
    """
    imported = json.loads(pg14_database.sql(statement))
    assert imported["billing_state"] == "migration_waived"
    assert json.loads(pg14_database.sql(
        f"""
        select pg_catalog.jsonb_build_object(
          'credits', profile.credits,
          'orphanState', orphan.state,
          'importState', imported.state,
          'importBalance', imported.balance_after,
          'reserves', pg_catalog.count(*) filter (where tx.transaction_type = 'reserve'),
          'refunds', pg_catalog.count(*) filter (where tx.transaction_type = 'refund'),
          'recoveryReceipts', (
            select pg_catalog.count(*)
            from public.birth_time_rectification_action_receipts receipt
            where receipt.user_id = profile.id and receipt.action_kind = 'recover_fee'
          )
        )::text
        from public.profiles profile
        join public.birth_time_rectification_billing orphan on orphan.case_id = '{lost_action}'::uuid
        join public.birth_time_rectification_billing imported on imported.case_id = '{import_action}'::uuid
        left join public.credit_transactions tx on tx.user_id = profile.id
        where profile.id = '{user_id}'::uuid
        group by profile.id, profile.credits, orphan.state, imported.state, imported.balance_after;
        """
    )) == {
        "credits": 10,
        "orphanState": "released",
        "importState": "migration_waived",
        "importBalance": 10,
        "reserves": 1,
        "refunds": 1,
        "recoveryReceipts": 1,
    }
    assert json.loads(pg14_database.sql(
        f"""
        select pg_catalog.jsonb_build_object(
          'kind', receipt.request ->> 'kind',
          'credits', (receipt.response ->> 'credits')::integer,
          'transactionRequest', tx.request_id
        )::text
        from public.birth_time_rectification_action_receipts receipt
        join public.credit_transactions tx
          on tx.user_id = receipt.user_id and tx.transaction_type = 'refund'
        where receipt.user_id = '{user_id}'::uuid and receipt.action_kind = 'recover_fee';
        """
    )) == {
        "kind": "recover_fee",
        "credits": 10,
        "transactionRequest": f"rectification:{lost_action}",
    }

    assert json.loads(pg14_database.sql(statement)) == imported
    assert pg14_database.sql(
        f"select count(*) from public.credit_transactions where user_id = '{user_id}'::uuid"
    ) == "2"
