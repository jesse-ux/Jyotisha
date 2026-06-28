#!/usr/bin/env python3
"""Regression tests for Life Event Graph v1."""

from __future__ import annotations

from mcp_server import _build_life_event_graph, _collect_strict_evidence


def test_life_event_graph_folds_strict_evidence_and_vedastro_top_event() -> None:
    strict = {
        "question_type": "relationship",
        "event_judgement": {
            "event_family": "relationship",
            "score": 85,
            "verdict": "high_probability_window",
            "dominant_label": "legal_marriage",
            "secondary_context": [
                "darakaraka_active",
                "jaimini_support",
                "ul_support",
                "external_activation_support",
                "synastry_support",
            ],
            "primary_drivers": [
                "marriage_convergence",
                "vimshottari_current",
                "narayana_current",
                "darakaraka",
                "upapada_lagna",
            ],
        },
        "present_evidence": {
            "vimshottari_current": {"mahadasha": "Venus", "antardasha": "Moon"},
            "narayana_current": {"sign": "Libra", "lord": "Venus"},
            "marriage_convergence": {"convergence_level": "L4", "probability": "70-85%"},
            "external_activation": {
                "level": "moderate",
                "source": "vedastro_service_adapter_candidate",
                "signals": ["vedastro_range_scan"],
                "events": [
                    {
                        "event_id": "jupiter_7h_window",
                        "score": 72,
                        "start": "2026-05-01",
                        "end": "2026-06-01",
                        "tags": ["marriage", "transit"],
                    }
                ],
            },
        },
        "confidence_cap": "medium-high",
        "missing_evidence": [],
        "blocked": False,
    }

    graph = _build_life_event_graph("relationship", strict)

    assert graph["version"] == "life_event_graph_v1"
    assert graph["route"] == "relationship"
    assert graph["dominant_label"] == "legal_marriage"
    assert graph["confidence_cap"] == "medium-high"
    assert graph["blocked"] is False
    assert graph["event_nodes"][0] == {
        "kind": "judgement",
        "label": "legal_marriage",
        "verdict": "high_probability_window",
        "score": 85,
        "source": "strict_workflow",
    }
    assert graph["event_nodes"][1] == {
        "kind": "dasha_window",
        "label": "Venus/Moon",
        "source": "vimshottari_current",
    }
    assert graph["event_nodes"][2] == {
        "kind": "dasha_window",
        "label": "Libra/Venus",
        "source": "narayana_current",
    }
    assert graph["event_nodes"][3] == {
        "kind": "convergence",
        "label": "marriage_convergence",
        "level": "L4",
        "probability": "70-85%",
        "source": "dasa_convergence",
    }
    assert graph["event_nodes"][4] == {
        "kind": "external_window",
        "label": "jupiter_7h_window",
        "score": 72,
        "start": "2026-05-01",
        "end": "2026-06-01",
        "tags": ["marriage", "transit"],
        "source": "vedastro_service_adapter_candidate",
    }


def test_life_event_graph_is_returned_from_strict_relationship_evidence() -> None:
    result = {
        "modules": {
            "varga_full": {"D9_Navamsa": {"summary": "ok"}},
            "special_lagnas": {"Upapada_Lagna": {"sign": "Libra", "lord": "Venus"}},
            "jaimini": {
                "darakaraka": {"planet": "Venus", "house": 7},
                "marriage_support": {"dk_7h_link": True},
            },
            "vivah_saham": {"sign": "Taurus", "house": 7},
            "dasha": {"current_dasha": {"mahadasha": "Venus", "antardasha": "Moon"}},
            "narayana_dasha": {"current_dasha": {"sign": "Libra", "lord": "Venus"}},
            "dasa_convergence": {
                "domain_activations": {
                    "marriage_partnership": {"convergence_level": "L4", "probability": "70-85%"}
                }
            },
            "external_activation": {
                "evidence_ledger": [
                    {
                        "source": "vedastro_service_adapter_candidate",
                        "operation": "range_scan",
                        "domain": "marriage",
                        "event_id": "jupiter_7h_window",
                        "score": 72,
                        "start": "2026-05-01",
                        "end": "2026-06-01",
                        "tags": ["marriage", "transit"],
                    }
                ]
            },
        }
    }

    strict = _collect_strict_evidence("relationship", result)

    assert strict["life_event_graph"]["version"] == "life_event_graph_v1"
    assert strict["life_event_graph"]["route"] == "relationship"
    assert strict["life_event_graph"]["dominant_label"] == "legal_marriage"
    assert any(node["kind"] == "external_window" for node in strict["life_event_graph"]["event_nodes"])
