from pathlib import Path


def test_full_reading_derives_saham_datetime_from_standard_chart_args() -> None:
    source = (Path(__file__).resolve().parents[1] / "scripts" / "jyotish_engine.py").read_text(encoding="utf-8")
    section = source[source.index("# ── Step 4.8: Tajika Yogas + Sahams"):source.index("# ── Step 4.9:")]
    assert "birth_dt = _birth_datetime_from_args(args)" in section
    assert "getattr(args, 'birth_datetime'" not in section
