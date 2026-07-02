from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_official_capability_runner_schema_is_declared() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_official_capability_runner.py", "--print-schema"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["runner"] == "vedastro_official_capability_runner"
    assert report["primary_source"] == "vedastro_python_bridge"
    assert "run_bucket" in report["operations"]
    assert "run_selected_methods" in report["operations"]
    assert "run_snapshot_bundle" in report["operations"]
    assert "run_full_capability_catalog" in report["operations"]


def test_official_capability_runner_can_execute_stubbed_selected_methods() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_official_capability_runner.py",
            "--methods-json",
            json.dumps(["AllPlanetData", "AllHouseData", "GetAllEventDataGroupedByTag"]),
            "--birth-json",
            json.dumps(
                {
                    "year": REDACTED_YEAR,
                    "month": 4,
                    "day": 17,
                    "hour": 14,
                    "minute": 49,
                    "lat": 36.42,
                    "lon": 114.2,
                    "tz": 8,
                    "reference_date": "2026-06-29",
                }
            ),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env={
            **dict(**__import__("os").environ),
            "VEDASTRO_OFFICIAL_CAPABILITY_RUNNER_STUB": json.dumps(
                {
                    "AllPlanetData": {"available": True, "status": "ok", "result": {"PlanetRasiD1Sign": {"Name": "Aries"}}},
                    "AllHouseData": {"available": True, "status": "ok", "result": {"HouseBhavaChalitSign": {"Name": "Leo"}}},
                    "GetAllEventDataGroupedByTag": {"available": True, "status": "ok", "result": {"Marriage": []}},
                }
            ),
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["requested_method_count"] == 3
    assert report["summary"]["executed_method_count"] == 3
    assert report["summary"]["ok_count"] == 3
    assert report["results"]["AllPlanetData"]["status"] == "ok"
    assert report["results"]["AllHouseData"]["status"] == "ok"


def test_official_capability_runner_can_execute_stubbed_snapshot_bundle() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_official_capability_runner.py",
            "--bundle",
            "official_full_snapshot",
            "--birth-json",
            json.dumps(
                {
                    "year": REDACTED_YEAR,
                    "month": 4,
                    "day": 17,
                    "hour": 14,
                    "minute": 49,
                    "lat": 36.42,
                    "lon": 114.2,
                    "tz": 8,
                    "reference_date": "2026-06-29",
                }
            ),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env={
            **dict(**__import__("os").environ),
            "VEDASTRO_OFFICIAL_CAPABILITY_RUNNER_STUB": json.dumps(
                {
                    "AllPlanetData:Sun": {
                        "available": True,
                        "status": "ok",
                        "result": {"PlanetRasiD1Sign": {"Name": "Aries"}},
                    },
                    "AllHouseData:House1": {
                        "available": True,
                        "status": "ok",
                        "result": {"HouseBhavaChalitSign": {"Name": "Leo"}},
                    },
                    "DasaAtRange": {"available": True, "status": "ok", "result": [{"Lord": "Venus"}]},
                    "DasaAtTime": {"available": True, "status": "ok", "result": {"Lord": "Venus"}},
                    "GetCharaDasaAtTime": {"available": True, "status": "ok", "result": {"Sign": "Leo"}},
                    "AllPlanetStrength": {"available": True, "status": "ok", "result": {"Sun": 527.36}},
                    "AshtakvargaLifeMap": {"available": True, "status": "ok", "result": {"TotalBindus": 337}},
                }
            ),
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["bundle"] == "official_full_snapshot"
    assert report["summary"]["ok_count"] >= 6
    assert report["result"]["section_statuses"]["chart_core"] in {"ok", "partial"}
    assert report["result"]["section_statuses"]["house_core"] in {"ok", "partial"}
    assert report["result"]["snapshot_sections"]["chart_core"]["Sun"]["Payload"]["AllPlanetData"]["PlanetRasiD1Sign"]["Name"] == "Aries"
    assert report["result"]["snapshot_sections"]["house_core"]["House1"]["Payload"]["AllHouseData"]["HouseBhavaChalitSign"]["Name"] == "Leo"


def test_official_capability_runner_can_compile_stubbed_full_catalog_without_heavy_calls() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_official_capability_runner.py",
            "--bundle",
            "official_full_capability_catalog",
            "--birth-json",
            json.dumps(
                {
                    "year": REDACTED_YEAR,
                    "month": 4,
                    "day": 17,
                    "hour": 14,
                    "minute": 49,
                    "lat": 36.42,
                    "lon": 114.2,
                    "tz": 8,
                    "reference_date": "2026-06-29",
                }
            ),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env={
            **dict(**__import__("os").environ),
            "VEDASTRO_OFFICIAL_CAPABILITY_CATALOG_STUB": json.dumps(
                {
                    "available": True,
                    "status": "ok",
                    "capabilities": [
                        {
                            "method": "GetAllEventDataGroupedByTag",
                            "signature": "()",
                            "bucket": "zero_arg",
                            "parameter_names": [],
                            "callable": True,
                        },
                        {
                            "method": "AllPlanetData",
                            "signature": "(planetName, time)",
                            "bucket": "planet_time",
                            "parameter_names": ["planetName", "time"],
                            "callable": True,
                        },
                        {
                            "method": "SearchEvents",
                            "signature": "(birthTime, atTime, eventTagList)",
                            "bucket": "event_time",
                            "parameter_names": ["birthTime", "atTime", "eventTagList"],
                            "callable": True,
                        },
                        {
                            "method": "DasaAtRange",
                            "signature": "(birthTime, startTime, endTime, levels, precisionHours)",
                            "bucket": "dasha_at_range",
                            "parameter_names": ["birthTime", "startTime", "endTime", "levels", "precisionHours"],
                            "callable": True,
                        },
                        {
                            "method": "AllPlanetDashamamshaSign",
                            "signature": "(planetName, time)",
                            "bucket": "planet_time",
                            "parameter_names": ["planetName", "time"],
                            "callable": True,
                        },
                        {
                            "method": "MatchReport",
                            "signature": "(maleBirthTime, femaleBirthTime)",
                            "bucket": "(maleBirthTime, femaleBirthTime)",
                            "parameter_names": ["maleBirthTime", "femaleBirthTime"],
                            "callable": True,
                        },
                    ],
                    "buckets": {
                        "zero_arg": {"count": 1, "examples": ["GetAllEventDataGroupedByTag"]},
                        "planet_time": {"count": 2, "examples": ["AllPlanetData", "AllPlanetDashamamshaSign"]},
                        "event_time": {"count": 1, "examples": ["SearchEvents"]},
                        "dasha_at_range": {"count": 1, "examples": ["DasaAtRange"]},
                        "(maleBirthTime, femaleBirthTime)": {"count": 1, "examples": ["MatchReport"]},
                    },
                }
            ),
            "VEDASTRO_OFFICIAL_CAPABILITY_RUNNER_STUB": json.dumps(
                {
                    "GetAllEventDataGroupedByTag": {
                        "available": True,
                        "status": "ok",
                        "result": {"Marriage": []},
                    },
                    "AllPlanetData": {
                        "available": True,
                        "status": "ok",
                        "result": {"PlanetRasiD1Sign": {"Name": "Aries"}},
                    },
                    "SearchEvents": {
                        "available": True,
                        "status": "ok",
                        "result": {"Events": []},
                    },
                    "DasaAtRange": {
                        "available": True,
                        "status": "ok",
                        "result": {"Periods": []},
                    },
                    "AllPlanetDashamamshaSign": {
                        "available": True,
                        "status": "ok",
                        "result": {"Name": "Capricorn"},
                    },
                }
            ),
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["bundle"] == "official_full_capability_catalog"
    assert report["summary"]["catalog_method_count"] == 6
    assert report["summary"]["executed_method_count"] == 5
    assert report["summary"]["unsupported_method_count"] == 1
    assert report["coverage"]["source_mode"] == "official_full_capability_catalog"
    assert report["method_statuses"]["AllPlanetData"]["status"] == "ok"
    assert report["method_statuses"]["SearchEvents"]["domains"] == ["career", "marriage", "wealth", "rectification", "timing"]
    assert report["method_statuses"]["SearchEvents"]["execution_policy"] == "auto"
    assert report["method_statuses"]["SearchEvents"]["priority"] == "high"
    assert report["method_statuses"]["DasaAtRange"]["domains"] == ["career", "marriage", "wealth", "rectification", "timing"]
    assert "career" in report["method_statuses"]["AllPlanetDashamamshaSign"]["domains"]
    assert "timing" not in report["method_statuses"]["AllPlanetDashamamshaSign"]["domains"]
    assert report["domain_routing"]["marriage"]["high_priority_methods"] == ["SearchEvents", "DasaAtRange"]
    assert report["domain_routing"]["career"]["auto_method_count"] >= 2
    assert report["method_statuses"]["MatchReport"]["status"] == "requires_user_context"
    assert report["method_statuses"]["MatchReport"]["execution_policy"] == "needs_user_context"


def test_official_capability_runner_builds_dynamic_theme_selection_and_citations() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_official_capability_runner.py",
            "--bundle",
            "official_full_capability_catalog",
            "--birth-json",
            json.dumps(
                {
                    "year": REDACTED_YEAR,
                    "month": 4,
                    "day": 17,
                    "hour": 14,
                    "minute": 49,
                    "lat": 36.42,
                    "lon": 114.2,
                    "tz": 8,
                    "reference_date": "2026-06-29",
                    "themes": ["career", "marriage"],
                }
            ),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env={
            **dict(**__import__("os").environ),
            "VEDASTRO_OFFICIAL_CAPABILITY_CATALOG_STUB": json.dumps(
                {
                    "available": True,
                    "status": "ok",
                    "capabilities": [
                        {
                            "method": "SearchEvents",
                            "signature": "(birthTime, atTime, eventTagList)",
                            "bucket": "event_time",
                            "parameter_names": ["birthTime", "atTime", "eventTagList"],
                            "callable": True,
                        },
                        {
                            "method": "DasaAtRange",
                            "signature": "(birthTime, startTime, endTime, levels, precisionHours)",
                            "bucket": "dasha_at_range",
                            "parameter_names": ["birthTime", "startTime", "endTime", "levels", "precisionHours"],
                            "callable": True,
                        },
                        {
                            "method": "AllPlanetDashamamshaSign",
                            "signature": "(planetName, time)",
                            "bucket": "planet_time",
                            "parameter_names": ["planetName", "time"],
                            "callable": True,
                        },
                        {
                            "method": "MatchReport",
                            "signature": "(maleBirthTime, femaleBirthTime)",
                            "bucket": "relationship_context",
                            "parameter_names": ["maleBirthTime", "femaleBirthTime"],
                            "callable": True,
                        },
                    ],
                    "buckets": {
                        "event_time": {"count": 1, "examples": ["SearchEvents"]},
                        "dasha_at_range": {"count": 1, "examples": ["DasaAtRange"]},
                        "planet_time": {"count": 1, "examples": ["AllPlanetDashamamshaSign"]},
                        "relationship_context": {"count": 1, "examples": ["MatchReport"]},
                    },
                }
            ),
            "VEDASTRO_OFFICIAL_CAPABILITY_RUNNER_STUB": json.dumps(
                {
                    "SearchEvents": {"available": True, "status": "ok", "result": {"Events": []}},
                    "DasaAtRange": {"available": True, "status": "ok", "result": {"Periods": []}},
                    "AllPlanetDashamamshaSign": {"available": True, "status": "ok", "result": {"Name": "Capricorn"}},
                }
            ),
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    career = report["dynamic_selection"]["career"]
    marriage = report["dynamic_selection"]["marriage"]

    assert career["requested_theme"] == "career"
    assert career["selected_methods"][0]["method"] == "SearchEvents"
    assert career["selected_methods"][0]["citation_id"] == "vedastro:career:SearchEvents"
    assert career["selected_methods"][0]["execution_policy"] == "auto"
    assert "vedastro:career:DasaAtRange" in career["report_reference"]["citation_ids"]
    assert career["report_reference"]["blocked_count"] == 0

    assert marriage["selected_methods"][0]["method"] == "SearchEvents"
    assert marriage["needs_user_context_methods"][0]["method"] == "MatchReport"
    assert marriage["needs_user_context_methods"][0]["citation_id"] == "vedastro:marriage:MatchReport"
    assert marriage["report_reference"]["needs_user_context_count"] == 1


def test_full_catalog_classification_marks_non_core_domains_and_unknowns() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_official_capability_runner.py",
            "--bundle",
            "official_full_capability_catalog",
            "--birth-json",
            json.dumps(
                {
                    "year": REDACTED_YEAR,
                    "month": 4,
                    "day": 17,
                    "hour": 14,
                    "minute": 49,
                    "lat": 36.42,
                    "lon": 114.2,
                    "tz": 8,
                    "reference_date": "2026-06-29",
                    "themes": ["health", "education", "property", "children", "migration", "prashna"],
                }
            ),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env={
            **dict(**__import__("os").environ),
            "VEDASTRO_OFFICIAL_CAPABILITY_CATALOG_STUB": json.dumps(
                {
                    "available": True,
                    "status": "ok",
                    "capabilities": [
                        {
                            "method": "HealthProblemEvent",
                            "signature": "(birthTime, startTime, endTime)",
                            "bucket": "event_range",
                            "parameter_names": ["birthTime", "startTime", "endTime"],
                            "callable": True,
                        },
                        {
                            "method": "EducationDegreeYoga",
                            "signature": "(birthTime)",
                            "bucket": "birth_time_only",
                            "parameter_names": ["birthTime"],
                            "callable": True,
                        },
                        {
                            "method": "PropertyHouseVehicleResult",
                            "signature": "(birthTime)",
                            "bucket": "birth_time_only",
                            "parameter_names": ["birthTime"],
                            "callable": True,
                        },
                        {
                            "method": "ChildrenProgenyPromise",
                            "signature": "(birthTime)",
                            "bucket": "birth_time_only",
                            "parameter_names": ["birthTime"],
                            "callable": True,
                        },
                        {
                            "method": "ForeignTravelMigrationEvent",
                            "signature": "(birthTime, startTime, endTime)",
                            "bucket": "event_range",
                            "parameter_names": ["birthTime", "startTime", "endTime"],
                            "callable": True,
                        },
                        {
                            "method": "PrashnaHoraryJudgement",
                            "signature": "(queryTime, questionText)",
                            "bucket": "query_text",
                            "parameter_names": ["queryTime", "questionText"],
                            "callable": True,
                        },
                        {
                            "method": "OpaqueExperimentalCalculator",
                            "signature": "(complexPayload)",
                            "bucket": "opaque",
                            "parameter_names": ["complexPayload"],
                            "callable": True,
                        },
                    ],
                    "buckets": {
                        "event_range": {"count": 2, "examples": ["HealthProblemEvent", "ForeignTravelMigrationEvent"]},
                        "birth_time_only": {"count": 3, "examples": ["EducationDegreeYoga"]},
                        "query_text": {"count": 1, "examples": ["PrashnaHoraryJudgement"]},
                        "opaque": {"count": 1, "examples": ["OpaqueExperimentalCalculator"]},
                    },
                }
            ),
            "VEDASTRO_OFFICIAL_CAPABILITY_RUNNER_STUB": json.dumps(
                {
                    "HealthProblemEvent": {"available": True, "status": "ok", "result": {}},
                    "EducationDegreeYoga": {"available": True, "status": "ok", "result": {}},
                    "PropertyHouseVehicleResult": {"available": True, "status": "ok", "result": {}},
                    "ChildrenProgenyPromise": {"available": True, "status": "ok", "result": {}},
                    "ForeignTravelMigrationEvent": {"available": True, "status": "ok", "result": {}},
                }
            ),
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    required_fields = {"domains", "execution_policy", "adjudicator_use", "confidence_role", "blocked_reason"}
    for status in report["method_statuses"].values():
        assert required_fields.issubset(status)

    assert "health" in report["method_statuses"]["HealthProblemEvent"]["domains"]
    assert "education" in report["method_statuses"]["EducationDegreeYoga"]["domains"]
    assert "property" in report["method_statuses"]["PropertyHouseVehicleResult"]["domains"]
    assert "children" in report["method_statuses"]["ChildrenProgenyPromise"]["domains"]
    assert "migration" in report["method_statuses"]["ForeignTravelMigrationEvent"]["domains"]
    assert "prashna" in report["method_statuses"]["PrashnaHoraryJudgement"]["domains"]
    assert report["method_statuses"]["PrashnaHoraryJudgement"]["execution_policy"] == "needs_user_text"
    assert report["method_statuses"]["PrashnaHoraryJudgement"]["adjudicator_use"] == "secondary_context"
    assert report["method_statuses"]["OpaqueExperimentalCalculator"]["domains"] == ["unknown"]
    assert report["method_statuses"]["OpaqueExperimentalCalculator"]["execution_policy"] == "blocked"
    assert report["method_statuses"]["OpaqueExperimentalCalculator"]["blocked_reason"] == "unsupported_signature"

    for domain in ("health", "education", "property", "children", "migration", "prashna"):
        assert domain in report["domain_routing"]
        assert domain in report["dynamic_selection"]
    assert "general" not in report["domain_routing"]
    assert report["summary"]["unknown_method_count"] == 1
    assert report["summary"]["misrouted_general_method_count"] == 0
