#!/usr/bin/env python3
"""Add pinned Xalen observations to the existing field-level parity rows."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

RASHI = {"Mesha":"Aries","Vrishabha":"Taurus","Mithuna":"Gemini","Karka":"Cancer","Simha":"Leo","Kanya":"Virgo","Tula":"Libra","Vrishchika":"Scorpio","Dhanu":"Sagittarius","Makara":"Capricorn","Kumbha":"Aquarius","Meena":"Pisces"}
COMPONENT = {"sthana":"sthana", "kala":"kala", "dig":"dig", "chesta":"chesta", "naisargika":"naisargika", "drik":"drik"}


def _xalen_value(row: dict, raw: dict):
    section, field = row["section"], row["field"]
    if section in {"D1", "D2", "D4", "D9", "D10"}:
        planet = field.split(".", 1)[0]
        return RASHI[raw["varga"][section][planet]]
    if section == "ashtakavarga_bav":
        return raw["ashtakavarga"]["bav"][field]
    if section == "ashtakavarga_sav":
        return raw["ashtakavarga"]["sav"]
    if section == "shadbala_components":
        planet, component = field.split(".", 1)
        return raw["shadbala"][planet][COMPONENT[component]]
    if section == "shadbala_total":
        return raw["shadbala"][field]["total"]
    return None


def compare(manifest_path: Path, xalen_path: Path) -> dict:
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    envelope = json.loads(xalen_path.read_text(encoding="utf-8"))
    raw = envelope["raw"]
    rows, counts = [], Counter()
    for source in manifest["comparison_rows"]:
        value = _xalen_value(source, raw)
        if value is None:
            continue
        local = source["local_value"]
        if isinstance(local, (int, float)) and isinstance(value, (int, float)):
            matched = abs(float(local) - float(value)) <= 0.05
        else:
            matched = local == value
        status = "match" if matched else "mismatch"
        counts[status] += 1
        rows.append({"section":source["section"],"field":source["field"],"local_value":local,"xalen_value":value,"status":status})
    return {"scope":"xalen_fourth_oracle_comparison","source_commit":envelope["source_commit"],"license":envelope["license"],"truth_policy":"fourth_observation_not_truth","row_count":len(rows),"match_count":counts["match"],"mismatch_count":counts["mismatch"],"rows":rows}


def main() -> int:
    p=argparse.ArgumentParser(description=__doc__); p.add_argument("--manifest",type=Path,default=Path("references/oracle/three_engine_parity_replay_manifest.json")); p.add_argument("--xalen",type=Path,default=Path("references/oracle/artifacts/xalen_steve_jobs_high_rigor_raw.json")); p.add_argument("--output",type=Path); a=p.parse_args()
    report=compare(a.manifest,a.xalen); text=json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+"\n"
    if a.output: a.output.parent.mkdir(parents=True,exist_ok=True); a.output.write_text(text,encoding="utf-8")
    print(text,end=""); return 0


if __name__ == "__main__": raise SystemExit(main())
