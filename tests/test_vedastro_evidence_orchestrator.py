from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vedastro_evidence_orchestrator_routes_to_minimal_domain_set(monkeypatch) -> None:
    from scripts import vedastro_evidence_orchestrator as orchestrator

    calls = []

    def fake_scan(case, domain, start_date, end_date, case_id):
        calls.append((domain, start_date, end_date, case_id, case["year"]))
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": True,
            "status": "ok",
            "operation": "range_scan",
            "domain": domain,
            "event_count": 1,
            "evidence_ledger": [{"domain": domain, "event_id": f"{domain}_event"}],
            "source_metadata": {"endpoint_host": "api.vedastro.org"},
        }

    monkeypatch.setattr(orchestrator, "run_range_scan_for_case", fake_scan)

    result = orchestrator.orchestrate_vedastro_evidence(
        {
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "lat": 36.42,
            "lon": 114.2,
            "tz": 8.0,
        },
        route="relationship",
        reference_date="2026-06-29",
    )

    assert [call[0] for call in calls] == ["marriage"]
    assert result["source_metadata"]["auto_ingested_by"] == "VedAstroEvidenceOrchestrator"
    assert result["source_metadata"]["node_coverage"]["strategy"] == "domain_scoped_range_scan"
    assert result["event_count"] == 1


def test_api_and_mcp_use_shared_vedastro_evidence_orchestrator() -> None:
    api = (ROOT / "scripts" / "jyotish_api_server.py").read_text(encoding="utf-8")
    mcp = (ROOT / "mcp_server.py").read_text(encoding="utf-8")

    assert "vedastro_evidence_orchestrator" in api
    assert "orchestrate_vedastro_evidence" in api
    assert "vedastro_evidence_orchestrator" in mcp
    assert "orchestrate_vedastro_evidence" in mcp
