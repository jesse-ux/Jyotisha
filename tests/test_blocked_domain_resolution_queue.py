import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ARTIFACT = ROOT / "references/oracle/blocked_domain_resolution_queue_2026_07_20.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_blocked_domain_resolution_queue_covers_all_current_blocked_domains():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/blocked_domain_resolution_queue.py", "--date", "2026-07-20"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "blocked_domain_resolution_queue"
    assert data["created_at"] == "2026-07-20"
    assert data["summary"]["blocked_domain_count"] >= 10
    assert data["summary"]["cannot_be_closed_by_code_only_count"] >= 6
    assert data["production_tuning_allowed"] is False


def test_blocked_domain_resolution_queue_marks_hard_external_and_human_dependencies():
    data = json.loads(ARTIFACT.read_text(encoding="utf-8"))
    by_domain = {row["domain"]: row for row in data["domains"]}
    assert by_domain["timing_holdout"]["hard_dependency"] == "independent_human_labels"
    assert by_domain["external_oracle_identity"]["hard_dependency"] == "upstream_build_identity"
    assert by_domain["three_engine_parity"]["local_next_action"] == "continue_field_level_attribution"
    assert by_domain["worked_example_collection"]["hard_dependency"] == "public_numeric_worked_examples"


def test_blocked_domain_resolution_queue_is_indexed():
    packets = {row["packet_id"]: row for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]}
    assert packets["blocked_domain_resolution_queue_2026_07_20"]["claim_status"] == "open_queue"
