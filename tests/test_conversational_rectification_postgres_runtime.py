import json
import hashlib
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor
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
    command_fingerprint: str | None = None,
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
      {_jsonb(private_candidate or _valid_private_candidate())},
      {"null" if command_fingerprint is None else _text(command_fingerprint)}
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


def _create_completed_handoff_case(
    database: PgDatabase,
    user_id: str,
    case_id: str,
    question: str,
) -> None:
    _reserve(database, user_id, case_id)
    first_turn = {
        **_valid_turn(case_id),
        "pendingConsultationQuestion": question,
    }
    database.sql(
        f"""
        select public.create_conversational_rectification_case(
          '{user_id}'::uuid, '{case_id}'::uuid, 0, '{case_id}'::uuid,
          null, {_text(question)}, {_jsonb(_valid_declared_birth_input())},
          {_jsonb(first_turn)},
          {_jsonb({"modelId": "synthetic-model", "schemaValidated": True})},
          {_jsonb(_valid_private_candidate())}
        )::text;
        """
    )
    _complete(database, user_id, case_id)
    completed_turn = {
        **first_turn,
        "status": "completed",
        "candidate": {**first_turn["candidate"], "status": "confirmed"},
        "evidenceRequest": None,
        "actions": ["continue_original_question"],
    }
    database.sql(
        f"""
        update public.birth_time_rectification_turns
        set candidate = {_jsonb(completed_turn["candidate"])},
            evidence_request = null,
            actions = '["continue_original_question"]'::jsonb
        where case_id = '{case_id}'::uuid and turn_version = 0;
        update public.birth_time_rectification_cases
        set status = 'completed',
            turn_state = {_jsonb(completed_turn)},
            journey_snapshot = {_jsonb(completed_turn)}
        where id = '{case_id}'::uuid and user_id = '{user_id}'::uuid;
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


def test_historical_receipt_replays_exact_public_response_after_later_turns(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000000943"
    case_id = "00000000-0000-4000-8000-000000000944"
    first_action = "00000000-0000-4000-8000-000000000945"
    later_actions = (
        "00000000-0000-4000-8000-000000000946",
        "00000000-0000-4000-8000-000000000947",
    )
    first_fingerprint = "a" * 64
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, case_id)
    _create_case(pg14_database, user_id, case_id, _valid_declared_birth_input())
    _complete(pg14_database, user_id, case_id)

    original = json.loads(pg14_database.sql(_save_statement(
        user_id,
        case_id,
        0,
        first_action,
        [],
        command_fingerprint=first_fingerprint,
    )))
    for version, action_id in enumerate(later_actions, start=1):
        pg14_database.sql(_save_statement(
            user_id,
            case_id,
            version,
            action_id,
            [],
            command_fingerprint=str(version) * 64,
        ))

    replayed = json.loads(pg14_database.sql(
        f"""
        select public.replay_conversational_rectification_action(
          '{user_id}'::uuid, '{case_id}'::uuid, 0, '{first_action}'::uuid,
          'save_turn', '{first_fingerprint}'
        )::text;
        """
    ))
    assert replayed == original
    assert replayed["turn_version"] == 1
    assert replayed["latest_turn"]["turnVersion"] == 1
    assert pg14_database.rejects(
        f"""
        select public.replay_conversational_rectification_action(
          '{user_id}'::uuid, '{case_id}'::uuid, 0, '{first_action}'::uuid,
          'save_turn', '{'b' * 64}'
        );
        """
    )

    privileges = json.loads(pg14_database.sql(
        """
        select pg_catalog.jsonb_build_object(
          'anon', pg_catalog.has_function_privilege(
            'anon',
            'public.replay_conversational_rectification_action(uuid,uuid,bigint,uuid,text,text)',
            'EXECUTE'
          ),
          'authenticated', pg_catalog.has_function_privilege(
            'authenticated',
            'public.replay_conversational_rectification_action(uuid,uuid,bigint,uuid,text,text)',
            'EXECUTE'
          ),
          'serviceRole', pg_catalog.has_function_privilege(
            'service_role',
            'public.replay_conversational_rectification_action(uuid,uuid,bigint,uuid,text,text)',
            'EXECUTE'
          )
        )::text;
        """
    ))
    assert privileges == {"anon": False, "authenticated": False, "serviceRole": True}


def test_overlapping_mutation_uses_command_identity(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000001041"
    case_id = "00000000-0000-4000-8000-000000001042"
    action_id = "00000000-0000-4000-8000-000000001043"
    fingerprint = "c" * 64
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, case_id)
    _create_case(pg14_database, user_id, case_id, _valid_declared_birth_input())
    _complete(pg14_database, user_id, case_id)

    original = json.loads(pg14_database.sql(_save_statement(
        user_id,
        case_id,
        0,
        action_id,
        [],
        command_fingerprint=fingerprint,
    )))
    alternate_turn = {
        **_valid_turn(case_id),
        "turnVersion": 1,
        "narrative": "A different valid narrative derived by an overlapping request.",
    }
    replayed = json.loads(pg14_database.sql(_save_statement(
        user_id,
        case_id,
        0,
        action_id,
        [],
        turn=alternate_turn,
        validation_receipt={"modelId": "alternate-model", "schemaValidated": True},
        command_fingerprint=fingerprint,
    )))
    assert replayed == original
    assert pg14_database.rejects(_save_statement(
        user_id,
        case_id,
        0,
        action_id,
        [],
        turn=alternate_turn,
        command_fingerprint="d" * 64,
    ))


def test_handoff_claim_is_atomic_and_failure_then_success_settles_once(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000002101"
    case_id = "00000000-0000-4000-8000-000000002102"
    first_claim = "00000000-0000-4000-8000-000000002103"
    second_claim = "00000000-0000-4000-8000-000000002104"
    retry_claim = "00000000-0000-4000-8000-000000002105"
    question = "未来半年是否适合换工作？"
    fingerprint = hashlib.sha256(question.encode("utf-8")).hexdigest()
    _create_user(pg14_database, user_id, credits=10)
    _create_completed_handoff_case(pg14_database, user_id, case_id, question)

    def claim(action_id: str) -> dict[str, object]:
        return json.loads(pg14_database.sql(
            f"""
            select public.claim_conversational_rectification_handoff(
              '{user_id}'::uuid, '{case_id}'::uuid, 0,
              '{action_id}'::uuid, '{fingerprint}'
            )::text;
            """
        ))

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(claim, (first_claim, second_claim)))
    assert sorted(result["status"] for result in results) == ["claimed", "in_progress"]
    winner_action = first_claim if results[0]["status"] == "claimed" else second_claim
    request_id = next(result["requestId"] for result in results if result["status"] == "claimed")
    assert results[0]["requestId"] == results[1]["requestId"]

    execution = json.loads(pg14_database.sql(
        f"""
        select public.begin_conversational_rectification_handoff_execution(
          '{user_id}'::uuid, '{case_id}'::uuid, 0, '{winner_action}'::uuid,
          '{request_id}'::uuid, '{fingerprint}'
        )::text;
        """
    ))
    assert execution == {
        "status": "ready",
        "requestId": request_id,
        "billingReused": False,
        "credits": 7,
    }
    reserved = json.loads(pg14_database.sql(
        f"""
        select row_to_json(result)::text from public.begin_consultation_credit(
          '{user_id}'::uuid, '{request_id}'
        ) result;
        """
    ))
    assert reserved["success"] is True
    assert reserved["credits"] == 6

    released = json.loads(pg14_database.sql(
        f"""
        select public.settle_conversational_rectification_handoff(
          '{user_id}'::uuid, '{case_id}'::uuid, '{winner_action}'::uuid,
          '{request_id}'::uuid, false
        )::text;
        """
    ))
    assert released == {"status": "pending", "requestId": request_id, "credits": 7}
    retry = claim(retry_claim)
    assert retry["status"] == "claimed"
    assert retry["requestId"] != request_id

    retry_execution = json.loads(pg14_database.sql(
        f"""
        select public.begin_conversational_rectification_handoff_execution(
          '{user_id}'::uuid, '{case_id}'::uuid, 0, '{retry_claim}'::uuid,
          '{retry['requestId']}'::uuid, '{fingerprint}'
        )::text;
        """
    ))
    assert retry_execution["status"] == "ready"
    assert json.loads(pg14_database.sql(
        f"""
        select row_to_json(result)::text from public.begin_consultation_credit(
          '{user_id}'::uuid, '{retry['requestId']}'
        ) result;
        """
    ))["success"] is True
    consumed = json.loads(pg14_database.sql(
        f"""
        select public.settle_conversational_rectification_handoff(
          '{user_id}'::uuid, '{case_id}'::uuid, '{retry_claim}'::uuid,
          '{retry['requestId']}'::uuid, true
        )::text;
        """
    ))
    assert consumed == {"status": "consumed", "requestId": retry["requestId"], "credits": 6}
    state = json.loads(pg14_database.sql(
        f"""
        select jsonb_build_object(
          'credits', profile.credits,
          'pendingQuestion', c.pending_consultation_question,
          'actions', t.actions,
          'handoffState', h.state,
          'consultations', (
            select count(*) from public.consultation_requests r
            where r.user_id = '{user_id}'::uuid and r.status = 'completed'
          )
        )::text
        from public.profiles profile
        join public.birth_time_rectification_cases c on c.user_id = profile.id
        join public.birth_time_rectification_turns t
          on t.case_id = c.id and t.turn_version = c.turn_version
        join public.birth_time_rectification_question_handoffs h on h.case_id = c.id
        where profile.id = '{user_id}'::uuid and c.id = '{case_id}'::uuid;
        """
    ))
    assert state == {
        "credits": 6,
        "pendingQuestion": None,
        "actions": [],
        "handoffState": "consumed",
        "consultations": 1,
    }
    late_claim = claim("00000000-0000-4000-8000-000000002106")
    assert late_claim["status"] == "consumed"
    assert late_claim["turn"]["pendingConsultationQuestion"] is None
    replayed_execution = json.loads(pg14_database.sql(
        f"""
        select public.begin_conversational_rectification_handoff_execution(
          '{user_id}'::uuid, '{case_id}'::uuid, 0, '{retry_claim}'::uuid,
          '{retry['requestId']}'::uuid, '{fingerprint}'
        )::text;
        """
    ))
    assert replayed_execution == {
        "status": "consumed",
        "requestId": retry["requestId"],
    }


def test_handoff_acl_and_attach_replacement_are_owner_locked(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000002111"
    other_user_id = "00000000-0000-4000-8000-000000002112"
    case_id = "00000000-0000-4000-8000-000000002113"
    action_id = "00000000-0000-4000-8000-000000002114"
    first_question = "旧问题"
    replacement = "新的事业问题"
    fingerprint = hashlib.sha256(replacement.encode("utf-8")).hexdigest()
    _create_user(pg14_database, user_id)
    _create_user(pg14_database, other_user_id)
    _reserve(pg14_database, user_id, case_id)
    first_turn = {**_valid_turn(case_id), "pendingConsultationQuestion": first_question}
    pg14_database.sql(
        f"""
        select public.create_conversational_rectification_case(
          '{user_id}'::uuid, '{case_id}'::uuid, 0, '{case_id}'::uuid,
          null, {_text(first_question)}, {_jsonb(_valid_declared_birth_input())},
          {_jsonb(first_turn)},
          {_jsonb({"modelId": "synthetic-model", "schemaValidated": True})},
          {_jsonb(_valid_private_candidate())}
        );
        """
    )
    _complete(pg14_database, user_id, case_id)
    replaced = json.loads(pg14_database.sql(
        f"""
        select public.attach_conversational_rectification_question(
          '{user_id}'::uuid, '{case_id}'::uuid, 0, '{action_id}'::uuid,
          {_text(replacement)}, '{fingerprint}'
        )::text;
        """
    ))
    assert replaced["pending_consultation_question"] == replacement
    assert replaced["latest_turn"]["pendingConsultationQuestion"] == replacement
    assert pg14_database.rejects(
        f"""
        select public.attach_conversational_rectification_question(
          '{other_user_id}'::uuid, '{case_id}'::uuid, 0, '{action_id}'::uuid,
          {_text(replacement)}, '{fingerprint}'
        );
        """
    )

    privileges = json.loads(pg14_database.sql(
        """
        select jsonb_build_object(
          'anon', has_function_privilege(
            'anon',
            'public.claim_conversational_rectification_handoff(uuid,uuid,bigint,uuid,text)',
            'EXECUTE'
          ),
          'authenticated', has_function_privilege(
            'authenticated',
            'public.claim_conversational_rectification_handoff(uuid,uuid,bigint,uuid,text)',
            'EXECUTE'
          ),
          'serviceRole', has_function_privilege(
            'service_role',
            'public.claim_conversational_rectification_handoff(uuid,uuid,bigint,uuid,text)',
            'EXECUTE'
          )
        )::text;
        """
    ))
    assert privileges == {"anon": False, "authenticated": False, "serviceRole": True}


def test_expired_handoff_lease_reuses_the_reserved_request_without_double_billing(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000002121"
    case_id = "00000000-0000-4000-8000-000000002122"
    abandoned_claim = "00000000-0000-4000-8000-000000002123"
    recovered_claim = "00000000-0000-4000-8000-000000002124"
    question = "这次事业调整应该如何准备？"
    fingerprint = hashlib.sha256(question.encode("utf-8")).hexdigest()
    _create_user(pg14_database, user_id, credits=10)
    _create_completed_handoff_case(pg14_database, user_id, case_id, question)

    first_claim = json.loads(pg14_database.sql(
        f"""
        select public.claim_conversational_rectification_handoff(
          '{user_id}'::uuid, '{case_id}'::uuid, 0,
          '{abandoned_claim}'::uuid, '{fingerprint}'
        )::text;
        """
    ))
    request_id = first_claim["requestId"]
    assert first_claim["status"] == "claimed"
    assert json.loads(pg14_database.sql(
        f"""
        select public.begin_conversational_rectification_handoff_execution(
          '{user_id}'::uuid, '{case_id}'::uuid, 0,
          '{abandoned_claim}'::uuid, '{request_id}'::uuid, '{fingerprint}'
        )::text;
        """
    ))["billingReused"] is False
    assert json.loads(pg14_database.sql(
        f"""
        select row_to_json(result)::text from public.begin_consultation_credit(
          '{user_id}'::uuid, '{request_id}'
        ) result;
        """
    ))["success"] is True

    pg14_database.sql(
        f"""
        update public.birth_time_rectification_question_handoffs
        set lease_expires_at = now() - interval '1 second'
        where case_id = '{case_id}'::uuid and user_id = '{user_id}'::uuid;
        """
    )
    recovered = json.loads(pg14_database.sql(
        f"""
        select public.claim_conversational_rectification_handoff(
          '{user_id}'::uuid, '{case_id}'::uuid, 0,
          '{recovered_claim}'::uuid, '{fingerprint}'
        )::text;
        """
    ))
    assert recovered["status"] == "claimed"
    assert recovered["requestId"] == request_id
    execution = json.loads(pg14_database.sql(
        f"""
        select public.begin_conversational_rectification_handoff_execution(
          '{user_id}'::uuid, '{case_id}'::uuid, 0,
          '{recovered_claim}'::uuid, '{request_id}'::uuid, '{fingerprint}'
        )::text;
        """
    ))
    assert execution == {
        "status": "ready",
        "requestId": request_id,
        "billingReused": True,
        "credits": 6,
    }
    accounting = json.loads(pg14_database.sql(
        f"""
        select jsonb_build_object(
          'credits', profile.credits,
          'requests', count(distinct request.request_id),
          'reserves', count(tx.id) filter (where tx.transaction_type = 'reserve')
        )::text
        from public.profiles profile
        join public.consultation_requests request
          on request.user_id = profile.id and request.request_id = '{request_id}'
        left join public.credit_transactions tx
          on tx.user_id = profile.id and tx.request_id = '{request_id}'
        where profile.id = '{user_id}'::uuid
        group by profile.credits;
        """
    ))
    assert accounting == {"credits": 6, "requests": 1, "reserves": 1}

    released = json.loads(pg14_database.sql(
        f"""
        select public.settle_conversational_rectification_handoff(
          '{user_id}'::uuid, '{case_id}'::uuid, '{recovered_claim}'::uuid,
          '{request_id}'::uuid, false
        )::text;
        """
    ))
    assert released == {"status": "pending", "requestId": request_id, "credits": 7}


def test_legacy_overlap_still_uses_full_derived_request(pg14_database: PgDatabase) -> None:
    legacy_user_id = "00000000-0000-4000-8000-000000001051"
    legacy_case_id = "00000000-0000-4000-8000-000000001052"
    legacy_action_id = "00000000-0000-4000-8000-000000001053"
    _create_user(pg14_database, legacy_user_id)
    _reserve(pg14_database, legacy_user_id, legacy_case_id)
    _create_case(
        pg14_database,
        legacy_user_id,
        legacy_case_id,
        _valid_declared_birth_input(),
    )
    _complete(pg14_database, legacy_user_id, legacy_case_id)
    legacy_statement = _save_statement(
        legacy_user_id,
        legacy_case_id,
        0,
        legacy_action_id,
        [],
    )
    legacy_original = json.loads(pg14_database.sql(legacy_statement))
    assert json.loads(pg14_database.sql(legacy_statement)) == legacy_original
    assert pg14_database.rejects(_save_statement(
        legacy_user_id,
        legacy_case_id,
        0,
        legacy_action_id,
        [],
        turn={
            **_valid_turn(legacy_case_id),
            "turnVersion": 1,
            "narrative": "A different legacy-derived narrative must remain a conflict.",
        },
    ))


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


def test_correction_lineage_is_append_only_owner_scoped_and_rejects_retired_targets(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000001201"
    case_id = "00000000-0000-4000-8000-000000001202"
    first_action = "00000000-0000-4000-8000-000000001203"
    second_action = "00000000-0000-4000-8000-000000001204"
    third_action = "00000000-0000-4000-8000-000000001205"
    rejected_action = "00000000-0000-4000-8000-000000001206"
    missing_id = "00000000-0000-4000-8000-000000001207"
    first_id = "00000000-0000-4000-8000-000000001211"
    second_id = "00000000-0000-4000-8000-000000001212"
    third_id = "00000000-0000-4000-8000-000000001213"
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, case_id)
    _create_case(pg14_database, user_id, case_id, _valid_declared_birth_input())
    _complete(pg14_database, user_id, case_id)

    first = {
        "id": first_id,
        "rawText": "2019 年 7 月开始第一份工作",
        "domain": "career",
        "eventSummary": "开始第一份工作",
        "dateValue": "2019-07",
        "datePrecision": "month",
        "extractionStatus": "clear",
        "scoreable": True,
    }
    pg14_database.sql(_save_statement(
        user_id,
        case_id,
        0,
        first_action,
        [first],
        turn={
            **_valid_turn(case_id),
            "turnVersion": 1,
            "evidenceRecap": [{
                "id": first_id,
                "summary": "开始第一份工作",
                "dateLabel": "2019-07",
                "isCorrection": False,
            }],
        },
    ))
    loaded_first = json.loads(pg14_database.sql(
        f"select public.load_conversational_rectification_case('{user_id}'::uuid, '{case_id}'::uuid)::text"
    ))
    assert loaded_first["event_evidence"][0]["correctsEvidenceIds"] == []

    second = {
        "id": second_id,
        "rawText": "更正：2020 年 11 月离职",
        "domain": "career",
        "eventSummary": "离职",
        "dateValue": "2020-11",
        "datePrecision": "month",
        "extractionStatus": "corrected",
        "scoreable": True,
        "correctsEvidenceIds": [first_id],
    }
    pg14_database.sql(_save_statement(
        user_id,
        case_id,
        1,
        second_action,
        [second],
        turn={
            **_valid_turn(case_id),
            "turnVersion": 2,
            "evidenceRecap": [{
                "id": second_id,
                "summary": "离职",
                "dateLabel": "2020-11",
                "isCorrection": True,
            }],
        },
    ))

    for invalid_target in (missing_id, first_id):
        rejected = {
            **second,
            "id": third_id,
            "correctsEvidenceIds": [invalid_target],
        }
        assert pg14_database.rejects(_save_statement(
            user_id,
            case_id,
            2,
            rejected_action,
            [rejected],
        ))
    assert pg14_database.sql(
        f"select turn_version::text from public.birth_time_rectification_cases where id = '{case_id}'::uuid"
    ) == "2"
    assert pg14_database.sql(
        f"select count(*)::text from public.birth_time_rectification_event_evidence where case_id = '{case_id}'::uuid"
    ) == "2"

    third = {
        **second,
        "id": third_id,
        "rawText": "更正：2021 年 2 月入职",
        "eventSummary": "入职",
        "dateValue": "2021-02",
        "correctsEvidenceIds": [second_id],
    }
    pg14_database.sql(_save_statement(
        user_id,
        case_id,
        2,
        third_action,
        [third],
        turn={
            **_valid_turn(case_id),
            "turnVersion": 3,
            "evidenceRecap": [{
                "id": third_id,
                "summary": "入职",
                "dateLabel": "2021-02",
                "isCorrection": True,
            }],
        },
    ))
    loaded = json.loads(pg14_database.sql(
        f"select public.load_conversational_rectification_case('{user_id}'::uuid, '{case_id}'::uuid)::text"
    ))
    assert len(loaded["event_evidence"]) == 3
    assert loaded["event_evidence"][1]["correctsEvidenceIds"] == [first_id]
    assert loaded["event_evidence"][2]["correctsEvidenceIds"] == [second_id]
    assert loaded["latest_turn"]["evidenceRecap"] == [{
        "id": third_id,
        "summary": "入职",
        "dateLabel": "2021-02",
        "isCorrection": True,
    }]


def test_duplicate_correction_target_fails_atomically_without_advancing_any_durable_state(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000001401"
    case_id = "00000000-0000-4000-8000-000000001402"
    first_action = "00000000-0000-4000-8000-000000001403"
    rejected_action = "00000000-0000-4000-8000-000000001404"
    first_id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaa1411"
    replacement_a = "00000000-0000-4000-8000-000000001412"
    replacement_b = "00000000-0000-4000-8000-000000001413"
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, case_id)
    _create_case(pg14_database, user_id, case_id, _valid_declared_birth_input())
    _complete(pg14_database, user_id, case_id)
    first = {
        "id": first_id,
        "rawText": "2019 年 7 月开始第一份工作",
        "domain": "career",
        "eventSummary": "开始第一份工作",
        "dateValue": "2019-07",
        "datePrecision": "month",
        "extractionStatus": "clear",
        "scoreable": True,
    }
    pg14_database.sql(_save_statement(user_id, case_id, 0, first_action, [first]))

    def durable_counts() -> dict[str, int]:
        return json.loads(pg14_database.sql(
            f"""
            select pg_catalog.jsonb_build_object(
              'version', rectification.turn_version,
              'turns', (select pg_catalog.count(*) from public.birth_time_rectification_turns turn where turn.case_id = rectification.id),
              'evidence', (select pg_catalog.count(*) from public.birth_time_rectification_event_evidence evidence where evidence.case_id = rectification.id),
              'receipts', (select pg_catalog.count(*) from public.birth_time_rectification_action_receipts receipt where receipt.case_id = rectification.id)
            )::text
            from public.birth_time_rectification_cases rectification
            where rectification.id = '{case_id}'::uuid;
            """
        ))

    before = durable_counts()
    duplicate_replacements = [
        {
            "id": replacement_a,
            "rawText": "更正：2020 年 11 月离职",
            "domain": "career",
            "eventSummary": "离职",
            "dateValue": "2020-11",
            "datePrecision": "month",
            "extractionStatus": "corrected",
            "scoreable": True,
            "correctsEvidenceIds": [first_id.upper()],
        },
        {
            "id": replacement_b,
            "rawText": "更正：2021 年 2 月入职",
            "domain": "career",
            "eventSummary": "入职",
            "dateValue": "2021-02",
            "datePrecision": "month",
            "extractionStatus": "corrected",
            "scoreable": True,
            "correctsEvidenceIds": [first_id],
        },
    ]
    assert pg14_database.rejects(_save_statement(
        user_id,
        case_id,
        1,
        rejected_action,
        duplicate_replacements,
    ))
    assert durable_counts() == before


def test_concurrent_corrections_of_one_tip_leave_exactly_one_winner(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000001421"
    case_id = "00000000-0000-4000-8000-000000001422"
    first_action = "00000000-0000-4000-8000-000000001423"
    action_a = "00000000-0000-4000-8000-000000001424"
    action_b = "00000000-0000-4000-8000-000000001425"
    first_id = "00000000-0000-4000-8000-000000001431"
    replacement_a = "00000000-0000-4000-8000-000000001432"
    replacement_b = "00000000-0000-4000-8000-000000001433"
    _create_user(pg14_database, user_id)
    _reserve(pg14_database, user_id, case_id)
    _create_case(pg14_database, user_id, case_id, _valid_declared_birth_input())
    _complete(pg14_database, user_id, case_id)
    first = {
        "id": first_id,
        "rawText": "2019 年 7 月开始第一份工作",
        "domain": "career",
        "eventSummary": "开始第一份工作",
        "dateValue": "2019-07",
        "datePrecision": "month",
        "extractionStatus": "clear",
        "scoreable": True,
    }
    pg14_database.sql(_save_statement(user_id, case_id, 0, first_action, [first]))

    statements = []
    for action_id, evidence_id, date_value, summary in (
        (action_a, replacement_a, "2020-11", "离职"),
        (action_b, replacement_b, "2021-02", "入职"),
    ):
        replacement = {
            "id": evidence_id,
            "rawText": f"更正：{date_value} {summary}",
            "domain": "career",
            "eventSummary": summary,
            "dateValue": date_value,
            "datePrecision": "month",
            "extractionStatus": "corrected",
            "scoreable": True,
            "correctsEvidenceIds": [first_id],
        }
        statements.append(_save_statement(
            user_id,
            case_id,
            1,
            action_id,
            [replacement],
        ))

    processes = [subprocess.Popen(
        pg14_database.command("-A", "-t", "-q", "-c", statement),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) for statement in statements]
    results = [process.communicate(timeout=20) for process in processes]
    return_codes = [process.returncode for process in processes]
    assert return_codes.count(0) == 1, results
    assert sum(code != 0 for code in return_codes) == 1, results

    durable = json.loads(pg14_database.sql(
        f"""
        select pg_catalog.jsonb_build_object(
          'version', rectification.turn_version,
          'turns', (select pg_catalog.count(*) from public.birth_time_rectification_turns turn where turn.case_id = rectification.id),
          'evidence', (select pg_catalog.count(*) from public.birth_time_rectification_event_evidence evidence where evidence.case_id = rectification.id),
          'winningReceipts', (select pg_catalog.count(*) from public.birth_time_rectification_action_receipts receipt where receipt.case_id = rectification.id and receipt.action_id in ('{action_a}'::uuid, '{action_b}'::uuid))
        )::text
        from public.birth_time_rectification_cases rectification
        where rectification.id = '{case_id}'::uuid;
        """
    ))
    assert durable == {
        "version": 2,
        "turns": 3,
        "evidence": 2,
        "winningReceipts": 1,
    }


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

    declared = {
        "birthDate": "1990-01-01",
        "reportedTime": "05:20",
        "source": "legacy_import",
        "birthTimeClue": None,
        "uncertaintyBeforeMinutes": 0,
        "uncertaintyAfterMinutes": 0,
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
    statement = f"""
    select public.import_legacy_conversational_rectification_case(
      '{user_id}'::uuid, '{import_action}'::uuid, '{legacy_case_id}'::uuid,
      0, '{import_action}'::uuid, 3, null,
      {_jsonb(declared)}, '[]'::jsonb,
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


def test_concurrent_legacy_import_projects_events_once_and_keeps_old_row_read_only(
    pg14_database: PgDatabase,
) -> None:
    user_id = "00000000-0000-4000-8000-000000002701"
    legacy_case_id = "00000000-0000-4000-8000-000000002702"
    action_a = "00000000-0000-4000-8000-000000002703"
    action_b = "00000000-0000-4000-8000-000000002704"
    drift_action = "00000000-0000-4000-8000-000000002709"
    career_id = "00000000-0000-4000-8000-000000002705"
    finance_id = "00000000-0000-4000-8000-000000002706"
    _create_user(pg14_database, user_id, credits=10)
    _create_legacy_case(pg14_database, user_id, legacy_case_id)
    old_life_events = [
        {"id": career_id, "domain": "career", "precision": "month", "date": "2021-07"},
        {"id": finance_id, "domain": "finance", "precision": "year", "date": "2020"},
        {"id": "00000000-0000-4000-8000-000000002707", "domain": "relationship", "precision": "month", "date": "2099-01"},
        {"id": "00000000-0000-4000-8000-000000002708", "domain": "education", "precision": "year", "date": "1980"},
    ]
    pg14_database.sql(
        f"""
        update public.birth_time_rectification_cases
        set questionnaire = {_jsonb({'questions': [{'prompt': '哪一个时间段更符合？'}]})},
            answers = {_jsonb({'generic-question': 'A'})},
            life_events = {_jsonb(old_life_events)},
            candidate_scan = {_jsonb({'genericRanges': ['2006-2011', '2011-2016']})},
            candidate_start = '05:10',
            candidate_end = '05:30'
        where id = '{legacy_case_id}'::uuid;
        """
    )
    declared = {
        "birthDate": "1990-01-01",
        "reportedTime": "05:20",
        "source": "legacy_import",
        "birthTimeClue": None,
        "uncertaintyBeforeMinutes": 0,
        "uncertaintyAfterMinutes": 0,
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
    evidence = [
        {
            "id": career_id,
            "rawText": "旧校时记录中的事业事件（2021-07）",
            "domain": "career",
            "eventSummary": "旧校时记录中的事业事件",
            "dateValue": "2021-07",
            "datePrecision": "month",
            "extractionStatus": "clear",
            "scoreable": True,
            "correctsEvidenceIds": [],
        },
        {
            "id": finance_id,
            "rawText": "旧校时记录中的其他事件（2020）",
            "domain": "other",
            "eventSummary": "旧校时记录中的其他事件",
            "dateValue": "2020",
            "datePrecision": "year",
            "extractionStatus": "clear",
            "scoreable": True,
            "correctsEvidenceIds": [],
        },
    ]

    def statement(action: str) -> str:
        turn = {
            **_valid_turn(action),
            "evidenceRecap": [
                {"id": item["id"], "summary": item["eventSummary"], "dateLabel": item["dateValue"]}
                for item in evidence
            ],
        }
        return f"""
        select public.import_legacy_conversational_rectification_case(
          '{user_id}'::uuid, '{action}'::uuid, '{legacy_case_id}'::uuid,
          0, '{action}'::uuid, 3, null,
          {_jsonb(declared)}, {_jsonb(evidence)}, {_jsonb(turn)},
          {_jsonb({'modelId': 'synthetic-model', 'schemaValidated': True})},
          {_jsonb(_valid_private_candidate())}
        )::text;
        """

    drifted_declared = {**declared, "reportedTime": "06:40"}
    drifted_turn = {
        **_valid_turn(drift_action),
        "evidenceRecap": [
            {"id": item["id"], "summary": item["eventSummary"], "dateLabel": item["dateValue"]}
            for item in evidence
        ],
    }
    assert pg14_database.rejects(
        f"""
        select public.import_legacy_conversational_rectification_case(
          '{user_id}'::uuid, '{drift_action}'::uuid, '{legacy_case_id}'::uuid,
          0, '{drift_action}'::uuid, 3, null,
          {_jsonb(drifted_declared)}, {_jsonb(evidence)}, {_jsonb(drifted_turn)},
          {_jsonb({'modelId': 'synthetic-model', 'schemaValidated': True})},
          {_jsonb(_valid_private_candidate())}
        )::text;
        """
    )
    assert pg14_database.sql(
        f"select count(*) from public.birth_time_rectification_cases where imported_from_case_id = '{legacy_case_id}'::uuid"
    ) == "0"

    processes = [subprocess.Popen(
        pg14_database.command("-A", "-t", "-q", "-c", statement(action)),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    ) for action in (action_a, action_b)]
    results = [process.communicate(timeout=20) for process in processes]
    return_codes = [process.returncode for process in processes]
    assert return_codes.count(0) == 1, results
    assert sum(code != 0 for code in return_codes) == 1, results

    durable = json.loads(pg14_database.sql(
        f"""
        select pg_catalog.jsonb_build_object(
          'credits', profile.credits,
          'activeTime', pg_catalog.to_char(profile.active_birth_time, 'HH24:MI'),
          'importCount', (select pg_catalog.count(*) from public.birth_time_rectification_cases imported where imported.imported_from_case_id = '{legacy_case_id}'::uuid),
          'billingStates', (select pg_catalog.jsonb_agg(billing.state) from public.birth_time_rectification_billing billing join public.birth_time_rectification_cases imported on imported.id = billing.case_id where imported.imported_from_case_id = '{legacy_case_id}'::uuid),
          'eventIds', (select pg_catalog.jsonb_agg(event.id order by event.created_at) from public.birth_time_rectification_event_evidence event join public.birth_time_rectification_cases imported on imported.id = event.case_id where imported.imported_from_case_id = '{legacy_case_id}'::uuid),
          'importedGenericState', (select pg_catalog.jsonb_build_object('questionnaire', imported.questionnaire, 'answers', imported.answers, 'lifeEvents', imported.life_events, 'candidateScan', imported.candidate_scan, 'baseline', pg_catalog.to_char(imported.baseline_active_time, 'HH24:MI')) from public.birth_time_rectification_cases imported where imported.imported_from_case_id = '{legacy_case_id}'::uuid),
          'legacyGenericState', (select pg_catalog.jsonb_build_object('questionnaire', legacy.questionnaire, 'answers', legacy.answers, 'candidateScan', legacy.candidate_scan) from public.birth_time_rectification_cases legacy where legacy.id = '{legacy_case_id}'::uuid)
        )::text
        from public.profiles profile where profile.id = '{user_id}'::uuid;
        """
    ))
    assert durable == {
        "credits": 10,
        "activeTime": "04:58",
        "importCount": 1,
        "billingStates": ["migration_waived"],
        "eventIds": [career_id, finance_id],
        "importedGenericState": {
            "questionnaire": {},
            "answers": {},
            "lifeEvents": [],
            "candidateScan": {},
            "baseline": "04:58",
        },
        "legacyGenericState": {
            "questionnaire": {"questions": [{"prompt": "哪一个时间段更符合？"}]},
            "answers": {"generic-question": "A"},
            "candidateScan": {"genericRanges": ["2006-2011", "2011-2016"]},
        },
    }
    assert pg14_database.rejects(
        f"update public.birth_time_rectification_cases set answers = '{{}}'::jsonb where id = '{legacy_case_id}'::uuid"
    )
