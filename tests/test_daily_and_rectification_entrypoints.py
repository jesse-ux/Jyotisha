from pathlib import Path


PAGE = Path("frontend/src/app/page.tsx")
DAILY_ROUTE = Path("frontend/src/app/api/daily-starlanguage/route.ts")
RECTIFICATION_ROUTE = Path("frontend/src/app/api/birth-rectification/route.ts")


def test_daily_starlanguage_entrypoint_is_productized() -> None:
    source = PAGE.read_text(encoding="utf-8")
    assert "今日星语" in source
    assert "fetchDailyStarlanguage" in source
    assert "buildDailyStarlanguageCard" in source
    assert "daily-starlanguage-card" in source
    assert "今日趋势" in source
    assert "行动建议" in source
    assert "今日提醒" in source
    assert "draftDailyStarlanguageQuestion" in source
    assert "探索性日提示" in source
    assert "不是确定预测" in source


def test_daily_starlanguage_api_declares_honest_source_boundary() -> None:
    source = DAILY_ROUTE.read_text(encoding="utf-8")
    assert "status: \"ok\"" in source
    assert "/api/chart" in source
    assert "/api/transit" in source
    assert "jyotish_api_transit_lite" in source
    assert "calculation_lite" in source
    assert "exploratory_unvalidated" in source
    assert "not_deterministic_prediction" in source


def test_birth_time_rectification_entrypoint_is_productized() -> None:
    source = PAGE.read_text(encoding="utf-8")
    assert "生时校正" in source
    assert "fetchBirthRectificationPreview" in source
    assert "birth-rectification-card" in source
    assert "draftBirthTimeRectificationQuestion" in source
    assert "候选出生时间段" in source
    assert "不能直接改写默认星盘" in source


def test_birth_rectification_api_proxies_active_questionnaire_with_boundary() -> None:
    source = RECTIFICATION_ROUTE.read_text(encoding="utf-8")
    assert "/api/active_rectification_questions" in source
    assert "candidate_scan" in source
    assert "question_count" in source
    assert "not_auto_rectified" in source
