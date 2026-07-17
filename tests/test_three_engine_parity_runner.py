from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import three_engine_parity_runner  # noqa: E402
from three_engine_parity_runner import build_public_case_replay  # noqa: E402


def test_public_same_chart_replay_never_promotes_missing_vedastro_raw(tmp_path: Path) -> None:
    report = build_public_case_replay(output_dir=tmp_path, allow_vedastro_network=False)

    assert report["case_id"] == "steve_jobs_public_1955_lahiri"
    assert report["birth_data_policy"] == "public_case_only"
    assert report["engines"]["PyJHora_JHora"]["status"] == "structured_captured"
    assert report["engines"]["jyotishganit"]["status"] == "raw_captured"
    assert report["engines"]["VedAstro"]["status"] == "blocked"
    assert report["status"] in {"partial", "blocked"}
    assert report["tested"] is False
    assert report["comparison_rows"]
    assert any(row["status"] == "match" for row in report["comparison_rows"])
    assert all(row["status"] in {"blocked", "match", "not_comparable"} for row in report["comparison_rows"])


def test_public_same_chart_replay_imports_verified_vedastro_artifact(tmp_path: Path, monkeypatch) -> None:
    artifact_root = tmp_path / "vedastro_adapter"
    artifact_root.mkdir()
    artifact = artifact_root / "official_full_snapshot-abc-def.json"
    artifact.write_text(
        json.dumps(
            {
                "status": "ok",
                "operation": "official_full_snapshot",
                "raw_response": {"source": "vedastro_official_full_snapshot", "sections": {"chart_core": {}}},
                "request_manifest": {
                    "settings": {"ayanamsa": "lahiri", "node_mode": "mean"},
                    "requests": [
                        {
                            "body": {
                                "BirthTime": {
                                    "StdTime": "19:15 24/02/1955 -08:00",
                                    "Location": {"Latitude": 37.7749, "Longitude": -122.4194},
                                }
                            }
                        }
                    ],
                },
                "snapshot_sections": {"chart_core": {"Status": "Pass"}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(three_engine_parity_runner, "VEDASTRO_ARTIFACT_DIR", artifact_root)

    report = build_public_case_replay(output_dir=tmp_path / "out", allow_vedastro_network=True)

    assert report["engines"]["VedAstro"]["status"] == "official_verified"
    assert report["engines"]["VedAstro"]["official_raw_response_path"] == str(artifact)
    assert len(report["engines"]["VedAstro"]["artifact_hash"]) == 64
    assert report["blocked_reason"] == "none"


def test_public_same_chart_replay_rejects_wrong_vedastro_artifact(tmp_path: Path, monkeypatch) -> None:
    artifact_root = tmp_path / "vedastro_adapter"
    artifact_root.mkdir()
    artifact = artifact_root / "official_full_snapshot-wrong-chart.json"
    artifact.write_text(
        json.dumps(
            {
                "status": "ok",
                "raw_response": {"source": "vedastro_official_full_snapshot"},
                "request_manifest": {
                    "requests": [
                        {
                            "body": {
                                "BirthTime": {
                                    "StdTime": "12:00 01/01/1990 +05:30",
                                    "Location": {"Latitude": 28.6139, "Longitude": 77.209},
                                }
                            }
                        }
                    ]
                },
                "snapshot_sections": {"chart_core": {"Status": "Pass"}},
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(three_engine_parity_runner, "VEDASTRO_ARTIFACT_DIR", artifact_root)

    report = build_public_case_replay(output_dir=tmp_path / "out", allow_vedastro_network=True)

    assert report["engines"]["VedAstro"]["status"] == "blocked"
    assert report["engines"]["VedAstro"]["reason"] == "official_runner_requires_explicit_raw_capture_workflow"


def test_public_same_chart_replay_adds_normalized_d1_rows(tmp_path: Path, monkeypatch) -> None:
    artifact_root = tmp_path / "vedastro_adapter"
    artifact_root.mkdir()
    artifact = artifact_root / "official_full_snapshot-abc-def.json"
    artifact.write_text(
        json.dumps(
            {
                "status": "ok",
                "raw_response": {"source": "vedastro_official_full_snapshot"},
                "request_manifest": {
                    "requests": [
                        {
                            "body": {
                                "BirthTime": {
                                    "StdTime": "19:15 24/02/1955 -08:00",
                                    "Location": {"Latitude": 37.7749, "Longitude": -122.4194},
                                }
                            }
                        }
                    ]
                },
                "snapshot_sections": {
                    "chart_core": {
                        "Sun": {
                            "Payload": {
                                "AllPlanetData": {
                                    "PlanetNirayanaLongitude": {"TotalDegrees": "312.5122"},
                                    "PlanetRasiD1Sign": {"Name": "Aquarius"},
                                }
                            }
                        }
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(three_engine_parity_runner, "VEDASTRO_ARTIFACT_DIR", artifact_root)

    report = build_public_case_replay(output_dir=tmp_path / "out", allow_vedastro_network=True)
    rows = {(row["section"], row["field"]): row for row in report["comparison_rows"]}

    assert rows[("D1", "Sun.sign")]["status"] == "match"
    assert rows[("D1", "Sun.longitude")]["status"] == "match"
