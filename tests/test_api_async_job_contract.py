import json
import time
from pathlib import Path

import pytest

from scripts import jyotish_api_server as api


def test_evidence_packet_view_exposes_only_auditable_result_sections():
    packet = api.build_evidence_packet_view({
        "job_id": "job_1",
        "status": "completed",
        "result": {
            "fallback_reason": "VedAstro official snapshot blocked: timeout",
            "machine_evidence_packet": {"status": "draft", "metadata": {"capture_id": "x"}},
            "technique_audit": [{"technique": "D9", "status": "used"}],
            "ai_prompt_pack": {"prompt_zh": "internal prompt"},
        },
    })

    assert packet["job_id"] == "job_1"
    assert packet["execution_status"]["official_evidence_status"] == "official_blocked"
    assert packet["machine_evidence_packet"]["metadata"]["capture_id"] == "x"
    assert "ai_prompt_pack" not in packet


def test_async_job_route_extracts_id_before_loading(monkeypatch, tmp_path):
    record = {"job_id": "chart_abc", "status": "completed", "result": {}}
    monkeypatch.setattr(api, "_load_async_job_record", lambda *args, **kwargs: record)

    handler = api.JyotishAPIHandler.__new__(api.JyotishAPIHandler)
    handler.path = "/api/chart/jobs/chart_abc"
    handler.headers = {"Origin": ""}
    handler._enforce_request_security = lambda: None
    captured = {}
    handler._json = lambda data, status=200: captured.update(data=data, status=status)
    handler._error_json = lambda message, status=500, error_code="ERR_INTERNAL": captured.update(error=error_code, status=status)
    handler._job_access_token = lambda: "token"

    handler.do_GET()

    assert captured["status"] == 200
    assert captured["data"]["job_id"] == "chart_abc"


def test_evidence_packet_page_is_present_and_does_not_embed_birth_data():
    page = Path(api.REPO_ROOT) / "web" / "evidence_packet.html"
    source = page.read_text(encoding="utf-8")

    assert "Evidence Packet" in source
    assert "access token" in source
    assert "birth" not in source.lower()


def test_rectification_page_uses_choice_questionnaire_contract():
    page = Path(api.REPO_ROOT) / "web" / "rectification.html"
    source = page.read_text(encoding="utf-8")

    assert "/api/rectification/questionnaire" in source
    assert "/api/rectification/answers" in source
    assert "候选簇排序" in source


def test_home_page_keeps_location_confirmation_local():
    page = Path(api.REPO_ROOT) / "web" / "index.html"
    source = page.read_text(encoding="utf-8")

    assert "/api/location/resolve" in source
    assert "第三方地理服务" in source


def test_startup_cleanup_removes_only_expired_job_records(monkeypatch, tmp_path):
    expired = tmp_path / "expired.json"
    active = tmp_path / "active.json"
    expired.write_text(json.dumps({"expires_at_unix": time.time() - 1}), encoding="utf-8")
    active.write_text(json.dumps({"expires_at_unix": time.time() + 60}), encoding="utf-8")
    monkeypatch.setattr(api, "_async_job_dir", lambda scope: tmp_path)

    result = api.prune_expired_async_jobs()

    assert result["removed"] == 1
    assert not expired.exists()
    assert active.exists()


def test_rate_limit_is_configurable_and_rejects_over_budget(monkeypatch):
    api._RATE_LIMIT_BUCKETS.clear()
    monkeypatch.setenv("JYOTISH_API_RATE_LIMIT_PER_MINUTE", "1")

    api.enforce_rate_limit("test-client", now=0)
    with pytest.raises(api.RateLimited):
        api.enforce_rate_limit("test-client", now=1)
