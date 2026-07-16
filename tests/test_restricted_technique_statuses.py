from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "technique_registry.json"


def test_restricted_techniques_keep_canonical_status_boundaries() -> None:
    techniques = json.loads(REGISTRY.read_text(encoding="utf-8"))["techniques"]

    assert techniques["prashna"]["status"] == "blocked"
    assert techniques["prashna_integration"]["status"] == "partial"
    assert techniques["upagraha_gulika_maandi"]["status"] == "partial"
    assert techniques["panchavargiya_bala"]["status"] == "blocked"
    assert techniques["rangacharya_jaimini_variant"]["status"] == "knowledge-only"

    for key in ("prashna", "prashna_integration", "upagraha_gulika_maandi", "panchavargiya_bala"):
        assert techniques[key]["verification_level"]["prediction"] == "support_only"

    assert techniques["rangacharya_jaimini_variant"]["verification_level"]["prediction"] == "blocked"
