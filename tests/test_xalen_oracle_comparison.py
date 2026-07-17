from pathlib import Path
from scripts.xalen_oracle_comparison import compare

ROOT=Path(__file__).resolve().parents[1]

def test_xalen_compares_all_high_rigor_rows_as_fourth_observation() -> None:
    report=compare(ROOT/"references/oracle/three_engine_parity_replay_manifest.json",ROOT/"references/oracle/artifacts/xalen_steve_jobs_high_rigor_raw.json")
    assert report["row_count"] == 92
    assert report["match_count"] + report["mismatch_count"] == 92
    assert report["truth_policy"] == "fourth_observation_not_truth"
    assert report["license"] == "Apache-2.0"
