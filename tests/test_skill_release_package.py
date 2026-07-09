from __future__ import annotations

import zipfile

from scripts.skill_release_package import build_package_plan, write_zip


def test_skill_release_package_dry_run_uses_safe_tracked_files() -> None:
    plan = build_package_plan("premium_cloud_drive")

    assert plan["scope"] == "skill_release_package"
    assert plan["edition"] == "premium_cloud_drive"
    assert plan["privacy_scan_status"] == "pass"
    assert plan["file_count"] > 0
    assert "SKILL.md" in plan["files"]
    assert "scripts/skill_release_manifest.py" in plan["files"]
    assert ".env.local" not in plan["files"]
    assert not any(path.startswith("scratch/") for path in plan["files"])
    assert not any("private" in path.lower() for path in plan["files"])


def test_skill_release_package_can_write_zip(tmp_path) -> None:
    target = tmp_path / "jyotish-premium.zip"
    plan = write_zip("premium_cloud_drive", target)

    assert plan["zip_path"] == str(target)
    assert target.exists()
    with zipfile.ZipFile(target) as archive:
        names = set(archive.namelist())
    assert "SKILL.md" in names
    assert "scripts/skill_release_manifest.py" in names
    assert ".env.local" not in names
