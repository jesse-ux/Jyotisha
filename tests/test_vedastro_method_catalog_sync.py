from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_vedastro_method_catalog_sync_schema_is_declared() -> None:
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_method_catalog_sync.py", "--print-schema"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["sync"] == "vedastro_method_catalog_sync"
    assert report["scope"] == "official_vedastro_method_catalog"
    assert "sync_tags" in report["operations"]
    assert "write_snapshot" in report["operations"]


def test_vedastro_method_catalog_sync_can_write_stubbed_snapshot() -> None:
    env = os.environ.copy()
    env["VEDASTRO_METHOD_CATALOG_STUB"] = json.dumps(
        {
            "source": "stubbed_catalog",
            "tag_groups": {
                "Marriage": [{"Name": "GoodForMarriage", "CalculatorMethod": "GoodForMarriage"}],
                "LendingMoney": [{"Name": "GoodForLendingMoney", "CalculatorMethod": "GoodForLendingMoney"}],
            },
        }
    )
    output_path = ROOT / "scratch" / "local" / "vedastro_adapter" / "test_method_catalog_snapshot.json"
    completed = subprocess.run(
        [
            sys.executable,
            "scripts/vedastro_method_catalog_sync.py",
            "--write",
            "--output",
            str(output_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["status"] == "ok"
    assert report["source"] == "stubbed_catalog"
    assert report["summary"]["tag_count"] == 2
    assert report["summary"]["method_count"] == 2
    snapshot = json.loads(output_path.read_text(encoding="utf-8"))
    assert "Marriage" in snapshot["tag_groups"]
    assert snapshot["summary"]["method_count"] == 2
