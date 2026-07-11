from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from three_engine_parity_runner import build_public_case_replay  # noqa: E402


def test_public_same_chart_replay_never_promotes_missing_vedastro_raw(tmp_path: Path) -> None:
    report = build_public_case_replay(output_dir=tmp_path, allow_vedastro_network=False)

    assert report["case_id"] == "steve_jobs_public_1955_lahiri"
    assert report["birth_data_policy"] == "public_case_only"
    assert report["engines"]["PyJHora_JHora"]["status"] == "raw_imported"
    assert report["engines"]["jyotishganit"]["status"] == "raw_captured"
    assert report["engines"]["VedAstro"]["status"] == "blocked"
    assert report["status"] in {"partial", "blocked"}
    assert report["tested"] is False
    assert report["comparison_rows"]
    assert all(row["status"] in {"blocked", "not_comparable"} for row in report["comparison_rows"])
