from __future__ import annotations

import json
from pathlib import Path

from scripts.jyotishganit_shadbala_surface_probe import (
    PUBLIC_CASE_LATITUDE as SHADBALA_LATITUDE,
    PUBLIC_CASE_LONGITUDE as SHADBALA_LONGITUDE,
)
from scripts.jyotishganit_vs_local_field_comparison import (
    PUBLIC_CASE_LATITUDE as FIELD_LATITUDE,
    PUBLIC_CASE_LONGITUDE as FIELD_LONGITUDE,
)
from scripts.three_engine_parity_runner import PUBLIC_CASE


ROOT = Path(__file__).resolve().parents[1]


def test_steve_jobs_probe_defaults_share_the_three_engine_input() -> None:
    assert (SHADBALA_LATITUDE, SHADBALA_LONGITUDE) == (PUBLIC_CASE["lat"], PUBLIC_CASE["lon"])
    assert (FIELD_LATITUDE, FIELD_LONGITUDE) == (PUBLIC_CASE["lat"], PUBLIC_CASE["lon"])


def test_mislabeled_legacy_oracle_is_explicitly_invalidated() -> None:
    artifact = json.loads(
        (ROOT / "references/oracle/jyotishganit_shadbala_surface_probe_steve_jobs_2026_07_19.json")
        .read_text(encoding="utf-8")
    )

    assert artifact["claim_status"] == "invalidated_input_mismatch"
    assert artifact["production_tuning_allowed"] is False
    assert artifact["invalidation"]["required_coordinates"] == [37.7749, -122.4194]
