from scripts import three_engine_high_rigor_parity as parity


def test_jyotishganit_planet_map_reads_divisional_occupants() -> None:
    chart = {"houses": [{"occupants": [{"celestialBody": "Sun", "sign": "Leo"}]}]}
    assert parity._jyotish_planet_signs(chart) == {"Sun": "Leo"}


def test_vedastro_components_read_six_raw_fields() -> None:
    raw = {"Payload": {"AllPlanetData": {field: index for index, field in enumerate(parity.VED_COMPONENT_FIELDS.values(), 1)}}}
    assert parity._ved_components(raw) == {name: index for index, name in enumerate(parity.VED_COMPONENT_FIELDS, 1)}
