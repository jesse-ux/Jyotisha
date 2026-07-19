import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "references" / "oracle" / "gender_interpretation_contract_2026_07_19.json"
REPORT = ROOT / "docs" / "research" / "gender_interpretation_contract_2026_07_19.md"


def test_gender_contract_exists_and_is_not_a_chart_calculation_switch() -> None:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert data["contract_id"] == "gender_interpretation_contract_2026_07_19"
    assert data["calculation_layer_policy"]["changes_chart_math"] is False
    assert "vimshottari_dasha" in data["calculation_layer_policy"]["gender_neutral_calculations"]
    assert "shadbala" in data["calculation_layer_policy"]["gender_neutral_calculations"]
    assert "ashtakavarga" in data["calculation_layer_policy"]["gender_neutral_calculations"]


def test_gender_contract_limits_gender_use_to_relationship_and_birth_contexts() -> None:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))

    assert data["allowed_use_domains"] == [
        "relationship_spouse_interpretation",
        "marriage_timing_weighting",
        "children_birth_context_language",
    ]
    assert "career" in data["forbidden_use_domains"]
    assert "wealth" in data["forbidden_use_domains"]
    assert "core_personality" in data["forbidden_use_domains"]


def test_gender_contract_keeps_core_marriage_stack_gender_neutral() -> None:
    data = json.loads(CONTRACT.read_text(encoding="utf-8"))
    marriage = data["relationship_spouse_interpretation"]

    assert marriage["core_stack_gender_neutral"] == ["7th_house", "7th_lord", "D9", "UL", "Darakaraka"]
    assert marriage["gender_specific_supplements"]["male"]["spouse_karaka_focus"] == ["Venus"]
    assert marriage["gender_specific_supplements"]["female"]["spouse_karaka_focus"] == ["Jupiter", "Mars"]
    assert marriage["gender_specific_supplements"]["unknown_or_not_binary"]["spouse_karaka_focus"] == [
        "7th_lord",
        "D9",
        "UL",
        "Darakaraka",
        "Venus_as_general_relationship_karaka",
    ]
    assert marriage["hard_boundary"] == "gender_specific_karakas_are_supplements_not_single_factor_truth"


def test_gender_contract_report_is_readable_and_product_safe() -> None:
    text = REPORT.read_text(encoding="utf-8")

    assert "不改变星盘计算" in text
    assert "男命增强 Venus" in text
    assert "女命增强 Jupiter/Mars" in text
    assert "不能只靠“男金女木”" in text
    assert "prefer_not_to_say" in text
