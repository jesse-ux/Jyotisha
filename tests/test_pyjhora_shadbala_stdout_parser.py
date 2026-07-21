import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PACKET = ROOT / "references/oracle/pyjhora_steve_jobs_shadbala_stdout_components_2026_07_21.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_parser_extracts_42_same_unit_component_rows():
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/parse_pyjhora_shadbala_stdout.py"],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "pyjhora_shadbala_stdout_component_packet"
    assert data["claim_status"] == "observation_only"
    assert data["truth_matrix_allowed"] is False
    assert data["summary"]["component_row_count"] == 42
    assert data["summary"]["planet_count"] == 7
    assert data["summary"]["component_count"] == 6
    first = data["component_rows"][0]
    assert {"planet", "component", "virupa", "rupa", "source_artifact_sha256"} <= set(first)


def test_packet_is_stable_and_indexed_after_capture():
    data = json.loads(PACKET.read_text(encoding="utf-8"))
    assert data["summary"]["component_row_count"] == 42
    assert data["source_artifact"].endswith("pyjhora_steve_jobs_shadbala_lahiri_stdout_20260627.txt")
    packets = {
        row["packet_id"]: row
        for row in json.loads(INDEX.read_text(encoding="utf-8"))["packets"]
    }
    assert packets["pyjhora_steve_jobs_shadbala_stdout_components_2026_07_21"]["claim_status"] == "observation_only"
