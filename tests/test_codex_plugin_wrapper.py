from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_local_codex_plugin_manifest_points_at_repo_truth() -> None:
    plugin_json = ROOT / ".codex-plugin" / "plugin.json"
    assert plugin_json.exists()

    payload = json.loads(plugin_json.read_text(encoding="utf-8"))
    assert payload["name"] == "jyotish-vedic-astrology"
    assert payload["skills"] == "./skills/"

    mcp_servers = payload["mcpServers"]
    assert isinstance(mcp_servers, dict)
    assert "jyotish" in mcp_servers
    jyotish = mcp_servers["jyotish"]
    assert jyotish["command"] == "python3"
    assert jyotish["args"] == ["./mcp_server.py"]

    assert (ROOT / "skills").is_dir()
    assert (ROOT / "mcp_server.py").is_file()
