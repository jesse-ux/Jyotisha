#!/usr/bin/env python3
"""Runtime smoke check for the Jyotish web app and local API."""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "jyotish-app"
API_SERVER = ROOT / "scripts" / "jyotish_api_server.py"
TMP = Path(os.environ.get("TMPDIR") or tempfile.gettempdir())


def run(cmd: list[str], *, cwd: Path = ROOT, timeout: int = 12, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=check)


def curl_text(url: str, *, timeout: int = 12) -> str:
    return run(["curl", "-sS", url], timeout=timeout).stdout


def curl_status(url: str, *, timeout: int = 4) -> tuple[bool, str]:
    completed = run(
        ["curl", "-sS", "-o", "/dev/null", "-w", "%{http_code}", url],
        timeout=timeout,
        check=False,
    )
    code = completed.stdout.strip()
    return completed.returncode == 0 and code.startswith(("2", "3", "4")), completed.stderr.strip() or code


def curl_json(url: str, *, timeout: int = 12) -> dict[str, Any]:
    return json.loads(curl_text(url, timeout=timeout))


def curl_post_json(url: str, payload: dict[str, Any], *, timeout: int = 15) -> dict[str, Any]:
    completed = run(
        [
            "curl",
            "-sS",
            "-X",
            "POST",
            "-H",
            "Content-Type: application/json",
            "--data-binary",
            json.dumps(payload),
            url,
        ],
        timeout=timeout,
    )
    return json.loads(completed.stdout)


def wait_for_url(url: str, *, timeout: float = 12.0, logs: list[Path] | None = None) -> None:
    deadline = time.time() + timeout
    last = ""
    while time.time() < deadline:
        ok, last = curl_status(url)
        if ok:
            return
        time.sleep(0.25)
    log_text = ""
    for log in logs or []:
        if log.exists():
            log_text += f"\n--- {log} ---\n{log.read_text(encoding='utf-8', errors='replace')[-4000:]}"
    raise RuntimeError(f"Timed out waiting for {url}: {last}{log_text}")


def start_process(cmd: list[str], cwd: Path, log_path: Path) -> subprocess.Popen[str]:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log = log_path.open("w", encoding="utf-8")
    return subprocess.Popen(cmd, cwd=cwd, stdout=log, stderr=subprocess.STDOUT, text=True)


def stop_process(process: subprocess.Popen[str] | None) -> None:
    if process is None:
        return
    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=5)


def sample_birth_payload() -> dict[str, Any]:
    return {
        "year": 1990,
        "month": 1,
        "day": 1,
        "hour": 12,
        "minute": 0,
        "lat": 39.9,
        "lon": 116.4,
        "tz": 8,
    }


def assert_report_artifact_smoke(api_base: str) -> dict[str, Any]:
    result = curl_post_json(
        f"{api_base}/api/report_artifact",
        {
            "format": "html",
            "name": "runtime smoke report",
            "html": "<!doctype html><html><body><h1>Runtime Smoke</h1></body></html>",
        },
        timeout=20,
    )
    if not result.get("success") or result.get("endpoint") != "report_artifact":
        raise AssertionError(f"report_artifact_smoke failed: {result}")
    if not result.get("html_base64") or not result.get("html_filename", "").endswith(".html"):
        raise AssertionError(f"report_artifact_smoke missing fallback artifact: {result}")
    delivery = result.get("delivery") or {}
    expected_fields = {
        "artifact_status": "html_ready",
        "primary_artifact": "html",
        "download_filename": result.get("html_filename"),
        "download_mime": "text/html;charset=utf-8",
    }
    for field, expected in expected_fields.items():
        if result.get(field) != expected:
            raise AssertionError(f"report_artifact_smoke bad {field}: {result}")
    if delivery.get("artifact_status") != result.get("artifact_status"):
        raise AssertionError(f"report_artifact_smoke delivery status mismatch: {result}")
    if delivery.get("filename") != result.get("download_filename"):
        raise AssertionError(f"report_artifact_smoke delivery filename mismatch: {result}")
    if not result.get("user_message") or not result.get("next_action"):
        raise AssertionError(f"report_artifact_smoke missing user guidance: {result}")
    return {
        "success": True,
        "html_filename": result.get("html_filename"),
        "format": result.get("format"),
        "artifact_status": result.get("artifact_status"),
        "download_filename": result.get("download_filename"),
    }


def assert_ai_bridge_policy_smoke(web_base: str) -> dict[str, Any]:
    bridge = curl_text(f"{web_base}/api-bridge.js")
    ai_chat = curl_text(f"{web_base}/ai-chat.js")
    i18n = curl_text(f"{web_base}/i18n.js")
    required = [
        "AI_BROWSER_KEY_DISABLED",
        "不要把 OpenAI API key 放进浏览器",
        "aiKeyPolicy: 'server_side_only'",
    ]
    missing = [token for token in required if token not in bridge]
    unsafe = [
        "YINDUZHANXING_AI_KEY",
        "apiKey: AI_KEY",
        "Authorization': 'Bearer ' + AI_KEY",
    ]
    chat_required = [
        "buildAISetupGuidance",
        "OPENAI_API_KEY",
        "/api/chat",
        "不要把 OpenAI API key 放进浏览器",
    ]
    chat_text = ai_chat + "\n" + i18n
    chat_missing = [token for token in chat_required if token not in chat_text]
    chat_unsafe = [
        "jyotish_ai_endpoint",
        "Custom endpoint failed",
        "在浏览器控制台输入",
    ]
    leaked = [token for token in unsafe if token in bridge] + [token for token in chat_unsafe if token in chat_text]
    if missing or leaked:
        raise AssertionError(f"ai_bridge_policy_smoke failed: missing={missing}, chat_missing={chat_missing}, leaked={leaked}")
    if chat_missing:
        raise AssertionError(f"ai_chat_policy_smoke failed: chat_missing={chat_missing}")
    return {
        "success": True,
        "policy": "AI_BROWSER_KEY_DISABLED",
        "chat_policy": "server_side_only",
    }


