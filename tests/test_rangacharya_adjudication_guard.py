import pytest

from scripts import rangacharya


def test_assert_adjudication_allowed_rejects_default_variant():
    result = rangacharya.calc_rangacharya_variant(0, {"Sun": 10.0})
    with pytest.raises(rangacharya.RangacharyaValidationError):
        rangacharya.assert_adjudication_allowed(result)


def test_validation_summary_lists_blocking_rules():
    result = rangacharya.calc_rangacharya_variant(0, {"Sun": 10.0})
    summary = rangacharya.validation_summary(result)
    assert summary["adjudication_enabled"] is False
    assert summary["blocking_statuses"]
