from pathlib import Path


def test_high_rigor_workflow_exposes_external_parity_for_plan_and_execution() -> None:
    source = (Path(__file__).resolve().parents[1] / "scripts" / "jyotish_api_server.py").read_text(encoding="utf-8")

    assert source.count("'high_rigor_external_parity'") >= 2
    assert source.count("'external_parity_not_passed'") >= 2
    assert "'external_parity_gate': external_parity_gate" in source
