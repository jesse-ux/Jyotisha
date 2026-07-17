from __future__ import annotations

from scripts.muntha import calc_muntha_from_sun_sign


def test_standalone_muntha_module_imports_and_calculates() -> None:
    result = calc_muntha_from_sun_sign(0, 12)

    assert result["muntha_sign"] == 11
    assert result["muntha_lord"] == "Jupiter"
