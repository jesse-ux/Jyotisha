import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "references" / "technique_registry.json"


def test_rangacharya_variant_registered_as_comparison_only():
    techniques = json.loads(REGISTRY.read_text(encoding="utf-8"))["techniques"]
    entry = techniques["rangacharya_jaimini_variant"]
    assert entry["status"] == "comparison-only"
    assert entry["verification_level"]["calculation"] == "experimental"
    assert entry["verification_level"]["prediction"] == "blocked"
    assert entry["conclusion_policy"] == "Display current-vs-variant differences only; do not use for verdicts or timing."
    assert entry["evidence_role"] == "comparison_only"
    assert "references/rangacharya_source_cards.json" in entry["knowledge_refs"]
