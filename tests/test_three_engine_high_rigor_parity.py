import os
from pathlib import Path
import subprocess
import sys

from benchmarks.jyotish.scripts.run_skill_baseline import run_sample
from benchmarks.jyotish.scripts.run_pyjhora_compare import build_pyjhora_sample, compare_one
from scripts import three_engine_high_rigor_parity as parity


ROOT = Path(__file__).resolve().parents[1]


def test_runner_imports_from_commercial_root() -> None:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(ROOT)
    result = subprocess.run(
        [sys.executable, "-c", "import scripts.three_engine_high_rigor_parity"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_public_sample_exposes_shadbala_components() -> None:
    result = run_sample(parity.SAMPLE)
    assert result["ok"] is True
    components = result["canonical"]["shadbala_components"]
    assert set(components["Sun"]) == set(parity.VED_COMPONENT_FIELDS)


def test_pyjhora_sample_exposes_shadbala_components() -> None:
    sample = build_pyjhora_sample(parity.SAMPLE)
    assert set(sample["shadbala_components"]["Sun"]) == set(parity.VED_COMPONENT_FIELDS)


def test_pyjhora_matrix_includes_shadbala_components() -> None:
    baseline = {
        "ascendant": {}, "planets": {}, "varga": {}, "ashtakavarga": {}, "shadbala": {}, "dasha": {},
        "shadbala_components": {"Sun": {name: 1.0 for name in parity.VED_COMPONENT_FIELDS}},
    }
    rows = compare_one("sample", baseline, baseline)
    assert {row["field"] for row in rows if row["section"] == "Shadbala_Component" and row["body"] == "Sun"} == set(parity.VED_COMPONENT_FIELDS)


def test_jyotishganit_planet_map_reads_divisional_occupants() -> None:
    chart = {"houses": [{"occupants": [{"celestialBody": "Sun", "sign": "Leo"}]}]}
    assert parity._jyotish_planet_signs(chart) == {"Sun": "Leo"}


def test_vedastro_components_read_six_raw_fields() -> None:
    raw = {"Payload": {"AllPlanetData": {field: index for index, field in enumerate(parity.VED_COMPONENT_FIELDS.values(), 1)}}}
    assert parity._ved_components(raw) == {name: index for index, name in enumerate(parity.VED_COMPONENT_FIELDS, 1)}
