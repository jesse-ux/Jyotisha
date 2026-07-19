from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "scripts/day_level_holdout_intake.py"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def test_day_level_holdout_intake_appends_annotation_and_preserves_blocked_gate(tmp_path: Path) -> None:
    manifest = tmp_path / "holdout.json"
    manifest.write_text(
        json.dumps(
            {
                "benchmark_id": "day_level_timing_holdout_v3",
                "status": "awaiting_independent_labels",
                "prohibited_tuning_data": [],
                "frozen_gate": {
                    "minimum_independent_cases": 20,
                    "minimum_independent_negative_intervals": 80,
                },
                "annotations": [],
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    subprocess.run(
        [
            sys.executable,
            str(INTAKE),
            "--manifest",
            str(manifest),
            "--case-id",
            "pilot_case_001",
            "--domain",
            "career",
            "--label",
            "no_target_event",
            "--start",
            "2020-01-01",
            "--end",
            "2020-01-31",
            "--source-url",
            "https://example.com/source",
            "--adjudicator",
            "human_reviewer",
            "--event-absent-assertion",
            "No target career event found in public timeline for this interval.",
        ],
        check=True,
        cwd=ROOT,
    )
    data = json.loads(manifest.read_text(encoding="utf-8"))
    assert len(data["annotations"]) == 1
    row = data["annotations"][0]
    assert row["independent_human_reviewed"] is True
    assert row["frozen_before_scoring"] is True
    assert data["status"] == "awaiting_independent_labels"


def test_day_level_holdout_intake_is_indexed() -> None:
    data = json.loads(INDEX.read_text(encoding="utf-8"))
    packets = {packet["packet_id"]: packet for packet in data["packets"]}
    assert packets["day_level_holdout_intake"]["path"] == "scripts/day_level_holdout_intake.py"
    assert packets["day_level_holdout_intake"]["claim_status"] == "partial"
