from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_skill_and_plugin_default_to_guided_topics_when_user_has_no_question() -> None:
    skill = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    plugin = json.loads((ROOT / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    default_prompt = "\n".join(plugin["interface"]["defaultPrompt"])

    for text in (skill, readme, default_prompt):
        assert "guided_topics" in text
        assert "strict_workflow" in text
        assert "evidence_packet" in text or "evidence packet" in text
        assert "Technique Audit Table" in text
        assert "scripts/user_invocation_acceptance_check.py" in text

    assert "不要反问" in skill
    assert "不要要求用户自己想问题" in default_prompt
    assert "raw_response" in default_prompt


def test_user_entrypoint_can_start_from_guided_topics_prompt() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_user_entrypoint.py",
            "--year",
            "2000",
            "--month",
            "1",
            "--day",
            "1",
            "--hour",
            "12",
            "--minute",
            "0",
            "--lat",
            "0.0",
            "--lon",
            "0.0",
            "--tz",
            "0",
            "--question",
            "请先生成 guided_topics 并推荐我最值得看的问题",
            "--themes",
            "career,marriage,wealth",
            "--reference-date",
            "2026-07-06",
            "--format",
            "json",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env={
            **os.environ,
            "JYOTISH_SKIP_LOCAL_ENV": "1",
            "VEDASTRO_API_ENDPOINT": "",
            "VEDASTRO_ENABLE_NETWORK": "",
            "VEDASTRO_TIMEOUT_SECONDS": "",
        },
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["strict_workflow"]["triggered"] is True
    assert report["strict_workflow"]["routes_available"]
    assert report["runtime_mode"]["expected_fallback_status"] in {
        "none_if_official_endpoint_responds",
        "official_snapshot_budget_exhausted_or_endpoint_blocked",
    }
    assert report["honesty_boundary"]["all_641_methods_executed"] is False
    assert report["input"]["question"] == "请先生成 guided_topics 并推荐我最值得看的问题"


def test_fixture_dasha_timeline_rejects_workbuddy_regression_claims() -> None:
    base = [
        sys.executable,
        "scripts/jyotish_engine.py",
        "dasha",
        "--year",
        "2000",
        "--month",
        "1",
        "--day",
        "1",
        "--hour",
        "12",
        "--minute",
        "0",
        "--lat",
        "0.0",
        "--lon",
        "0.0",
        "--tz",
        "0",
        "--years",
        "45",
    ]

    observed = {}
    for today in ("2014-06-15", "2024-03-01", "2027-03-01"):
        completed = subprocess.run(
            [*base, "--today", today],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )
        assert completed.returncode == 0, completed.stderr or completed.stdout
        current = json.loads(completed.stdout)["current_dasha"]
        observed[today] = (
            current["mahadasha"],
            current["antardasha"]["lord"],
            current["antardasha"]["start"],
            current["antardasha"]["end"],
        )

    assert observed["2014-06-15"] == ("Jupiter", "Rahu", "2014-04-27", "2016-09-20")
    assert observed["2024-03-01"] == ("Saturn", "Venus", "2023-07-12", "2026-09-11")
    assert observed["2027-03-01"] == ("Saturn", "Sun", "2026-09-11", "2027-08-24")


def test_one_command_user_invocation_acceptance_check() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/user_invocation_acceptance_check.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "pass"
    assert report["checks"]["user_invocation_tests"] is True
    assert report["checks"]["guided_topics_entrypoint"] is True
    assert report["checks"]["external_adapter_diagnostics"] is True
    assert report["external_adapter_status"] in {"pass", "partial", "complete"}
