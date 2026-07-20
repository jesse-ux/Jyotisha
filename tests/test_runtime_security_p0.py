from __future__ import annotations

import hashlib
import sys
import time
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import jyotish_api_server as api  # noqa: E402
import report_builder  # noqa: E402


class _Headers(dict):
    def get(self, key, default=None):
        return super().get(key, default)


class _Server:
    allowed_origins = {"http://localhost:3456"}
    server_address = ("127.0.0.1", 5200)


def _handler(headers: dict[str, str]):
    handler = api.JyotishAPIHandler.__new__(api.JyotishAPIHandler)
    handler.headers = _Headers(headers)
    handler.server = _Server()
    return handler


def test_untrusted_origin_is_rejected_before_post_side_effects() -> None:
    handler = _handler(
        {
            "Origin": "https://evil.example",
            "Host": "127.0.0.1:5200",
            "Content-Type": "application/json",
        }
    )
    with pytest.raises(api.Forbidden, match="Origin"):
        handler._enforce_request_security(require_json=True)


def test_post_requires_json_content_type() -> None:
    handler = _handler(
        {
            "Origin": "http://localhost:3456",
            "Host": "127.0.0.1:5200",
            "Content-Type": "text/plain",
        }
    )
    with pytest.raises(api.UnsupportedMediaType):
        handler._enforce_request_security(require_json=True)


@pytest.mark.parametrize(
    "url",
    [
        "https://example.com/image.png",
        "http://127.0.0.1:8080/private",
        "file:///etc/passwd",
        "ftp://example.com/file",
    ],
)
def test_report_renderer_blocks_external_and_local_resources(url: str) -> None:
    assert report_builder.is_allowed_report_resource_url(
        url,
        report_url="file:///tmp/report.html",
    ) is False


def test_report_renderer_allows_only_document_and_embedded_resources() -> None:
    assert report_builder.is_allowed_report_resource_url(
        "file:///tmp/report.html",
        report_url="file:///tmp/report.html",
    ) is True
    assert report_builder.is_allowed_report_resource_url(
        "data:image/png;base64,AA==",
        report_url="file:///tmp/report.html",
    ) is True


def test_async_job_identity_is_random_and_capability_protected(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(api, "_async_job_dir", lambda _scope: tmp_path)
    first = api._new_async_job_identity("chart")
    second = api._new_async_job_identity("chart")
    assert first["job_id"] != second["job_id"]
    assert len(first["job_id"].split("_", 1)[1]) >= 32
    assert first["access_token"] != second["access_token"]

    record = {
        "job_id": first["job_id"],
        "status": "queued",
        "access_token_hash": hashlib.sha256(first["access_token"].encode()).hexdigest(),
        "expires_at_unix": time.time() + 60,
    }
    api._write_async_job_record("chart", first["job_id"], record)
    assert api._load_async_job_record(
        "chart", first["job_id"], access_token=first["access_token"]
    )["status"] == "queued"
    with pytest.raises(api.JobAccessDenied):
        api._load_async_job_record("chart", first["job_id"], access_token="wrong")


def test_expired_async_job_is_deleted(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(api, "_async_job_dir", lambda _scope: tmp_path)
    identity = api._new_async_job_identity("chart")
    api._write_async_job_record(
        "chart",
        identity["job_id"],
        {
            "job_id": identity["job_id"],
            "access_token_hash": hashlib.sha256(identity["access_token"].encode()).hexdigest(),
            "expires_at_unix": time.time() - 1,
        },
    )
    assert api._load_async_job_record(
        "chart", identity["job_id"], access_token=identity["access_token"]
    ) is None
    assert not (tmp_path / f"{identity['job_id']}.json").exists()

def test_background_job_queue_rejects_when_capacity_is_full(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    class _FullCapacity:
        def acquire(self, blocking=False):
            return False

    monkeypatch.setattr(api, "_ASYNC_JOB_CAPACITY", _FullCapacity())
    with pytest.raises(api.JobQueueFull):
        api._submit_background_job(lambda: None)
