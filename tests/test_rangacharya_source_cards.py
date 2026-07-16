import json
from pathlib import Path


CARDS = Path("references/rangacharya_source_cards.json")


REQUIRED_CARD_IDS = {
    "rangacharya_core_arudha",
    "active_effective_lagna",
    "prakriti_sanmukha",
    "rangacharya_special_mappings",
    "rangacharya_named_yogas",
    "rangacharya_ul_family_rules",
    "article_warehouse_future_tracks",
}


def _cards():
    return json.loads(CARDS.read_text(encoding="utf-8"))


def test_source_cards_exist_with_required_schema():
    data = _cards()
    assert data["schema_version"] == 1
    assert isinstance(data["cards"], list)
    for card in data["cards"]:
        assert card["id"]
        assert card["status"] in {
            "transcribed",
            "source_verified",
            "golden_verified",
            "engine_cross_checked",
            "case_calibrated",
            "blocked",
        }
        assert card["adjudication_enabled"] is False
        assert "evidence" in card


def test_source_cards_cover_phase2_rule_groups():
    data = _cards()
    found = {card["id"] for card in data["cards"]}
    assert REQUIRED_CARD_IDS <= found


def test_source_cards_do_not_contain_secrets():
    text = CARDS.read_text(encoding="utf-8")
    assert "sk_live_" not in text
    assert "VEDASTRO_API_KEY" not in text
