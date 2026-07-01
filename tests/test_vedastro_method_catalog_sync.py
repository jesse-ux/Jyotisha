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
    assert "sync_python_capabilities" in report["operations"]


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


def test_vedastro_method_catalog_sync_can_build_stubbed_python_capability_registry() -> None:
    env = os.environ.copy()
    env["VEDASTRO_METHOD_CATALOG_STUB"] = json.dumps(
        {
            "source": "stubbed_catalog",
            "tag_groups": {},
            "python_capabilities": [
                {
                    "method": "AllPlanetData",
                    "signature": "(planetName, time)",
                    "bucket": "planet_time",
                    "parameter_names": ["planetName", "time"],
                    "callable": True,
                },
                {
                    "method": "AllHouseData",
                    "signature": "(houseName, time)",
                    "bucket": "house_name_time",
                    "parameter_names": ["houseName", "time"],
                    "callable": True,
                },
                {
                    "method": "GetAllEventDataGroupedByTag",
                    "signature": "()",
                    "bucket": "zero_arg",
                    "parameter_names": [],
                    "callable": True,
                },
            ],
        }
    )
    completed = subprocess.run(
        [sys.executable, "scripts/vedastro_method_catalog_sync.py"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
        env=env,
    )

    assert completed.returncode == 0, completed.stderr or completed.stdout
    report = json.loads(completed.stdout)
    assert report["summary"]["python_capability_count"] == 3
    assert report["summary"]["python_callable_count"] == 3
    assert report["summary"]["python_signature_bucket_count"] >= 2
    assert any(item["method"] == "AllPlanetData" for item in report["python_capabilities"])
    buckets = report["python_signature_buckets"]
    assert buckets["planet_time"]["count"] == 1
    assert "AllPlanetData" in buckets["planet_time"]["examples"]
