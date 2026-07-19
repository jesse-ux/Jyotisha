import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/deep_fragment_oss_reuse_gate_round2_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def _packet():
    return json.loads(PACKET.read_text(encoding="utf-8"))


def test_deep_fragment_gate_records_current_machine_scope():
    data = _packet()
    assert data["scope"] == "deep_fragment_oss_reuse_gate_round2"
    assert data["claim_status"] == "ready_contract"
    assert data["production_tuning_allowed"] is False
    assert data["truth_matrix_allowed"] is False
    assert "/Users/wuyongnaren/Documents" in data["scanned_roots"]
    assert "/private/tmp" in data["scanned_roots"]


def test_deep_fragment_gate_keeps_dangerous_fragments_quarantined():
    data = _packet()
    fragments = {row["path"]: row for row in data["local_fragments"]}
    assert fragments["/tmp/jyotisha-commercial-readonly.adiUr0/hip_main.dat"]["action"].startswith("quarantine")

    repos = {row["path"]: row for row in data["active_repositories"]}
    assert repos["/Users/wuyongnaren/.workbuddy/backups/jyotish-vedic-astrology-20260711-154109"]["action"] == "read_only_do_not_bulk_copy"
    assert repos["/private/tmp/vedicastro_diliprk_flatlib_src_1784467988"]["action"] == "dependency_identity_only_do_not_vendor"


def test_deep_fragment_gate_reuses_oss_without_license_drift():
    data = _packet()
    policies = {row["project"]: row for row in data["oss_reuse_policy"]}
    assert policies["naturalstupid/PyJHora"]["license_boundary"] == "AGPL-3.0"
    assert "copy code" in policies["naturalstupid/PyJHora"]["blocked_use"]
    assert "same-chart field observation" in policies["northtara/jyotishganit"]["allowed_use"]
    assert "KP runtime raw/hash probe in isolated dependency path" in policies[
        "diliprk/VedicAstro + diliprk/flatlib@sidereal"
    ]["allowed_use"]


def test_deep_fragment_gate_orders_remaining_tasks_by_reusable_sources():
    data = _packet()
    tasks = {row["task"]: row for row in data["next_actions_ordered"]}
    assert tasks["Shadbala component closure"]["priority"] == "P0"
    assert "shadbala_same_unit_normalizer" in tasks["Shadbala component closure"]["reuse_first"]
    assert tasks["KP cusp worked-example oracle queue"]["priority"] == "P0"
    assert "vedicastro_kp_cusp_batch_probe" in tasks["KP cusp worked-example oracle queue"]["reuse_first"]
    assert tasks["day-level holdout"]["priority"] == "P2"


def test_deep_fragment_gate_is_registered_in_evidence_index():
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    assert packets["deep_fragment_oss_reuse_gate_round2"]["claim_status"] == "ready_contract"
