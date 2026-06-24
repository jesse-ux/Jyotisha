"""Pytest import guardrails for local project modules."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = str(ROOT / "scripts")
WORKBUDDY_SKILL_SCRIPTS = ".workbuddy/skills/jyotish-vedic-astrology/scripts"


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


ensure_project_scripts_first()
