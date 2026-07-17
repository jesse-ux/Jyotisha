from pathlib import Path


PAGE = Path("frontend/src/app/page.tsx")


def test_daily_starlanguage_entrypoint_is_productized() -> None:
    source = PAGE.read_text(encoding="utf-8")
    assert "今日星语" in source
    assert "draftDailyStarlanguageQuestion" in source
    assert "探索性日提示" in source
    assert "不是确定预测" in source


def test_birth_time_rectification_entrypoint_is_productized() -> None:
    source = PAGE.read_text(encoding="utf-8")
    assert "生时校正" in source
    assert "draftBirthTimeRectificationQuestion" in source
    assert "候选出生时间段" in source
    assert "不能直接改写默认星盘" in source
