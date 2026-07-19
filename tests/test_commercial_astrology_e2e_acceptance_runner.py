from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

import commercial_astrology_e2e_acceptance_runner as runner  # noqa: E402


def test_runner_blocks_without_runtime_contexts() -> None:
    report = runner.evaluate()

    assert report["status"] == "blocked"
    assert report["question_count"] == 10
    assert {row["status"] for row in report["rows"]} == {"blocked"}
    assert report["runtime_context_required"] is True


def test_runner_passes_when_all_required_layers_are_present(tmp_path: Path) -> None:
    contract = json.loads(runner.DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    all_terms = sorted({term for patterns in runner.LAYER_PATTERNS.values() for term in patterns})
    payload = {"context": " ".join(all_terms), "claim_status": "exploratory_unvalidated"}

    for question in contract["questions"]:
        (tmp_path / f"{question['id']}.json").write_text(json.dumps(payload), encoding="utf-8")

    report = runner.evaluate(context_dir=tmp_path)

    assert report["status"] == "pass"
    assert {row["status"] for row in report["rows"]} == {"pass"}


def test_runner_fails_on_forbidden_claim_hits(tmp_path: Path) -> None:
    contract = json.loads(runner.DEFAULT_CONTRACT.read_text(encoding="utf-8"))
    all_terms = sorted({term for patterns in runner.LAYER_PATTERNS.values() for term in patterns})
    payload = {"context": " ".join(all_terms), "claim": "full_year_certainty"}

    for question in contract["questions"]:
        (tmp_path / f"{question['id']}.json").write_text(json.dumps(payload), encoding="utf-8")

    report = runner.evaluate(context_dir=tmp_path)
    annual = next(row for row in report["rows"] if row["id"] == "annual_forecast")

    assert report["status"] == "fail"
    assert annual["status"] == "fail"
    assert annual["forbidden_claim_hits"] == ["full-year certainty"]


def test_runner_writes_question_manifest_for_context_capture(tmp_path: Path) -> None:
    output = tmp_path / "questions.json"

    manifest = runner.write_question_manifest(runner.DEFAULT_CONTRACT, output)
    saved = json.loads(output.read_text(encoding="utf-8"))

    assert manifest == saved
    assert saved["scope"] == "commercial_astrology_e2e_question_manifest"
    assert len(saved["questions"]) == 10
    assert saved["questions"][0]["context_filename"] == "marriage_timing.json"
