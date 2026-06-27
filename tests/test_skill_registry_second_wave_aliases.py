from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "technique_registry.json"


def test_registry_includes_second_wave_first_class_entries() -> None:
    techniques = json.loads(REGISTRY.read_text(encoding="utf-8"))["techniques"]

    required = {
        "chandra_bala": "covered",
        "navatara": "covered",
        "varga_dignity": "covered",
        "special_lagnas": "covered",
    }
    for key, status in required.items():
        assert key in techniques, key
        assert techniques[key]["status"] == status
        assert techniques[key]["knowledge_refs"]
        assert techniques[key]["commands"]
        assert techniques[key]["output_paths"]


def test_registry_keeps_special_lagna_aliases_discoverable() -> None:
    techniques = json.loads(REGISTRY.read_text(encoding="utf-8"))["techniques"]

    assert "special_lagnas_extended" in techniques
    assert "special_lagnas" in techniques
    assert techniques["special_lagnas"]["status"] == techniques["special_lagnas_extended"]["status"]
