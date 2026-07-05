from __future__ import annotations

from scripts.pre_work_check import (
    DEFAULT_COMMAND_TIMEOUT_SECONDS,
    DEFAULT_FRAGMENT_TIMEOUT_SECONDS,
    EXTERNAL_ENGINE_DIAGNOSTIC_TARGET,
    FOCUSED_TEST_TARGETS,
    PRE_WORK_DOCS,
    classify_status,
)


def test_classify_status_keeps_remote_blocked_distinct_from_failure() -> None:
    assert classify_status(True, True, True, "verified") == "pass"
    assert classify_status(True, True, True, "blocked") == "pass_with_remote_blocked"
    assert classify_status(True, True, False, "verified") == "fail"


def test_pre_work_check_runs_governance_test_set() -> None:
    assert "tests/test_runtime_import_boundaries.py" in FOCUSED_TEST_TARGETS
    assert "tests/test_project_fragment_governance.py" in FOCUSED_TEST_TARGETS
    assert "tests/test_preflight_fragment_scan.py" in FOCUSED_TEST_TARGETS
    assert "tests/test_remote_repo_visibility_check.py" in FOCUSED_TEST_TARGETS
    assert "tests/test_pre_work_check.py" in FOCUSED_TEST_TARGETS


def test_pre_work_check_requires_error_ledger_and_fragment_sweeps() -> None:
    assert "docs/research/pre_work_error_ledger.md" in PRE_WORK_DOCS
    assert "docs/research/whole_machine_fragment_sweep_2026_07_05.md" in PRE_WORK_DOCS
    assert "docs/research/whole_machine_fragment_sweep_round25_2026_06_25.md" in PRE_WORK_DOCS


def test_pre_work_check_includes_external_engine_diagnostics() -> None:
    assert EXTERNAL_ENGINE_DIAGNOSTIC_TARGET == "scripts/diagnose_external_engine_adapters.py"


def test_pre_work_check_child_command_timeout_stays_short() -> None:
    assert DEFAULT_COMMAND_TIMEOUT_SECONDS <= 45
    assert DEFAULT_FRAGMENT_TIMEOUT_SECONDS >= DEFAULT_COMMAND_TIMEOUT_SECONDS
