from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _load(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def test_real_case_calibration_schema_defines_replay_contract() -> None:
    schema = _load("references/real_case_calibration/catalog.schema.json")
    props = schema["properties"]

    assert schema["title"] == "Real Case Calibration Catalog"
    assert {"case_id", "source", "chart_signature", "event_outcomes", "similarity", "replay"} <= set(props)
    assert props["source"]["properties"]["source_grade"]["enum"] == ["primary", "verified_secondary", "forum_claim", "unverified"]
    assert "outcome_replay_status" in props["replay"]["properties"]
    assert "do_not_use_for_prediction" in props["replay"]["properties"]


def test_three_engine_parity_replay_schema_defines_raw_oracle_slots() -> None:
    schema = _load("references/oracle/three_engine_parity_replay.schema.json")
    engines = schema["properties"]["engines"]["properties"]

    assert schema["title"] == "Three Engine Same-Chart Parity Replay"
    assert {"VedAstro", "PyJHora_JHora", "jyotishganit"} <= set(engines)
    assert "official_raw_response_path" in engines["VedAstro"]["properties"]
    assert "raw_output_path" in engines["PyJHora_JHora"]["properties"]
    assert "comparison_rows" in schema["properties"]
    assert "blocked_reason" in schema["properties"]
