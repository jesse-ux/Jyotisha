from scripts.xalen_oracle_adapter import COMMIT, MANIFEST


def test_xalen_adapter_is_pinned_and_license_bounded() -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    assert COMMIT in text
    assert "xalen-vedic" in text
    assert len(COMMIT) == 40
    assert "independent_ephemeris" in (MANIFEST.parent.parent.parent / "scripts/xalen_oracle_adapter.py").read_text(encoding="utf-8")
