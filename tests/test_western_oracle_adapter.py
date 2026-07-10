#!/usr/bin/env python3
"""Western external-oracle adapter tests."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from scripts.western_oracle_adapter import build_packet_from_oracle_payload

ROOT = Path(__file__).resolve().parents[1]


def test_western_oracle_adapter_maps_external_aspects_to_standard_signals() -> None:
    packet = build_packet_from_oracle_payload(
        {
            "source_engine": "kerykeion_external_json",
            "natal": {"ascendant": "Virgo", "mc": "Gemini"},
            "timing_techniques": {"solar_return": {"annual_focus": "career"}},
            "aspects": [
                {
                    "date": "2026-07-07",
                    "planet": "Uranus",
                    "aspect": "conjunction",
                    "target": "MC",
                    "orb": 0.2,
                },
                {
                    "date": "2026-07-20",
                    "planet": "Jupiter",
                    "aspect": "trine",
                    "target": "Venus",
                    "orb": 0.4,
                },
                {
                    "date": "2027-07-14",
                    "planet": "Saturn",
                    "aspect": "conjunction",
                    "target": "Sun",
                    "orb": 0.1,
                },
            ],
        },
        route_packet={"question_type": "career", "primary_theme": "career"},
    )

    assert packet["status"] == "complete"
    assert packet["source_engine"] == "kerykeion_external_json"
    claims = {signal["claim"] for signal in packet["signals"]}
    assert "career_triggered_relocation" in claims
    assert "client_cooperation_opportunity" in claims
    assert "career_responsibility_test" in claims
    assert packet["adapter_boundary"]["bundles_external_code"] is False


def test_western_oracle_adapter_preserves_explicit_signals() -> None:
    packet = build_packet_from_oracle_payload(
        {
            "source_engine": "manual_astro_com_export",
            "natal": {"ascendant": "Virgo"},
            "timing_techniques": {"transits": []},
            "signals": [
                {
                    "theme": "career",
                    "claim": "external_project_pivot",
                    "timing": "2026-07",
                    "source": "manual review",
                }
            ],
        },
        route_packet={"question_type": "career", "primary_theme": "career"},
    )

    assert packet["signals"] == [
        {
            "theme": "career",
            "claim": "external_project_pivot",
            "timing": "2026-07",
            "source": "manual review",
        }
    ]


def test_western_oracle_adapter_cli_reads_json_file(tmp_path: Path) -> None:
    input_path = tmp_path / "western_oracle.json"
    input_path.write_text(
        json.dumps(
            {
                "source_engine": "gongshenxing_export",
                "natal": {"ascendant": "Virgo", "mc": "Gemini"},
                "aspects": [{"date": "2026-07-07", "planet": "Uranus", "aspect": "conj", "target": "MC"}],
            }
        ),
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            "scripts/western_oracle_adapter.py",
            "--input",
            str(input_path),
            "--theme",
            "career",
            "--question-type",
            "career",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    packet = json.loads(completed.stdout)
    assert packet["source_engine"] == "gongshenxing_export"
    assert packet["signals"][0]["claim"] == "career_triggered_relocation"
