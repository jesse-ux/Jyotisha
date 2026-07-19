import json
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_evidence_packet_index_integrity_validator_passes_current_index() -> None:
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/evidence_packet_index_integrity.py", "--index", str(INDEX)],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["scope"] == "evidence_packet_index_integrity"
    assert data["status"] == "pass"
    assert data["summary"]["packet_count"] >= 60
    assert data["summary"]["missing_path_count"] == 0
    assert data["summary"]["duplicate_packet_id_count"] == 0
    assert data["summary"]["invalid_claim_status_count"] == 0


def test_evidence_packet_index_integrity_reports_bad_index(tmp_path: Path) -> None:
    bad = tmp_path / "bad_index.json"
    bad.write_text(
        json.dumps(
            {
                "packets": [
                    {
                        "packet_id": "dup",
                        "path": "references/oracle/missing_packet.json",
                        "domain": "timing_holdout",
                        "claim_status": "done",
                        "consumer_policy": "research",
                        "claim_boundary": "",
                    },
                    {
                        "packet_id": "dup",
                        "path": "references/oracle/evidence_packet_index_2026_07_19.json",
                        "domain": "timing_holdout",
                        "claim_status": "partial",
                        "consumer_policy": "research",
                        "claim_boundary": "ok",
                    },
                ]
            }
        ),
        encoding="utf-8",
    )
    data = json.loads(
        subprocess.check_output(
            ["python3", "scripts/evidence_packet_index_integrity.py", "--index", str(bad)],
            cwd=ROOT,
            text=True,
        )
    )
    assert data["status"] == "fail"
    assert data["summary"]["missing_path_count"] == 1
    assert data["summary"]["duplicate_packet_id_count"] == 1
    assert data["summary"]["invalid_claim_status_count"] == 1
