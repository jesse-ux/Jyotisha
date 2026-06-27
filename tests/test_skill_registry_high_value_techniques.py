from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "technique_registry.json"


def test_registry_includes_high_value_traditional_techniques() -> None:
    techniques = json.loads(REGISTRY.read_text(encoding="utf-8"))["techniques"]

    required = {
        "tara_bala": "covered",
        "vimsopaka_bala": "covered",
        "deha_jeeva": "covered",
        "shodasavarga": "covered",
        "moolatrikona": "covered",
    }
    for key, status in required.items():
        assert key in techniques, key
        assert techniques[key]["status"] == status
        assert techniques[key]["knowledge_refs"]
        assert techniques[key]["commands"]
        assert techniques[key]["output_paths"]


def test_registry_keeps_neechabhanga_alias_aligned() -> None:
    techniques = json.loads(REGISTRY.read_text(encoding="utf-8"))["techniques"]

    assert "nicha_bhanga_raj" in techniques
    assert "neechabhanga" in techniques
    assert techniques["neechabhanga"]["status"] == techniques["nicha_bhanga_raj"]["status"]
