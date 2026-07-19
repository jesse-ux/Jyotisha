from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.day_level_holdout_template import build_template

ROOT = Path(__file__).resolve().parents[1]


def test_holdout_template_is_nontechnical_and_validator_compatible_shape() -> None:
    template = build_template()
    annotation = template["annotation"]

    for token in [
        "case_id",
        "subject",
        "domain",
        "label",
        "start",
        "end",
        "event_absent_assertion",
        "source_url",
        "adjudicator",
        "independent_human_reviewed",
        "frozen_before_scoring",
    ]:
        assert token in annotation

    assert "Do not use old control dates" in " ".join(template["instructions"])
    assert annotation["source_url"] == "https://"
    assert annotation["independent_human_reviewed"] is True


def test_holdout_template_cli_writes_json(tmp_path: Path) -> None:
    output = tmp_path / "template.json"

    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / "day_level_holdout_template.py"), "--output", str(output)],
        check=True,
        text=True,
    )

    data = json.loads(output.read_text(encoding="utf-8"))
    assert data["template_type"] == "day_level_holdout_annotation_v3"
    assert data["annotation"]["label"] == "target_event|no_target_event"
