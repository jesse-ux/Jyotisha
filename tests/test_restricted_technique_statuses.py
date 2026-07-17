from __future__ import annotations

import json
from pathlib import Path

from scripts.audit_capabilities import ALLOWED_STATUS


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "technique_registry.json"


def test_restricted_techniques_keep_canonical_status_boundaries() -> None:
    techniques = json.loads(REGISTRY.read_text(encoding="utf-8"))["techniques"]

    assert techniques["prashna"]["status"] == "guarded"
    assert techniques["prashna_integration"]["status"] == "guarded"
    assert techniques["upagraha_gulika_maandi"]["status"] == "guarded"
    assert techniques["panchavargiya_bala"]["status"] == "guarded"
    assert techniques["rangacharya_jaimini_variant"]["status"] == "comparison-only"

    for key in ("prashna", "prashna_integration", "upagraha_gulika_maandi", "panchavargiya_bala"):
        assert techniques[key]["verification_level"]["prediction"] == "support_only"

    assert techniques["rangacharya_jaimini_variant"]["verification_level"]["prediction"] == "blocked"


def test_restricted_statuses_are_accepted_by_capability_audit() -> None:
    techniques = json.loads(REGISTRY.read_text(encoding="utf-8"))["techniques"]
    restricted_statuses = {
        techniques["prashna"]["status"],
        techniques["prashna_integration"]["status"],
        techniques["upagraha_gulika_maandi"]["status"],
        techniques["panchavargiya_bala"]["status"],
        techniques["rangacharya_jaimini_variant"]["status"],
    }

    assert restricted_statuses <= ALLOWED_STATUS
