"""Pytest import guardrails for local project modules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
WORKBUDDY_SKILL_SCRIPTS = ".workbuddy/skills/jyotish-vedic-astrology/scripts"
SLOW_API_SECURITY_PREFIXES = (
    "test_vedastro_",
    "test_high_rigor_",
    "test_professional_reading",
    "test_api_prompt_pack",
    "test_consultation_workflow",
    "test_thematic_report",
    "test_capability_audit",
    "test_technique_catalog",
)


def ensure_project_scripts_first() -> None:
    if SCRIPTS in sys.path:
        sys.path.remove(SCRIPTS)
    sys.path.insert(0, SCRIPTS)


def remove_workbuddy_shadow_modules() -> None:
    for name, module in list(sys.modules.items()):
        module_file = getattr(module, "__file__", "") or ""
        if WORKBUDDY_SKILL_SCRIPTS in module_file:
            del sys.modules[name]


def pytest_runtest_setup() -> None:
    remove_workbuddy_shadow_modules()
    ensure_project_scripts_first()


def pytest_collection_modifyitems(items) -> None:
    for item in items:
        if item.fspath.basename == "test_api_server_security.py" and item.name.startswith(SLOW_API_SECURITY_PREFIXES):
            item.add_marker("slow")


ensure_project_scripts_first()
