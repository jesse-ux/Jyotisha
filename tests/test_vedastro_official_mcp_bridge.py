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
    assert "call_tool" in report["operations"]


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


def test_vedastro_official_mcp_bridge_can_call_tool_against_mock_server() -> None:
    seen_arguments: dict[str, object] = {}

    class Handler(BaseHTTPRequestHandler):
        def do_POST(self) -> None:  # noqa: N802
            length = int(self.headers.get("Content-Length", "0"))
            payload = json.loads(self.rfile.read(length).decode("utf-8"))
            if payload["method"] == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "id": payload["id"],
                    "result": {"protocolVersion": "2025-06-18", "capabilities": {}},
                }
                body = json.dumps(response).encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Mcp-Session-Id", "session-demo")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return

            assert payload["method"] == "tools/call"
            assert self.headers.get("Mcp-Session-Id") == "session-demo"
            assert payload["params"]["name"] == "get_dasa_at_time"
            seen_arguments.update(payload["params"]["arguments"])
            response = {
                "jsonrpc": "2.0",
                "id": payload["id"],
                "result": {"content": [{"type": "text", "text": "Saturn/Venus"}]},
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
                "call_tool",
                "--tool",
                "get_dasa_at_time",
                "--arguments-json",
                '{"birth_date":"17/04/1990","check_date":"04/07/2026"}',
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
    assert report["operation"] == "call_tool"
    assert report["tool_name"] == "get_dasa_at_time"
    assert report["result"]["content"][0]["text"] == "Saturn/Venus"
    assert seen_arguments["birth_date"] == "17/04/1990"
