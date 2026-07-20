import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts.jyotish_api_server import BadRequest, JyotishAPIHandler


ROOT = Path(__file__).resolve().parents[1]


def test_cli_prashna_uses_question_moment_swiss_context_only():
    result = subprocess.run([
        sys.executable, "scripts/jyotish_engine.py", "prashna",
        "--datetime", "2026-07-12T12:00:00+08:00", "--question-text", "Test question",
        "--lat", "39.9042", "--lon", "116.4074", "--timezone", "8",
    ], cwd=ROOT, text=True, capture_output=True, timeout=30, check=True)
    payload = json.loads(result.stdout)

    assert payload["status"] == "computed"
    assert payload["chart_source"] == "swiss_ephemeris_backend"
    assert payload["supporting_indicators"]["gulika"]["status"] == "partial"
    assert payload["supporting_indicators"]["sphuta"]["status"] == "partial"
    assert "Kunda" in payload["blocked_layers"]


def test_cli_prashna_blocks_legacy_approximation_modes():
    result = subprocess.run([
        sys.executable, "scripts/jyotish_engine.py", "prashna",
        "--datetime", "2026-07-12T12:00:00+08:00", "--question-text", "Test question",
        "--lat", "39.9042", "--lon", "116.4074", "--timezone", "8", "--mode", "sphutas",
    ], cwd=ROOT, text=True, capture_output=True, timeout=30, check=True)
    payload = json.loads(result.stdout)

    assert payload["status"] == "blocked"
    assert "sphutas" in payload["reason"]


def test_api_prashna_rejects_client_planets_and_computes_context():
    handler = JyotishAPIHandler.__new__(JyotishAPIHandler)
    body = {
        "question_text": "Test question", "question_timestamp": "2026-07-12T12:00:00+08:00",
        "lat": 39.9042, "lon": 116.4074, "timezone": 8,
        "ayanamsa": "lahiri", "node_mode": "mean", "location_convention": "wgs84",
    }
    result = handler._compute_prashna(body)
    assert result["prashna_context"]["chart_source"] == "swiss_ephemeris_backend"
    with pytest.raises(BadRequest, match="forbidden"):
        handler._compute_prashna({**body, "planets": {"Sun": 0}})
