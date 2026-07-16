from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import career_vedastro_radar  # noqa: E402


def test_career_radar_wraps_vedastro_range_scan_as_secondary_evidence(monkeypatch) -> None:
    def fake_run(case, domain, start_date, end_date, case_id="user_chart"):
        return {
            "status": "ok",
            "domain": domain,
            "operation": "range_scan",
            "evidence_ledger": [{"event_id": "CareerExpansionWindow", "date": "2026-09-01"}],
            "adjudicator_policy": {"can_change_score": False},
        }

    monkeypatch.setattr(career_vedastro_radar.vedastro_service_adapter, "run_range_scan_for_case", fake_run)

    packet = career_vedastro_radar.build_career_radar_packet(
        {"year": 1990, "month": 1, "day": 1, "hour": 12, "minute": 0, "lat": 36.4, "lon": 114.2, "tz": 8},
        start_date="2026-07-16",
        end_date="2026-12-31",
    )

    assert packet["status"] == "ok"
    assert packet["domain"] == "career"
    assert packet["adjudicator_use"] == "secondary_evidence_only"
    assert packet["can_change_score"] is False
    assert packet["vedastro_range_scan_result"]["evidence_ledger"][0]["event_id"] == "CareerExpansionWindow"


def test_career_radar_preserves_blocked_boundary(monkeypatch) -> None:
    def fake_run(case, domain, start_date, end_date, case_id="user_chart"):
        return {"status": "blocked", "reason": "official_endpoint_not_configured", "evidence_ledger": []}

    monkeypatch.setattr(career_vedastro_radar.vedastro_service_adapter, "run_range_scan_for_case", fake_run)

    packet = career_vedastro_radar.build_career_radar_packet(
        {"year": 1990, "month": 1, "day": 1, "hour": 12, "minute": 0, "lat": 36.4, "lon": 114.2, "tz": 8},
        start_date="2026-07-16",
        end_date="2026-12-31",
    )

    assert packet["status"] == "blocked"
    assert packet["can_change_score"] is False
    assert packet["blocked_reason"] == "official_endpoint_not_configured"
