from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_prashna_registry_keeps_verdict_guarded_and_integration_guarded() -> None:
    registry = json.loads((ROOT / "references/technique_registry.json").read_text(encoding="utf-8"))
    prashna = registry["techniques"]["prashna"]

    integration = registry["techniques"]["prashna_integration"]
    assert prashna["status"] == "guarded"
    assert prashna["verification_level"]["calculation"] == "verified"
    assert prashna["verification_level"]["rule"] == "verified"
    assert prashna["verification_level"]["prediction"] == "support_only"
    assert "cannot set final verdict" in prashna["conclusion_policy"]
    assert integration["status"] == "guarded"
    assert integration["verification_level"]["calculation"] == "partial"
    assert integration["verification_level"]["rule"] == "partial"
    assert "guarded" in integration["conclusion_policy"].lower()
