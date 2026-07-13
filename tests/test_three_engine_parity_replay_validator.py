from __future__ import annotations

import hashlib
import json
from pathlib import Path

from scripts.three_engine_parity_replay_validator import validate_manifest

ROOT = Path(__file__).resolve().parents[1]


def test_three_engine_parity_manifest_blocks_without_oracle_rows() -> None:
    result = validate_manifest(ROOT / "references/oracle/three_engine_parity_replay_manifest.json")

    assert result["status"] == "blocked"
    assert result["comparison_row_count"] == 0
    assert result["tested"] is False
    assert result["blocked_reason"] == "no_same_chart_oracle_rows_imported"


def test_three_engine_parity_validator_accepts_one_same_chart_row(tmp_path: Path) -> None:
    raw = tmp_path / "vedastro.json"
    raw.write_text('{"source":"official"}', encoding="utf-8")
    manifest = {
        "case_id": "public_same_chart_001",
        "birth_data_policy": "public_case_only",
        "status": "tested",
        "engines": {
                "VedAstro": {
                    "status": "official_verified",
                    "official_raw_response_path": "vedastro.json",
                    "artifact_hash": hashlib.sha256(raw.read_bytes()).hexdigest(),
                    "settings": {"ayanamsa": "lahiri"},
                },
            "PyJHora_JHora": {"status": "tested", "raw_output_path": "references/oracle/artifacts/pyjhora.txt"},
            "jyotishganit": {"status": "tested", "raw_output_path": "references/oracle/artifacts/jyotishganit.json"},
        },
        "comparison_rows": [
            {
                "section": "D1",
                "field": "Sun.longitude",
                "local_value": 27.1,
                "oracle_values": {"VedAstro": 27.1, "PyJHora_JHora": 27.1, "jyotishganit": 27.1},
                "status": "match",
            }
        ],
    }
    path = tmp_path / "three_engine_parity_replay_manifest.json"
    path.write_text(json.dumps(manifest), encoding="utf-8")

    result = validate_manifest(path)

    assert result["status"] == "pass"
    assert result["tested"] is True
    assert result["comparison_row_count"] == 1
    assert result["match_count"] == 1
