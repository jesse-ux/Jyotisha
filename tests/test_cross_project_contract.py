"""Public synthetic-fixture contract shared with the commercial repository."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import cross_project_contract as contract  # noqa: E402


MANIFEST = ROOT / "references" / "cross_project_contract" / "fixture_manifest.v1.json"
LEDGER = ROOT / "references" / "cross_project_contract" / "sync_ledger.json"


def test_public_fixture_manifest_has_complete_effective_settings() -> None:
    manifest = contract.load_manifest(MANIFEST)

    assert manifest["schema_version"] == 1
    assert manifest["privacy_scope"] == "public_synthetic_only"
    fixture = manifest["fixtures"][0]
    assert fixture["birth"]["synthetic"] is True
    assert fixture["effective"] == {"ayanamsa": "lahiri", "node_mode": "mean", "timezone_offset": 5.5}


def test_local_calculation_matches_public_compatibility_hash() -> None:
    report = contract.evaluate_manifest(MANIFEST)

    assert report["matches"] is True
    assert report["fixtures"][0]["matches"] is True


def test_comparator_reports_tampered_expected_hash(tmp_path: Path) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    manifest["fixtures"][0]["compatibility_hash"] = "0" * 64
    changed = tmp_path / "fixture_manifest.v1.json"
    changed.write_text(json.dumps(manifest), encoding="utf-8")

    report = contract.evaluate_manifest(changed)

    assert report["matches"] is False
    assert report["fixtures"][0]["matches"] is False


def test_compatibility_payload_normalizes_engine_degree_field() -> None:
    fixture = contract.load_manifest(MANIFEST)["fixtures"][0]
    chart = {
        "ascendant": {"sign": "Aries", "degree": 1.25},
        "planets": {
            planet: {"sign": "Aries", "degree": float(index)}
            for index, planet in enumerate(contract.PLANETS)
        },
    }

    payload = contract.compatibility_payload(chart, fixture)

    assert payload["ascendant"]["lon"] == 1.25
    assert payload["planets"]["Sun"]["lon"] == 0.0


def test_sync_ledger_requires_provenance_privacy_tests_hash_and_rollback() -> None:
    ledger = contract.load_ledger(LEDGER)

    assert ledger == {"schema_version": 1, "entries": []}
    missing = contract.validate_ledger_entry({"source_repository": "x"})
    assert "target_commit" in missing
    assert "privacy_review" in missing
    assert "rollback" in missing
