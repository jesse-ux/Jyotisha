from pathlib import Path
from scripts.xalen_difference_attribution import build_report
ROOT=Path(__file__).resolve().parents[1]

def test_all_xalen_shadbala_and_av_differences_are_formula_unit_attributed() -> None:
 report=build_report(ROOT/"references/oracle/xalen_fourth_oracle_comparison_2026_07_17.json")
 assert report["row_count"]==46
 assert report["classified_count"]==46
 assert sum(report["category_counts"].values())==46
 assert all(row["unit"] in {"Virupa","bindu_count"} for row in report["rows"])
 av=[r for r in report["rows"] if r["unit"]=="bindu_count"]
 assert len(av)==4
 assert all(r["row_total_local"]==r["row_total_xalen"] for r in av)
