"""Cross-repository sync status checks for the research/commercial pair."""

from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cross_project_sync_status as sync_status  # noqa: E402


POLICY = ROOT / "references" / "cross_project_contract" / "sync_policy.v1.json"


def _make_peer_copy(tmp_path: Path) -> Path:
    peer = tmp_path / "peer"
    policy = sync_status.load_policy(POLICY)
    for rel_path in policy["shared_files"]:
        source = ROOT / rel_path
        target = peer / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
    return peer


def test_sync_policy_encodes_research_first_commercial_mature_rule() -> None:
    policy = sync_status.load_policy(POLICY)

    assert policy["schema_version"] == 1
    assert policy["sync_model"] == "research_validates_commercial_receives_mature"
    assert policy["directional_gates"]["research_to_commercial"]["source_required"] == "validated_in_research"
    assert policy["directional_gates"]["research_to_commercial"]["target_required"] == "commercial_safe"
    assert set(policy["research_repo_exclusions"]) >= {
        "commercial_credits",
        "billing",
        "subscriptions",
        "payment",
        "account_entitlements",
        "service_role_runtime",
    }
    assert "references/cross_project_contract/fixture_manifest.v1.json" in policy["shared_files"]


def test_sync_status_passes_when_shared_files_match(tmp_path: Path) -> None:
    peer = _make_peer_copy(tmp_path)

    report = sync_status.compare_peer(peer, policy_path=POLICY, root=ROOT)

    assert report["status"] == "pass"
    assert report["missing"] == []
    assert report["mismatched"] == []
    assert report["checked_count"] == len(sync_status.load_policy(POLICY)["shared_files"])


def test_sync_status_reports_mismatched_shared_file(tmp_path: Path) -> None:
    peer = _make_peer_copy(tmp_path)
    changed = peer / "references" / "cross_project_contract" / "fixture_manifest.v1.json"
    data = json.loads(changed.read_text(encoding="utf-8"))
    data["fixtures"][0]["compatibility_hash"] = "0" * 64
    changed.write_text(json.dumps(data, sort_keys=True), encoding="utf-8")

    report = sync_status.compare_peer(peer, policy_path=POLICY, root=ROOT)

    assert report["status"] == "fail"
    assert report["missing"] == []
    assert report["mismatched"] == ["references/cross_project_contract/fixture_manifest.v1.json"]
