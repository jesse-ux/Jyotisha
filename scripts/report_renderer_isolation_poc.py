#!/usr/bin/env python3
"""Run an isolated Chromium proof that report rendering cannot fetch external resources."""
from __future__ import annotations

import json
import argparse
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

try:
    from report_builder import is_allowed_report_resource_url
except ImportError:
    from scripts.report_builder import is_allowed_report_resource_url


class _ProbeHandler(BaseHTTPRequestHandler):
    requests = 0

    def do_GET(self) -> None:  # noqa: N802
        type(self).requests += 1
        self.send_response(200)
        self.end_headers()

    def log_message(self, _format: str, *_args: Any) -> None:
        return


def run_poc() -> dict[str, Any]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {"scope": "report_renderer_isolation_poc", "status": "blocked", "reason": "playwright_python_missing"}

    server = ThreadingHTTPServer(("127.0.0.1", 0), _ProbeHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            secret = root / "secret.txt"
            secret.write_text("must-not-load", encoding="utf-8")
            html = root / "report.html"
            remote_url = f"http://127.0.0.1:{server.server_port}/probe"
            html.write_text(
                f'<img src="{remote_url}"><img src="{secret.as_uri()}"><p>report</p>',
                encoding="utf-8",
            )
            report_url = html.as_uri()
            blocked: list[str] = []
            try:
                with sync_playwright() as playwright:
                    browser = playwright.chromium.launch(headless=True)
                    context = browser.new_context(java_script_enabled=False)
                    page = context.new_page()
                    page.route(
                        "**/*",
                        lambda route: route.continue_()
                        if is_allowed_report_resource_url(route.request.url, report_url=report_url)
                        else (blocked.append(route.request.url), route.abort())[1],
                    )
                    page.goto(report_url, wait_until="networkidle")
                    context.close()
                    browser.close()
            except Exception as exc:  # Browser binary/startup is an environment boundary.
                return {"scope": "report_renderer_isolation_poc", "status": "blocked", "reason": f"chromium_unavailable:{type(exc).__name__}"}
            return {
                "scope": "report_renderer_isolation_poc",
                "status": "pass" if _ProbeHandler.requests == 0 and len(blocked) >= 2 else "fail",
                "http_probe_requests": _ProbeHandler.requests,
                "blocked_resource_count": len(blocked),
                "blocked_schemes": sorted({url.split(":", 1)[0] for url in blocked}),
            }
    finally:
        server.shutdown()
        server.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--strict", action="store_true", help="Return nonzero unless the isolation probe passes.")
    args = parser.parse_args()
    result = run_poc()
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))
    raise SystemExit(0 if not args.strict or result["status"] == "pass" else 1)
