from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/full_technique_invocation_matrix_2026_07_22.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


@pytest.fixture(scope="module")
def matrix_packet() -> dict:
    subprocess.run(
        [sys.executable, "scripts/full_technique_invocation_matrix.py"],
        cwd=ROOT,
        check=True,
        text=True,
        capture_output=True,
    )
    return json.loads(PACKET.read_text(encoding="utf-8"))


def test_full_matrix_scans_all_required_runtime_layers(matrix_packet: dict) -> None:
    data = matrix_packet
    assert data["scope"] == "full_technique_invocation_matrix"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert "not numeric oracle closure" in data["boundary"]
    assert set(data["scan_roots"]) == {"skill", "api", "ui", "scripts", "references", "tests"}
    assert data["summary"]["technique_count"] >= 50
    assert data["summary"]["top50_count"] > 0


def test_first_batch_contains_requested_technique_families(matrix_packet: dict) -> None:
    data = matrix_packet
    first_batch = {row["technique_id"]: row for row in data["first_batch_execution_queue"]}
    required = {
        "ul_arudha_upapada",
        "a7_arudha_relationship",
        "a10_arudha_career",
        "kp_exact_cusp",
        "kp_star_sub_sub",
        "shadbala_chesta",
        "shadbala_sthana",
        "muhurta",
        "tarabala",
        "chandrabala",
        "rahu_kalam",
        "abhijit_muhurta",
        "prashna",
        "sphuta",
        "gulika",
        "saham",
        "tajika",
    }
    assert required <= set(first_batch)
    for key in required:
        assert first_batch[key]["first_batch_requested"] is True
        assert first_batch[key]["priority_batch"] in {"P0", "P1"}
        assert first_batch[key]["claim_boundary"]
    batched = {
        row["technique_id"]
        for bucket in ("P0_first_batch_requested", "P1_first_batch_requested")
        for row in data["migration_batches"][bucket]
    }
    assert required <= batched
    assert data["migration_batches"]["P2_deferred"]


def test_top50_tracks_material_that_is_not_fully_invoked(matrix_packet: dict) -> None:
    data = matrix_packet
    top50 = data["top50_material_not_invoked"]
    assert 1 <= len(top50) <= 50
    for row in top50:
        assert row["has_material"] is True
        assert row["has_material_but_not_fully_invoked"] is True
        assert row["missing_integration"]
        assert row["priority_score"] > 0
    top_ids = {row["technique_id"] for row in top50}
    assert {"kp_exact_cusp", "shadbala_chesta", "muhurta"} & top_ids


def test_blocked_claims_do_not_upgrade_truth_or_commercial_policy(matrix_packet: dict) -> None:
    data = matrix_packet
    rows = {row["technique_id"]: row for row in data["rows"]}
    for key in ("kp_exact_cusp", "kp_star_sub_sub", "prashna", "sphuta", "gulika", "saham", "tajika"):
        assert rows[key]["claim_status"] == "blocked_or_observation_only"
        assert rows[key]["commercial_sync_policy"] == "sync_observation_or_boundary_contract_only"
    assert rows["shadbala_chesta"]["claim_status"] == "component_partial"
    assert rows["shadbala_sthana"]["claim_status"] == "component_partial"
    assert "component-level" in rows["shadbala_chesta"]["claim_boundary"]


def test_full_matrix_packet_is_indexed_without_truth_upgrade() -> None:
    index = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {row["packet_id"]: row for row in index["packets"]}
    packet = packets["full_technique_invocation_matrix_2026_07_22"]
    assert packet["claim_status"] == "open_queue"
    assert packet["consumer_policy"] == "research_planning_only"
    assert "does not upgrade" in packet["claim_boundary"]
    assert index["summary"]["packet_count"] == len(index["packets"])
