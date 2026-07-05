from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_print_cline_mcp_config_points_at_current_repo_mcp_server() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/print_cline_mcp_config.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    config = json.loads(completed.stdout)
    server = config["mcpServers"]["jyotish"]
    assert server["command"] == sys.executable
    assert server["args"] == [str(ROOT / "mcp_server.py")]
    assert server["cwd"] == str(ROOT)
    assert server["env"]["PYTHONPATH"].endswith("/scripts")


def test_cline_project_config_is_ignored_and_installable(tmp_path: Path) -> None:
    completed = subprocess.run(
        [
            sys.executable,
            str(ROOT / "scripts" / "print_cline_mcp_config.py"),
            "--repo-root",
            str(tmp_path),
            "--install-project",
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    written = tmp_path / ".cline" / "mcp.json"
    assert written.exists()
    config = json.loads(written.read_text(encoding="utf-8"))
    assert config["mcpServers"]["jyotish"]["args"] == [str(tmp_path / "mcp_server.py")]
    assert ".cline/" in (ROOT / ".gitignore").read_text(encoding="utf-8")

