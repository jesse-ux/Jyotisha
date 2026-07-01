from __future__ import annotations

import pytest

from scripts.varga import calc_all_vargas


PLANET_LONS = {
    "Sun": 3.5082636623988996,
    "Moon": 311.80885383130334,
    "Mars": 91.31729371926605,
    "Mercury": 338.53260292309903,
    "Jupiter": 163.8229749564531,
    "Venus": 340.5440654310959,
    "Saturn": 304.28763628893995,
    "Rahu": 231.03374080496383,
    "Ketu": 51.03374080496383,
}
ASC_LON = 133.0814

EXPECTED_VEDASTRO = {
    "D2_Hora": {
        "Sun": ("Aries", 10.51),
        "Moon": ("Gemini", 5.4125),
        "Mars": ("Cancer", 3.9383),
        "Mercury": ("Pisces", 25.5842),
        "Jupiter": ("Capricorn", 11.4542),
        "Venus": ("Cancer", 1.6172),
        "Saturn": ("Aquarius", 12.8489),
        "Rahu": ("Cancer", 3.0872),
        "Ketu": ("Capricorn", 3.0867),
        "Ascendant": ("Leo", 26.1517),
    },
    "D4_Turyamsa": {
        "Sun": ("Aries", 14.0133),
        "Moon": ("Taurus", 17.2167),
        "Mars": ("Cancer", 5.2511),
        "Mercury": ("Gemini", 4.1122),
        "Jupiter": ("Sagittarius", 25.2722),
        "Venus": ("Gemini", 12.1567),
        "Saturn": ("Aquarius", 17.1322),
        "Rahu": ("Taurus", 24.1164),
        "Ketu": ("Scorpio", 24.1156),
        "Ascendant": ("Scorpio", 22.3033),
    },
    "D7_Saptamsa": {
        "Sun": ("Aries", 24.5233),
        "Moon": ("Aries", 22.6289),
        "Mars": ("Cancer", 9.1894),
        "Mercury": ("Aries", 29.6964),
        "Jupiter": ("Sagittarius", 6.7264),
        "Venus": ("Taurus", 13.7742),
        "Saturn": ("Aquarius", 29.9814),
        "Rahu": ("Pisces", 27.2039),
        "Ketu": ("Pisces", 27.2019),
        "Ascendant": ("Scorpio", 1.5308),
    },
    "D16_Shodasamsa": {
        "Sun": ("Taurus", 26.0533),
        "Moon": ("Aquarius", 8.8667),
        "Mars": ("Aries", 21.0044),
        "Mercury": ("Aries", 16.4489),
        "Jupiter": ("Cancer", 11.0889),
        "Venus": ("Taurus", 18.6267),
        "Saturn": ("Libra", 8.5286),
        "Rahu": ("Cancer", 6.4664),
        "Ketu": ("Cancer", 6.4622),
        "Ascendant": ("Aquarius", 29.2133),
    },
    "D20_Vimsamsa": {
        "Sun": ("Gemini", 10.0664),
        "Moon": ("Cancer", 26.0833),
        "Mars": ("Aries", 26.2556),
        "Mercury": ("Capricorn", 20.5608),
        "Jupiter": ("Taurus", 6.3611),
        "Venus": ("Pisces", 0.7831),
        "Saturn": ("Aquarius", 25.6611),
        "Rahu": ("Aquarius", 0.5831),
        "Ketu": ("Aquarius", 0.5778),
        "Ascendant": ("Leo", 21.5164),
    },
    "D27_Bhamsa": {
        "Sun": ("Cancer", 4.59),
        "Moon": ("Leo", 18.7125),
        "Mars": ("Aquarius", 5.445),
        "Mercury": ("Leo", 20.2572),
        "Jupiter": ("Cancer", 13.0875),
        "Venus": ("Libra", 14.5575),
        "Saturn": ("Capricorn", 25.6425),
        "Rahu": ("Cancer", 27.7872),
        "Ketu": ("Capricorn", 27.7797),
        "Ascendant": ("Pisces", 23.0475),
    },
    "D30_Trimsamsa": {
        "Sun": ("Scorpio", 15.1),
        "Moon": ("Sagittarius", 24.125),
        "Mars": ("Taurus", 9.3833),
        "Mercury": ("Gemini", 15.8417),
        "Jupiter": ("Sagittarius", 24.5417),
        "Venus": ("Gemini", 16.175),
        "Saturn": ("Scorpio", 8.4917),
        "Rahu": ("Capricorn", 0.875),
        "Ketu": ("Capricorn", 0.8667),
        "Ascendant": ("Sagittarius", 2.275),
    },
    "D45_Akshavedamsa": {
        "Sun": ("Virgo", 7.65),
        "Moon": ("Capricorn", 21.1875),
        "Mars": ("Taurus", 29.075),
        "Mercury": ("Sagittarius", 23.7622),
        "Jupiter": ("Leo", 21.8125),
        "Venus": ("Pisces", 24.2622),
        "Saturn": ("Aquarius", 12.7372),
        "Rahu": ("Pisces", 16.3122),
        "Ketu": ("Pisces", 16.3),
        "Ascendant": ("Pisces", 18.4125),
    },
    "D60_Shashtyamsa": {
        "Sun": ("Scorpio", 0.2),
        "Moon": ("Capricorn", 18.25),
        "Mars": ("Virgo", 18.7667),
        "Mercury": ("Leo", 1.6833),
        "Jupiter": ("Sagittarius", 19.0833),
        "Venus": ("Sagittarius", 2.35),
        "Saturn": ("Libra", 16.9833),
        "Rahu": ("Taurus", 1.75),
        "Ketu": ("Scorpio", 1.7333),
        "Ascendant": ("Libra", 4.55),
    },
}


@pytest.mark.parametrize("varga_key, expected_rows", EXPECTED_VEDASTRO.items())
def test_varga_vedastro_mode_matches_official_golden_case(varga_key, expected_rows):
    result = calc_all_vargas(PLANET_LONS, ASC_LON, mode="vedastro")
    chart = result[varga_key]
    for body, (sign, degree) in expected_rows.items():
        assert chart[body]["sign"] == sign, (varga_key, body)
        assert chart[body]["degree_in_sign"] == pytest.approx(degree, abs=0.02), (varga_key, body)
