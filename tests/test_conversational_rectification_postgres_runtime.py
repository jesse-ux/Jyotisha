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