def assert_contract(web_base: str, api_base: str) -> dict[str, Any]:
    html = curl_text(f"{web_base}/")
    for token in ['id="birth-form"', 'id="tab-kp"', "/main.js", "/api-bridge.js"]:
        if token not in html:
            raise AssertionError(f"frontend missing token: {token}")

    health = curl_json(f"{api_base}/api/health")
    if health.get("status") != "ok":
        raise AssertionError(f"bad health: {health}")
    for module in ["Remedies", "Ashtakavarga", "Kakshya", "CaseValidation"]:
        if module not in health.get("modules", ""):
            raise AssertionError(f"health missing module: {module}")

    audit = curl_json(f"{api_base}/api/capability_audit", timeout=20)
    registry_count = audit["registry"]["technique_count"]
    if audit["productization"]["summary"]["productized"] != registry_count:
        raise AssertionError("not all registry techniques are productized")
    if audit["ux_productization"]["summary"]["excellent"] != registry_count:
        raise AssertionError("not all registry techniques are excellent UX")
    if audit["priority_gaps"]:
        raise AssertionError(f"priority gaps remain: {audit['priority_gaps']}")

    chart = curl_post_json(f"{api_base}/api/chart", sample_birth_payload(), timeout=20)
    if not chart.get("success"):
        raise AssertionError(f"chart failed: {chart}")
    if not chart.get("remedies", {}).get("evidence_chain"):
        raise AssertionError("chart remedies evidence_chain is empty")

    payload = {"planets": chart["planets"], "ascendant": chart["ascendant"]}
    ashtakavarga = curl_post_json(f"{api_base}/api/ashtakavarga", payload, timeout=20)
    for path in [("summary", "strongest_houses"), ("pav_summary", "top_planets"), ("sodhita_summary", "top_signs")]:
        cur: Any = ashtakavarga
        for part in path:
            cur = cur.get(part) if isinstance(cur, dict) else None
        if not cur:
            raise AssertionError(f"ashtakavarga missing {'.'.join(path)}")

    kp = curl_post_json(f"{api_base}/api/kp", payload, timeout=20)
    if not kp or "error" in kp:
        raise AssertionError(f"kp failed: {kp}")

    report_artifact_smoke = assert_report_artifact_smoke(api_base)
    ai_bridge_policy_smoke = assert_ai_bridge_policy_smoke(web_base)

    return {
        "valid": True,
        "web_base": web_base,
        "api_base": api_base,
        "registry_count": registry_count,
        "ux": audit["ux_productization"]["summary"],
        "productization": audit["productization"]["summary"],
        "chart_remedy_evidence": len(chart["remedies"]["evidence_chain"]),
        "ashtakavarga_sav_total": ashtakavarga["summary"]["sav_total"],
        "report_artifact_smoke": report_artifact_smoke,
        "ai_bridge_policy_smoke": ai_bridge_policy_smoke,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run Jyotish frontend/API runtime smoke")
    parser.add_argument("--web-base", default="http://127.0.0.1:5173")
    parser.add_argument("--api-base", default="http://127.0.0.1:5200")
    parser.add_argument("--start-if-needed", action="store_true", help="Start local Vite/API servers if defaults are not already running")
    parser.add_argument("--api-port", type=int, default=5200)
    parser.add_argument("--web-port", type=int, default=5173)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    api_process: subprocess.Popen[str] | None = None
    web_process: subprocess.Popen[str] | None = None
    web_base = args.web_base.rstrip("/")
    api_base = args.api_base.rstrip("/")

    try:
        api_ok, _ = curl_status(f"{api_base}/api/health")
        web_ok, _ = curl_status(f"{web_base}/")
        if args.start_if_needed and (not api_ok or not web_ok):
            web_base = f"http://127.0.0.1:{args.web_port}"
            api_base = f"http://127.0.0.1:{args.api_port}"
            api_log = TMP / f"jyotish-runtime-api-{args.api_port}.log"
            web_log = TMP / f"jyotish-runtime-web-{args.web_port}.log"
            if not api_ok:
                api_process = start_process(
                    [sys.executable, str(API_SERVER), "--port", str(args.api_port), "--allow-origin", web_base],
                    ROOT,
                    api_log,
                )
                try:
                    wait_for_url(f"{api_base}/api/health", logs=[api_log])
                except RuntimeError as exc:
                    if "PermissionError" in str(exc) and "socket.bind" in str(exc):
                        print(json.dumps({"valid": False, "skipped": True, "reason": "sandbox disallows local listening servers"}, ensure_ascii=False, indent=2))
                        return 0
                    raise
            if not web_ok:
                web_process = start_process(
                    ["npm", "run", "dev", "--", "--host", "127.0.0.1", "--port", str(args.web_port)],
                    APP,
                    web_log,
                )
                wait_for_url(f"{web_base}/", logs=[web_log])

        result = assert_contract(web_base, api_base)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    finally:
        stop_process(web_process)
        stop_process(api_process)


if __name__ == "__main__":
    raise SystemExit(main())
