from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ERROR_LEDGER = ROOT / "docs" / "research" / "pre_work_error_ledger.md"
SWEEP = ROOT / "docs" / "research" / "whole_machine_fragment_sweep_2026_07_05.md"


def test_pre_work_error_ledger_exists_and_names_repeat_failures() -> None:
    text = ERROR_LEDGER.read_text(encoding="utf-8")
    required = [
        "ERR-001",
        "ERR-005",
        "ERR-007",
        "ERR-009",
        "ERR-017",
        "ERR-018",
        "ERR-019",
        "tests/test_runtime_import_boundaries.py",
        "tests/test_project_fragment_governance.py",
        "tests/test_user_invocation_acceptance_contract.py",
        "docs/research/whole_machine_fragment_sweep_round25_2026_06_25.md",
        "scripts/diagnose_external_engine_adapters.py --json",
        "docs/research/external_engine_blocker_research_2026_07_05.md",
        "docs/research/user_invocation_acceptance_error_log_2026_07_06.md",
    ]
    missing = [item for item in required if item not in text]
    assert missing == []


def test_agents_requires_pre_work_error_ledger() -> None:
    text = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    assert "docs/research/pre_work_error_ledger.md" in text
    assert "开工前" in text
    assert "python3 scripts/pre_work_check.py --remote-timeout 8 --command-timeout 45" in text
    assert "scripts/diagnose_external_engine_adapters.py --json" in text


def test_fragment_sweep_records_main_mirror_and_remote_boundaries() -> None:
    text = SWEEP.read_text(encoding="utf-8")
    required = [
        "/Users/wuyongnaren/Documents/印度占星",
        "/Users/wuyongnaren/.workbuddy/skills/jyotish-vedic-astrology",
        "/Users/wuyongnaren/Documents/星轨talk/engines-repo/jyotish",
        "github.com:732642856/yinduzhanxing.git",
        "SSL_ERROR_SYSCALL",
        "terminal ref parity is `blocked`",
    ]
    missing = [item for item in required if item not in text]
    assert missing == []


def test_error_ledger_contains_split_scan_commands_not_unbounded_home_scan() -> None:
    text = ERROR_LEDGER.read_text(encoding="utf-8")
    assert "-maxdepth 6" in text
    assert "-maxdepth 7" in text
    assert "find /Users/wuyongnaren -type" not in text
