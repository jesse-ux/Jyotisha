#!/usr/bin/env python3
"""Regression tests for the minimal VedAstro ingestion closure pack."""

from __future__ import annotations

from scripts.vedastro_ingestion_closure_pack import build_report


def test_vedastro_ingestion_closure_pack_reuses_blocked_and_allowlisted_paths() -> None:
    report = build_report()

    assert report["scope"] == "vedastro_ingestion_closure_pack"
    assert report["summary"]["range_scan_domains"] == ["career", "marriage", "wealth"]
    assert report["summary"]["schema_declares_allowlist"] is True
    assert report["summary"]["unconfigured_status"] == "service_endpoint_not_configured"
    assert report["summary"]["network_preview_status"] == "network_execution_disabled"
    assert report["summary"]["life_event_graph_accepts_external_window"] is True
    assert report["summary"]["global_live_closure_blocked"] is True
