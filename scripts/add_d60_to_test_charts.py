#!/usr/bin/env python3
"""为 standard_test_charts.json 批量补充 D60 (Shashtiamsa) 数据。"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _compute_one_chart import compute_yogas

ROOT = Path(__file__).resolve().parents[1]
STANDARD = ROOT / "references" / "standard_test_charts.json"

def main() -> int:
    data = json.loads(STANDARD.read_text(encoding="utf-8"))
    charts = data.get("charts", [])
    print(f"Processing {len(charts)} charts for D60 augmentation...")

    updated = 0
    for i, chart in enumerate(charts):
        name = chart.get("name", f"chart_{i}")
        # Skip if already has d60
        if chart.get("context", {}).get("d60"):
            print(f"  [{i+1}/{len(charts)}] {name}: already has D60, skipping")
            continue

        # Call compute_yogas to get full context with D60
        result = compute_yogas(chart)
        if "error" in result:
            print(f"  [{i+1}/{len(charts)}] {name}: ERROR - {result['error']}")
            continue

        new_context = result.get("context", {})
        d60_data = new_context.get("d60")
        if d60_data:
            chart["context"]["d60"] = d60_data
            updated += 1
            print(f"  [{i+1}/{len(charts)}] {name}: D60 added (asc={d60_data.get('ascendant')})")
        else:
            print(f"  [{i+1}/{len(charts)}] {name}: no D60 data generated")

    # Write back
    STANDARD.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nDone. Updated {updated}/{len(charts)} charts with D60 data.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
