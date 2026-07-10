from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_premium_skill_zip_runs_from_clean_directory(tmp_path: Path) -> None:
    zip_path = tmp_path / "jyotish-premium.zip"
    release = subprocess.run(
        [
            sys.executable,
            "scripts/skill_release_package.py",
            "--edition",
            "premium_cloud_drive",
            "--write-zip",
            str(zip_path),
        ],
        cwd=ROOT,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert release.returncode == 0, release.stderr or release.stdout

    extract_dir = tmp_path / "clean"
    with zipfile.ZipFile(zip_path) as archive:
        archive.extractall(extract_dir)

    required = [
        "INSTALL.md",
        "USER_PROMPTS.md",
        "PACKAGE_ACCEPTANCE.json",
        "references/real_case_calibration/replay_manifest.json",
        "references/oracle/three_engine_parity_replay_manifest.json",
        "references/oracle/western_oracle_adapter_contract.md",
    ]
    assert [path for path in required if not (extract_dir / path).exists()] == []

    acceptance = json.loads((extract_dir / "PACKAGE_ACCEPTANCE.json").read_text(encoding="utf-8"))
    assert acceptance["status"] == "pass"

    privacy = subprocess.run(
        [sys.executable, "scripts/public_release_privacy_scan.py"],
        cwd=extract_dir,
        text=True,
        capture_output=True,
        timeout=120,
        check=False,
    )
    assert privacy.returncode == 0, privacy.stderr or privacy.stdout

    user_acceptance = subprocess.run(
        [sys.executable, "scripts/user_invocation_acceptance_check.py"],
        cwd=extract_dir,
        text=True,
        capture_output=True,
        timeout=240,
        check=False,
    )
    assert user_acceptance.returncode == 0, user_acceptance.stderr or user_acceptance.stdout
    report = json.loads(user_acceptance.stdout)
    assert report["status"] == "pass"
    assert report["checks"]["guided_topics_entrypoint"] is True
