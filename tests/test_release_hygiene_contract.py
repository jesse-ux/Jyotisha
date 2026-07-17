from pathlib import Path


def test_release_profile_requires_privacy_and_renderer_probes() -> None:
    source = (Path(__file__).resolve().parents[1] / "scripts" / "run_quality_gate.py").read_text(encoding="utf-8")
    assert '"scripts/public_release_privacy_scan.py", "--json"' in source
    assert '"scripts/report_renderer_isolation_poc.py", "--strict"' in source
    assert '"scripts/three_engine_parity_replay_validator.py"' in source
    assert '"--require-external-parity"' in source
    assert 'parity_command.append("--require-pass")' in source
