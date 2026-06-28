from __future__ import annotations

import json
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vedastro_official_mcp_bridge_schema_is_declared() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_official_mcp_bridge.py", "--print-schema"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["bridge"] == "vedastro_official_mcp_bridge"
    assert report["role"] == "official_public_mcp_thin_bridge"
    assert "initialize" in report["operations"]
    assert "tools_list" in report["operations"]


def test_vedastro_official_mcp_bridge_can_list_tools_against_mock_server() -> None:
    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if payload["method"] == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": payload["id"],
                    "result": {
                        "protocolVersion": "2025-06-18",
                        "serverInfo": {"name": "VedAstro", "version": "1.0.0"},
                        "capabilities": {},
                    },
                }
                body = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Mcp-Session-Id", "session-demo")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            assert payload["method"] == "tools/list"
            assert self.headers.get("Mcp-Session-Id") == "session-demo"
            response = {
                "jsonrpc": "2.0",
                "id": payload["id"],
                "result": {
                    "tools": [
                        {"name": "get_current_transits"},
                        {"name": "get_dasa_at_time"},
                    ]
                },
            }
            body = json.dumps(response).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args) -> None:  # noqa: A003
            return

    server = HTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        endpoint = f"http://127.0.0.1:{server.server_port}/api/mcp/public"
        completed = subprocess.run(
            [
                sys.executable,
                "scripts/vedastro_official_mcp_bridge.py",
                "--endpoint",
                endpoint,
                "--operation",
                "tools_list",
            ],
            cwd=ROOT,
            text=True,
            capture_output=True,
            timeout=120,
            check=False,
        )
    finally:
        server.shutdown()
        thread.join(timeout=5)

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["available"] is True
    assert report["status"] == "ok"
    assert report["operation"] == "tools_list"
    assert report["session_id"] == "session-demo"
    assert report["tool_count"] == 2
    assert report["tool_names"] == ["get_current_transits", "get_dasa_at_time"]
