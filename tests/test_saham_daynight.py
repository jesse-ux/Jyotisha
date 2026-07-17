from datetime import datetime

from scripts.saham_daynight import determine_daytime


def test_swiss_daynight_does_not_use_solar_house_proxy():
    noon = determine_daytime(datetime(2026, 7, 12, 12, 0), lat=39.9042, lon=116.4074, tz=8)
    midnight = determine_daytime(datetime(2026, 7, 12, 0, 0), lat=39.9042, lon=116.4074, tz=8)

    assert noon["status"] == "computed"
    assert noon["is_daytime"] is True
    assert midnight["is_daytime"] is False
    assert noon["method"] == "swisseph.rise_trans"
