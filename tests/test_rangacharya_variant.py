from scripts import rangacharya


SAMPLE_LONGS = {
    "Sun": 10.0,
    "Moon": 45.0,
    "Mars": 80.0,
    "Mercury": 110.0,
    "Jupiter": 145.0,
    "Venus": 200.0,
    "Saturn": 250.0,
    "Rahu": 300.0,
    "Ketu": 120.0,
}


def test_variant_result_is_experimental_and_not_for_adjudication():
    result = rangacharya.calc_rangacharya_variant(0, SAMPLE_LONGS)
    assert result["variant"] == "rangacharya"
    assert result["adjudication_enabled"] is False
    assert result["status"] == "experimental_not_for_adjudication"


def test_variant_includes_core_sections():
    result = rangacharya.calc_rangacharya_variant(0, SAMPLE_LONGS)
    assert "source_status" in result
    assert "arudha_padas" in result
    assert "active_lagna" in result
    assert "effective_lagna" in result
    assert result["arudha_padas"]["AL"]["source_card_id"] == "rangacharya_core_arudha"
    assert result["arudha_padas"]["AL"]["source_card_status"] == "transcribed"
    assert result["active_lagna"]["source_card_id"] == "active_effective_lagna"
    assert result["effective_lagna"]["source_card_id"] == "active_effective_lagna"


def test_diff_marks_algorithm_names():
    current = {"AL": {"sign": "Aries"}}
    variant = {"arudha_padas": {"AL": {"sign": "Taurus"}}}
    diff = rangacharya.diff_current_vs_rangacharya(current, variant)
    assert diff["current_algorithm"] == "current_jaimini"
    assert diff["variant_algorithm"] == "rangacharya"
    assert diff["differences"][0]["key"] == "AL.sign"
