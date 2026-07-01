from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vedastro_evidence_orchestrator_routes_to_minimal_domain_set(monkeypatch) -> None:
    from scripts import vedastro_evidence_orchestrator as orchestrator

    calls = []

    def fake_snapshot(case, *, case_id="user_chart"):
        return {
            "backend": "vedastro_service_adapter_candidate",
            "available": True,
            "status": "ok",
            "operation": "official_full_snapshot",
            "primary_source": "vedastro_official",
            "snapshot_sections": {"chart_core": {}, "house_core": {}},
            "source_metadata": {
                "official_python_path": "vedastro_official_capability_runner",
                "official_python_bundle": {
                    "status": "ok",
                    "coverage": {"source_mode": "official_capability_runner_bundle"},
                },
                "official_full_capability_catalog": {
                    "status": "partial",
                    "summary": {"catalog_method_count": 641, "executed_method_count": 80},
                    "domain_routing": {
                        "marriage": {
                            "method_count": 8,
                            "auto_method_count": 5,
                            "needs_user_context_count": 1,
                            "needs_user_text_count": 0,
                            "blocked_method_count": 2,
                            "high_priority_methods": ["SearchEvents", "DasaAtRange"],
                        }
                    },
                    "dynamic_selection": {
                        "marriage": {
                            "requested_theme": "marriage",
                            "selected_methods": [
                                {"method": "SearchEvents", "citation_id": "vedastro:marriage:SearchEvents", "execution_policy": "auto"},
                            ],
                            "needs_user_context_methods": [
                                {"method": "MatchReport", "citation_id": "vedastro:marriage:MatchReport", "execution_policy": "needs_user_context"},
                            ],
                            "report_reference": {
                                "theme": "marriage",
                                "citation_ids": ["vedastro:marriage:SearchEvents"],
                                "auto_count": 1,
                                "needs_user_context_count": 1,
                                "blocked_count": 0,
                            },
                        }
                    },
                },
            },
        }

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

    monkeypatch.setattr(orchestrator, "run_official_full_snapshot_for_case", fake_snapshot)
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
    assert result["source_metadata"]["official_python_path"] == "vedastro_official_capability_runner"
    assert result["source_metadata"]["official_python_bundle_status"] == "ok"
    assert result["source_metadata"]["official_full_capability_catalog_status"] == "partial"
    assert result["source_metadata"]["official_full_capability_catalog_summary"]["catalog_method_count"] == 641
    assert result["source_metadata"]["official_full_capability_domain_routing"]["marriage"]["auto_method_count"] == 5
    assert result["source_metadata"]["official_full_capability_dynamic_selection"]["marriage"]["report_reference"]["auto_count"] == 1
    assert result["source_metadata"]["official_report_references"]["marriage"]["citation_ids"] == ["vedastro:marriage:SearchEvents"]
    assert result["source_metadata"]["node_coverage"]["official_full_capability_theme_routing"] is True
    assert result["source_metadata"]["node_coverage"]["official_full_capability_dynamic_selection"] is True
    assert result["event_count"] == 1


def test_api_and_mcp_use_shared_vedastro_evidence_orchestrator() -> None:
    api = (ROOT / "scripts" / "jyotish_api_server.py").read_text(encoding="utf-8")
    mcp = (ROOT / "mcp_server.py").read_text(encoding="utf-8")

    assert "vedastro_evidence_orchestrator" in api
    assert "orchestrate_vedastro_evidence" in api
    assert "vedastro_evidence_orchestrator" in mcp
    assert "orchestrate_vedastro_evidence" in mcp


def test_vedastro_orchestrator_surfaces_official_section_statuses_and_theme_requirements(monkeypatch) -> None:
    from scripts import vedastro_evidence_orchestrator as orchestrator

    monkeypatch.setattr(
        orchestrator,
        "run_official_full_snapshot_for_case",
        lambda *args, **kwargs: {
            "status": "partial",
            "available": True,
            "official_chart": {"planets": {"Sun": {}}, "ascendant": {"sign": "Leo"}},
            "section_statuses": {"chart_core": "ok", "dasha_all": "ok", "events_overview": "partial"},
            "source_metadata": {},
        },
    )
    monkeypatch.setattr(
        orchestrator,
        "run_range_scan_for_case",
        lambda *args, **kwargs: {
            "status": "ok",
            "available": True,
            "event_count": 1,
            "evidence_ledger": [],
        },
    )

    result = orchestrator.orchestrate_vedastro_evidence(
        {
            "year": REDACTED_YEAR,
            "month": 4,
            "day": 17,
            "hour": 14,
            "minute": 49,
            "lat": 36.42,
            "lon": 114.2,
            "tz": 8,
        },
        route="relationship",
        reference_date="2026-06-29",
    )

    assert result["source_metadata"]["official_section_statuses"]["dasha_all"] == "ok"
    assert result["source_metadata"]["theme_requirements"]["route"] == "relationship"
    assert result["source_metadata"]["theme_requirements"]["requires_dual_dasha"] is True


def test_vedastro_orchestrator_surfaces_daily_windows_by_domain(monkeypatch) -> None:
    from scripts import vedastro_evidence_orchestrator as orchestrator

    monkeypatch.setattr(
        orchestrator,
        "run_official_full_snapshot_for_case",
        lambda *args, **kwargs: {"status": "ok", "source_metadata": {}},
    )
    monkeypatch.setattr(
        orchestrator,
        "run_range_scan_for_case",
        lambda *args, **kwargs: {
            "status": "ok",
            "available": True,
            "event_count": 2,
            "daily_windows": [{"date": "2026-07-18", "domain": "career", "score": 5, "event_count": 2}],
            "top_daily_window": {"date": "2026-07-18", "domain": "career", "score": 5, "event_count": 2},
            "evidence_ledger": [],
        },
    )

    result = orchestrator.orchestrate_vedastro_evidence(
        {"year": REDACTED_YEAR, "month": 4, "day": 17, "hour": 14, "minute": 49, "lat": 36.42, "lon": 114.2, "tz": 8},
        route="career",
        reference_date="2026-06-30",
    )

    assert result["daily_windows_by_domain"]["career"][0]["date"] == "2026-07-18"
    assert result["top_daily_window_by_domain"]["career"]["score"] == 5
