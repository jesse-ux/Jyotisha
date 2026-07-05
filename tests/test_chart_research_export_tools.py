#!/usr/bin/env python3
"""Regression tests for report export and CLI entrypoints."""

from __future__ import annotations

import subprocess
import sys
from shutil import which
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader


ROOT = Path(__file__).resolve().parents[1]
REPORT_ROOT = ROOT / "docs" / "reports" / "chart_research_REDACTED_DATE_REDACTED_TIME"


def test_historical_event_backtest_cli_help_runs_from_repo_root() -> None:
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/historical_event_backtest.py",
            "--help",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert "historical-event backtest" in (completed.stdout + completed.stderr).lower()


def test_chart_research_pdf_export_generates_readable_pdf(tmp_path: Path) -> None:
    output_pdf = tmp_path / "chart_research.pdf"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/export_chart_research_pdf.py",
            "--report-root",
            str(REPORT_ROOT),
            "--output",
            str(output_pdf),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    assert output_pdf.exists()
    assert output_pdf.stat().st_size > 0

    reader = PdfReader(str(output_pdf))
    assert len(reader.pages) >= 3

    first_page = reader.pages[0].extract_text() or ""
    all_text = "\n".join((page.extract_text() or "") for page in reader.pages[:5])
    assert "B.V. Raman" in first_page or "B.V. Raman" in all_text
    assert "Executive Synthesis" in all_text or "Birth Data" in all_text


@pytest.mark.skipif(which("pdftoppm") is None, reason="pdftoppm not installed")
def test_chart_research_pdf_export_renders_visible_first_page(tmp_path: Path) -> None:
    output_pdf = tmp_path / "chart_research.pdf"
    export = subprocess.run(
        [
            sys.executable,
            "scripts/export_chart_research_pdf.py",
            "--report-root",
            str(REPORT_ROOT),
            "--output",
            str(output_pdf),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert export.returncode == 0, export.stderr or export.stdout

    png_prefix = tmp_path / "chart_research_page_1"
    render = subprocess.run(
        [
            "pdftoppm",
            "-png",
            "-f",
            "1",
            "-singlefile",
            str(output_pdf),
            str(png_prefix),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=60,
        check=False,
    )
    assert render.returncode == 0, render.stderr or render.stdout

    first_page_png = png_prefix.with_suffix(".png")
    assert first_page_png.exists()

    img = Image.open(first_page_png).convert("L")
    dark_pixels = sum(1 for pixel in img.getdata() if pixel < 250)
    assert dark_pixels > 1000
