"""Commercial claim contract for birth-time rectification receipts."""
from __future__ import annotations

from typing import Any


def build_rectification_technique_contract(*, event_count: int, domain_count: int, high_rigor: bool = False) -> dict[str, Any]:
    blockers: list[str] = []
    if event_count < 3:
        blockers.append("insufficient_events")
    if domain_count < 2:
        blockers.append("insufficient_domains")
    if high_rigor:
        blockers.append("three_engine_parity_not_passed")
    return {
        "schema_version": 1,
        "calculation_status": "not_started" if event_count == 0 else "evaluated",
        "used_divisional_charts": ["D4", "D9", "D10", "D24", "D30"],
        "used_arudha": ["A7", "UL", "A10"],
        "dasha_tracks": ["vimshottari_md_ad_pd", "narayana_md_ad"],
        "missing_layers": ["D11", "ashtakavarga", "shadbala"],
        "partial_layers": ["D2"],
        "auxiliary_layers": ["functional_benefic_malefic", "controlled_transit"],
        "external_engines": {"status": "required_not_run" if high_rigor else "not_run", "providers": ["pyjhora", "jyotishganit", "vedastro"]},
        "hard_blockers": blockers,
        "can_narrow_to_minute": False,
        "boundary": "A candidate range is not a confirmed birth minute.",
    }
