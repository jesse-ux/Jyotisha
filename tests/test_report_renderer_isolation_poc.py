from scripts.report_renderer_isolation_poc import run_poc


def test_report_renderer_isolation_poc_never_claims_pass_without_browser() -> None:
    result = run_poc()
    assert result["status"] in {"pass", "fail", "blocked"}
    if result["status"] == "pass":
        assert result["http_probe_requests"] == 0
        assert result["blocked_resource_count"] >= 2
