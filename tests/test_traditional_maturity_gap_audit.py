from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_traditional_maturity_gap_audit_keeps_covered_not_complete_boundary() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/traditional_maturity_gap_audit.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert "covered means" in report["boundary"]
    assert [phase["id"] for phase in report["execution_phases"]] == [
        "phase_1_truth_boundary",
        "phase_2_oracle_expansion",
        "phase_3_event_adjudication",
        "phase_4_expert_modifiers",
    ]
    assert report["ordered_priorities"][0]["id"] == "p0_dasha_boundary_closure"
    assert report["ordered_priorities"][-1]["id"] == "p2_article_template_industrialization"
    assert report["summary"]["P0"] >= 3
    assert any(item["id"] == "p0_dasha_boundary_closure" for item in report["p0"])
    assert any(item["id"] == "p0_tajika_sahams_annual_templates" for item in report["p0"])
    assert any(item["id"] == "p1_kp_event_adjudication" for item in report["p1"])
    assert any(item["id"] == "p1_career_a10_karakamsha_amk_chain" for item in report["p1"])
    assert any(item["id"] == "p1_flying_star_chain" for item in report["p1"])
