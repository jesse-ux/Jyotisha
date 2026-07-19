import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
INTAKE = ROOT / "references/oracle/authoritative_oss_jyotish_source_intake_2026_07_19.json"
INDEX = ROOT / "references/oracle/evidence_packet_index_2026_07_19.json"


def _load(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_oss_intake_keeps_source_candidates_out_of_production_truth():
    data = _load(INTAKE)

    assert data["scope"] == "authoritative_oss_jyotish_source_intake"
    assert data["production_tuning_allowed"] is False
    truth_boundary = data["truth_boundary"].lower()
    assert "final truth" in truth_boundary
    assert "do not become" in truth_boundary or "not final truth" in truth_boundary

    by_name = {source["name"]: source for source in data["sources"]}
    for required in (
        "northtara/jyotishganit",
        "VicharaVandana/jyotishyamitra",
        "vedika-io/xalen-ephemeris",
        "naturalstupid/PyJHora",
        "VedAstro/VedAstro",
    ):
        assert required in by_name

    for source in data["sources"]:
        truth_status = source["truth_status"].lower()
        assert truth_status != "final_truth"
        assert "ready_truth" not in truth_status


def test_copyleft_sources_are_not_vendorable_in_commercial_runtime():
    data = _load(INTAKE)

    restricted = [
        source
        for source in data["sources"]
        if source.get("license", "").startswith(("AGPL", "GPL"))
    ]
    assert restricted
    for source in restricted:
        action = source["commercial_action"].lower()
        assert "do_not" in action or "isolated" in action or "separate" in action


def test_oss_intake_is_registered_in_evidence_packet_index():
    index = _load(INDEX)

    packets = {packet["packet_id"]: packet for packet in index["packets"]}
    packet = packets["authoritative_oss_jyotish_source_intake"]
    assert packet["path"] == INTAKE.relative_to(ROOT).as_posix()
    assert packet["claim_status"] == "source_intake_only"
    assert "not final truth" in packet["claim_boundary"].lower()
    assert "pin" in packet["consumer_policy"]
