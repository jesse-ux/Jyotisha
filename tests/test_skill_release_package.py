from __future__ import annotations

import json
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
    assert "RELEASE_MANIFEST.json" in plan["generated_files"]
    assert "PACKAGE_ACCEPTANCE.json" in plan["generated_files"]
    assert "SALES_PACKAGE.md" in plan["generated_files"]
    assert "GUIDED_ENTRYPOINT.md" in plan["generated_files"]
    assert plan["required_contracts"]["references/real_case_calibration/replay_manifest.json"] is True
    assert plan["required_contracts"]["references/oracle/three_engine_parity_replay_manifest.json"] is True
    assert "references/real_case_calibration/replay_manifest.json" in plan["files"]
    assert "references/oracle/three_engine_parity_replay_manifest.json" in plan["files"]
    assert "references/oracle/western_oracle_adapter_contract.md" in plan["files"]


def test_skill_release_package_can_write_zip(tmp_path) -> None:
    target = tmp_path / "jyotish-premium.zip"
    plan = write_zip("premium_cloud_drive", target)

    assert plan["zip_path"] == str(target)
    assert target.exists()
    with zipfile.ZipFile(target) as archive:
        names = set(archive.namelist())
    assert "SKILL.md" in names
    assert "scripts/skill_release_manifest.py" in names
    assert "INSTALL.md" in names
    assert "USER_PROMPTS.md" in names
    assert "RELEASE_MANIFEST.json" in names
    assert "PACKAGE_ACCEPTANCE.json" in names
    assert "SALES_PACKAGE.md" in names
    assert "GUIDED_ENTRYPOINT.md" in names
    assert "references/real_case_calibration/replay_manifest.json" in names
    assert "references/oracle/three_engine_parity_replay_manifest.json" in names
    assert "references/oracle/western_oracle_adapter_contract.md" in names
    assert ".env.local" not in names
    with zipfile.ZipFile(target) as archive:
        install = archive.read("INSTALL.md").decode("utf-8")
        prompts = archive.read("USER_PROMPTS.md").decode("utf-8")
        sales = archive.read("SALES_PACKAGE.md").decode("utf-8")
        guided = archive.read("GUIDED_ENTRYPOINT.md").decode("utf-8")
        acceptance = json.loads(archive.read("PACKAGE_ACCEPTANCE.json").decode("utf-8"))
    assert "python3 scripts/user_invocation_acceptance_check.py" in install
    assert "https://github.com/732642856/yinduzhanxing" in install
    assert "guided_topics" in prompts
    assert "official_blocked" in prompts
    assert "western_oracle_payload" in prompts
    assert "premium_cloud_drive" in sales
    assert "Do not include private birth data" in sales
    assert "blind=true" in guided
    assert "Technique Audit Table" in guided
    assert "guided_topics" in guided
    assert acceptance["status"] in {"pass", "blocked"}
    assert acceptance["required_contracts"]["references/oracle/three_engine_parity_replay_manifest.json"] is True
