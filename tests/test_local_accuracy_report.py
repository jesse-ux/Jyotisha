import json
import subprocess
import sys


def run_report(*args):
    completed = subprocess.run(
        [sys.executable, "scripts/local_accuracy_report.py", *args],
        text=True,
        capture_output=True,
        timeout=90,
        check=False,
    )
    assert completed.returncode == 0, completed.stderr or completed.stdout
    return completed.stdout


def test_local_accuracy_report_outputs_machine_readable_baseline():
    report = json.loads(run_report("--format", "json"))

    assert report["scope"] == "local_jyotish_accuracy_report"
    assert report["summary"]["technique_count"] >= 68
    assert report["summary"]["locally_runnable"] is True

    real_cases = report["checks"]["public_real_person_revalidation"]
    assert real_cases["gated_passed_checks"] == real_cases["gated_total_checks"]
    assert real_cases["pass_rate"] >= 0.98

    yoga = report["checks"]["yoga_logic_benchmark"]
    assert yoga["precision"] >= 0.9
    assert yoga["recall"] >= 0.9
    assert yoga["f1"] >= 0.9
    assert yoga["external_benchmark_total"] >= yoga["agreements"]

    oracle = report["checks"]["dasha_shadbala_oracle_evidence"]
    assert oracle["production_tuning_allowed"] is False
    assert oracle["valid_packets"] >= 4
    assert oracle["ready_for_calibration"] >= 4

    ashtakoot = report["checks"]["ashtakoot_synastry_engine"]
    assert ashtakoot["full_engine_parity"] is True
    assert ashtakoot["max_score"] == 36


def test_local_accuracy_report_markdown_names_skill_gaps_and_command():
    output = run_report("--format", "markdown")

    assert "Local Jyotish Accuracy Report" in output
    assert "python3 scripts/local_accuracy_report.py --format json" in output
    assert "External oracle packets" in output
    assert "Interpretation accuracy" in output
