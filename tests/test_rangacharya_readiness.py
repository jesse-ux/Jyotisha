from scripts import rangacharya_readiness


def test_readiness_reports_blocked_until_no_adjudication_cards():
    report = rangacharya_readiness.build_report()
    assert report["scope"] == "rangacharya_readiness"
    assert report["adjudication_enabled"] is False
    assert report["blocked_count"] >= 1
    assert "rangacharya_core_arudha" in report["cards"]


def test_readiness_does_not_expose_secrets():
    report = rangacharya_readiness.build_report()
    assert "sk_live_" not in str(report)
